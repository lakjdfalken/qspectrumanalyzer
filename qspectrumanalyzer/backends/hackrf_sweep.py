import struct, shlex, sys, time

import numpy as np
from Qt import QtCore

from qspectrumanalyzer import subprocess
from qspectrumanalyzer.backends import BaseInfo, BasePowerThread


class Info(BaseInfo):
    """hackrf_sweep device metadata"""
    sample_rate_min = 20000000
    sample_rate_max = 20000000
    sample_rate = 20000000
    gain_min = -1
    gain_max = 102
    gain = 40
    start_freq_min = 0
    start_freq_max = 7230
    start_freq = 0
    stop_freq_min = 0
    stop_freq_max = 7250
    stop_freq = 6000
    bin_size_min = 3
    bin_size_max = 5000
    bin_size = 1000
    interval = 0
    ppm_min = 0
    ppm_max = 0
    ppm = 0
    crop_min = 0
    crop_max = 0
    crop = 0


class PowerThread(BasePowerThread):
    """Thread which runs hackrf_sweep process"""
    def setup(self, start_freq=0, stop_freq=6000, bin_size=1000,
              interval=0.0, gain=40, ppm=0, crop=0, single_shot=False,
              device=0, sample_rate=20000000, bandwidth=0, lnb_lo=0):
        """Setup hackrf_sweep params"""
        # Small bin sizes (<40 kHz) are only suitable with an arbitrarily
        # reduced sweep interval. Bin sizes smaller than 3 kHz showed to be
        # infeasible also in these cases.
        if bin_size < 3:
            bin_size = 3
        if bin_size > 5000:
            bin_size = 5000

        # We only support whole numbers of steps with bandwidth equal to the
        # sample rate.
        step_bandwidth = sample_rate / 1000000
        total_bandwidth = stop_freq - start_freq
        step_count = 1 + (total_bandwidth - 1) // step_bandwidth
        total_bandwidth = step_count * step_bandwidth
        stop_freq = start_freq + total_bandwidth

        # distribute gain between two analog gain stages
        if gain > 102:
            gain = 102
        lna_gain = 8 * (gain // 18) if gain >= 0 else 0
        vga_gain = 2 * ((gain - lna_gain) // 2) if gain >= 0 else 0

        self.params = {
            "start_freq": start_freq,  # MHz
            "stop_freq": stop_freq,  # MHz
            "hops": 0,
            "device": 0,
            "sample_rate": 20e6,  # sps
            "bin_size": bin_size,  # kHz
            "interval": interval,  # seconds
            "gain": gain,
            "lna_gain": lna_gain,
            "vga_gain": vga_gain,
            "ppm": 0,
            "crop": 0,
            "single_shot": single_shot
        }
        self.lnb_lo = lnb_lo
        self.databuffer = {"timestamp": [], "x": [], "y": []}
        self.x_chunks = []
        self.y_chunks = []
        self.lastsweep = 0
        self.interval = interval

    def process_start(self):
        """Start hackrf_sweep process"""
        if not self.process and self.params:
            settings = QtCore.QSettings()
            cmdline = shlex.split(settings.value("executable", "hackrf_sweep"))
            cmdline.extend([
                "-f", "{}:{}".format(int(self.params["start_freq"] - self.lnb_lo / 1e6),
                                     int(self.params["stop_freq"] - self.lnb_lo / 1e6)),
                "-B",
                "-w", "{}".format(int(self.params["bin_size"] * 1000)),
            ])

            if self.params["gain"] >= 0:
                cmdline.extend([
                    "-l", "{}".format(int(self.params["lna_gain"])),
                    "-g", "{}".format(int(self.params["vga_gain"])),
                ])

            if self.params["single_shot"]:
                cmdline.append("-1")

            additional_params = settings.value("params", Info.additional_params)
            if additional_params:
                cmdline.extend(shlex.split(additional_params))

            print('HackRF Starting backend:')
            print(' '.join(cmdline))
            print()
            self.process = subprocess.Popen(cmdline, stdout=subprocess.PIPE,
                                            universal_newlines=False, console=False)

    def parse_output(self, buf):
        """Parse one buf of output from hackrf_sweep"""
        (low_edge, high_edge) = struct.unpack('QQ', buf[:16])
        data = np.frombuffer(buf[16:], dtype='<f4')  # frombuffer is faster than fromstring
        step = (high_edge - low_edge) / len(data)

        # Start of a new sweep
        if (low_edge // 1000000) <= (self.params["start_freq"] - self.lnb_lo / 1e6):
            self.x_chunks = []
            self.y_chunks = []

        # linspace() instead of arange(), which can be off by one bin because
        # of floating point rounding of the step
        self.x_chunks.append(np.linspace(low_edge + self.lnb_lo + step / 2,
                                         high_edge + self.lnb_lo - step / 2,
                                         len(data)))
        self.y_chunks.append(data)

        if (high_edge / 1e6) >= (self.params["stop_freq"] - self.lnb_lo / 1e6):
            # We've reached the end of a pass. If it went too fast for our sweep interval, ignore it
            t_finish = time.time()
            if (t_finish < self.lastsweep + self.interval):
                return
            self.lastsweep = t_finish

            # hackrf_sweep emits the tiles out of order, so join the whole
            # sweep in one go and sort it with argsort() (concatenating and
            # sorting in Python on every tile is much slower)
            x = np.concatenate(self.x_chunks, dtype=np.float64)
            y = np.concatenate(self.y_chunks, dtype=np.float64)
            order = np.argsort(x, kind="stable")
            self.databuffer = {"timestamp": t_finish, "x": x[order], "y": y[order]}
            self.data_storage.update(self.databuffer)

    def run(self):
        """hackrf_sweep thread main loop"""
        self.process_start()
        self.alive = True
        self.powerThreadStarted.emit()

        while self.alive:
            try:
                buf = self.process.stdout.read(4)
            except AttributeError as e:
                print(e, file=sys.stderr)
                continue

            if buf:
                (record_length,) = struct.unpack('I', buf)
                try:
                    buf = self.process.stdout.read(record_length)
                except AttributeError as e:
                    print(e, file=sys.stderr)
                    continue

                if buf:
                    self.parse_output(buf)
                else:
                    break
            else:
                break

        self.process_stop()
        self.alive = False
        self.powerThreadStopped.emit()
