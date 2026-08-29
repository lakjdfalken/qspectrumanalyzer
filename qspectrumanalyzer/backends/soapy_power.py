import os, sys, shlex, signal, struct, collections

from PySide6 import QtCore
import numpy as np

from qspectrumanalyzer import subprocess
from qspectrumanalyzer.backends import BaseInfo, BasePowerThread


class SoapyPowerBinFormat:
    """Reader for the soapy_power binary output format (SDRFF version 2)

    This is vendored on purpose. We only ever need to parse what the
    soapy_power *executable* writes, so importing the soapypower Python
    package (and with it SoapySDR) just to get its formatter is an
    unnecessary hard dependency. Its own reader is also broken with
    NumPy >= 2, which removed the binary mode of np.fromstring()."""
    header_struct = struct.Struct('<BdddddQQ2x')
    header = collections.namedtuple('Header', 'version time_start time_stop start stop step samples size')
    magic = b'SDRFF'
    version = 2

    def read(self, f):
        """Read PSD data of one frequency hop from file-like object"""
        magic = f.read(len(self.magic))
        if len(magic) < len(self.magic):
            # End of stream (soapy_power exited or file is exhausted)
            return None
        if magic != self.magic:
            raise ValueError('Magic bytes not found! Read data: {}'.format(magic))

        header = self.header._make(
            self.header_struct.unpack(f.read(self.header_struct.size))
        )
        pwr_array = np.frombuffer(f.read(header.size), dtype='<f4')
        if pwr_array.nbytes != header.size:
            raise ValueError('Incomplete PSD data (expected {} bytes, got {})'.format(
                header.size, pwr_array.nbytes
            ))
        return header, pwr_array


formatter = SoapyPowerBinFormat()


def hop_x_axis(header):
    """Frequency axis of one frequency hop"""
    return np.linspace(header.start, header.stop,
                       round((header.stop - header.start) / header.step))


class Info(BaseInfo):
    """soapy_power device metadata"""
    sample_rate_min = 0
    sample_rate_max = 61440000
    bandwidth_min = 0
    bandwidth_max = 61440000
    start_freq_min = 0
    start_freq_max = 7250
    stop_freq_min = 0
    stop_freq_max = 7250
    gain_min = -1
    gain_max = 999
    bin_size_min = 0
    bin_size_max = 10000
    additional_params = '--even --fft-window boxcar --remove-dc'

    @classmethod
    def help_device(cls, executable, device):
        cmdline = shlex.split(executable)
        try:
            text = subprocess.check_output(cmdline + ['--detect'], universal_newlines=True,
                                           stderr=subprocess.DEVNULL, env=dict(os.environ, COLUMNS='125'),
                                           console=False)
            text += '\n'
            text += subprocess.check_output(cmdline + ['--device', device, '--info'], universal_newlines=True,
                                            stderr=subprocess.DEVNULL, env=dict(os.environ, COLUMNS='125'),
                                            console=False)
        except subprocess.CalledProcessError as e:
            text = e.output
        except OSError:
            text = '{} executable not found!'.format(executable)
        return text


class PowerThread(BasePowerThread):
    """Thread which runs soapy_power process"""
    def setup(self, start_freq, stop_freq, bin_size, interval=10.0, gain=-1, ppm=0, crop=0,
              single_shot=False, device="", sample_rate=2560000, bandwidth=0, lnb_lo=0):
        """Setup soapy_power params"""
        self.params = {
            "start_freq": start_freq,
            "stop_freq": stop_freq,
            "device": device,
            "sample_rate": sample_rate,
            "bandwidth": bandwidth,
            "bin_size": bin_size,
            "interval": interval,
            "hops": 0,
            "gain": gain,
            "ppm": ppm,
            "crop": crop * 100,
            "single_shot": single_shot
        }
        self.lnb_lo = lnb_lo
        self.databuffer = {"timestamp": [], "x": [], "y": []}
        self.min_freq = None

        # Frequency hops of the sweep currently being assembled
        self.timestamp = None
        self.x_chunks = []
        self.y_chunks = []

        self.pipe_read = None
        self.pipe_read_fd = None
        self.pipe_write_fd = None
        self.pipe_write_handle = None

    def process_start(self):
        """Start soapy_power process"""
        if not self.process and self.params:
            # Create pipe used for communication with soapy_power process
            self.pipe_read_fd, self.pipe_write_fd = os.pipe()
            self.pipe_read = open(self.pipe_read_fd, 'rb')
            os.set_inheritable(self.pipe_write_fd, True)

            if sys.platform == 'win32':
                self.pipe_write_handle = subprocess.make_inheritable_handle(self.pipe_write_fd)

            # Prepare soapy_power cmdline parameters
            settings = QtCore.QSettings()
            cmdline = shlex.split(settings.value("executable", "soapy_power"))
            cmdline.extend([
                "-f", "{}M:{}M".format(self.params["start_freq"],
                                       self.params["stop_freq"]),
                "-B", "{}k".format(self.params["bin_size"]),
                "-T", "{}".format(self.params["interval"]),
                "-d", "{}".format(self.params["device"]),
                "-r", "{}".format(self.params["sample_rate"]),
                "-p", "{}".format(self.params["ppm"]),
                "-F", "soapy_power_bin",
                # Fixed buffer sizes keep the sweep rate steady on macOS
                "-s", "65536",
                "-S", "131072",
                "--output-fd", "{}".format(
                    int(self.pipe_write_handle) if sys.platform == 'win32' else self.pipe_write_fd
                ),
            ])

            if self.lnb_lo != 0:
                cmdline.extend(["--lnb-lo", "{}".format(self.lnb_lo)])
            if self.params["bandwidth"] > 0:
                cmdline.extend(["-w", "{}".format(self.params["bandwidth"])])
            if self.params["gain"] >= 0:
                cmdline.extend(["-g", "{}".format(self.params["gain"])])
            if self.params["crop"] > 0:
                cmdline.extend(["-k", "{}".format(self.params["crop"])])
            if not self.params["single_shot"]:
                cmdline.append("-c")

            additional_params = settings.value("params", Info.additional_params)
            if additional_params:
                cmdline.extend(shlex.split(additional_params))

            # Start soapy_power process and close write part of pipe
            if sys.platform == 'win32':
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                creationflags = 0

            print('Starting soapy_power backend:')
            print(' '.join(cmdline))
            print()
            self.process = subprocess.Popen(cmdline, close_fds=False, universal_newlines=False,
                                            creationflags=creationflags, console=False)

            os.close(self.pipe_write_fd)
            if sys.platform == 'win32':
                self.pipe_write_handle.Close()

    def process_stop(self):
        """Stop soapy_power process"""
        with self._shutdown_lock:
            if self.process:
                if self.process.poll() is None:
                    try:
                        if sys.platform == 'win32':
                            self.process.send_signal(signal.CTRL_BREAK_EVENT)
                        else:
                            self.process.terminate()
                        self.process.wait(timeout=1.0)
                    except (ProcessLookupError, subprocess.TimeoutExpired):
                        # If graceful shutdown fails, force kill the process
                        if self.process.poll() is None:
                            self.process.kill()
                            self.process.wait()

            self.process = None

            # Close pipe used for communication with soapy_power process
            if self.pipe_read:
                self.pipe_read.close()

            self.pipe_read = None
            self.pipe_read_fd = None
            self.pipe_write_fd = None
            self.pipe_write_handle = None

    def parse_output(self, data):
        """Parse data from soapy_power"""
        header, y_axis = data

        x_axis = hop_x_axis(header)
        if len(x_axis) != len(y_axis):
            print("ERROR: len(x_axis) != len(y_axis)")
            return

        if self.min_freq is None:
            self.min_freq = header.start

        # Collect the hops of one sweep and join them only once, when the
        # sweep is complete (concatenating on every hop is quadratic)
        if header.start == self.min_freq:
            self.timestamp = header.time_stop
            self.x_chunks = [x_axis]
            self.y_chunks = [y_axis]
        else:
            self.x_chunks.append(x_axis)
            self.y_chunks.append(y_axis)

        if header.stop > (self.params["stop_freq"] * 1e6) - header.step:
            self.databuffer = {
                "timestamp": self.timestamp,
                "x": np.concatenate(self.x_chunks, dtype=np.float64),
                "y": np.concatenate(self.y_chunks, dtype=np.float64),
            }
            self.data_storage.update(self.databuffer)

    def run(self):
        """soapy_power thread main loop"""
        self.process_start()
        self.alive = True
        self.powerThreadStarted.emit()

        while self.alive:
            try:
                data = formatter.read(self.pipe_read)
            except ValueError as e:
                print(e, file=sys.stderr)
                break

            if data:
                self.parse_output(data)
            else:
                break

        self.process_stop()
        self.alive = False
        self.powerThreadStopped.emit()


def read_from_file(f):
    """Generator for reading data from soapy_power binary files"""
    min_freq = None
    timestamp = None
    x_chunks = []
    y_chunks = []

    def sweep():
        return {"timestamp": timestamp,
                "x": np.concatenate(x_chunks, dtype=np.float64),
                "y": np.concatenate(y_chunks, dtype=np.float64)}

    while True:
        try:
            data = formatter.read(f)
        except ValueError as e:
            print(e, file=sys.stderr)
            return

        if not data:
            if min_freq is not None:
                yield sweep()
            return

        header, y_axis = data
        x_axis = hop_x_axis(header)
        if len(x_axis) != len(y_axis):
            print("ERROR: len(x_axis) != len(y_axis)")
            continue

        if min_freq is None:
            min_freq = header.start
        elif header.start == min_freq:
            yield sweep()

        if header.start == min_freq:
            timestamp = header.time_stop
            x_chunks = [x_axis]
            y_chunks = [y_axis]
        else:
            x_chunks.append(x_axis)
            y_chunks.append(y_axis)
