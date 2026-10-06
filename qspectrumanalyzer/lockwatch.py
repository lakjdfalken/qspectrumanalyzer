"""Catching the interpreter lock held long enough to cost the radio samples

libhackrf hands every transfer to Python, and Python code cannot run without
the interpreter lock. A thread that holds it for long - a repaint, a numpy
call that never lets go - keeps the receive callback waiting, libhackrf runs
out of places to put what keeps arriving, and the samples are lost below the
point where the app could count them. The load line shows that it happened,
as a stream short of 100% and a long callback gap. This says who did it.

A thread sleeps a couple of milliseconds at a time, which it cannot wake from
without the lock - the way the callback suffers. Before each sleep it arms
faulthandler's timer, which runs in C and needs no lock, and disarms it on
waking. If waking takes too long the timer goes off and writes down every
thread's stack *while the lock is still held*, so the holder is caught in the
act rather than found wherever it had got to by the time it let go.
"""

import faulthandler
import re
import tempfile
import threading
import time

#: How long libhackrf can be kept waiting before samples are lost. Measured
#: with a HackRF One at 20 MSPS: a 142 ms hold lost 122 ms of signal and a
#: 381 ms hold lost 359, so about 20 ms of transfers are buffered
BUFFERED_SECONDS = 0.020

_THREAD = re.compile(r"^(?:Current thread|Thread) (0x[0-9a-f]+)(?: \[(.*)\])?")
_FRAME = re.compile(r'^\s+File "(.*)", line (\d+) in (.*)$')


class LockWatch:
    """Record what every thread was doing whenever the lock was held too long"""

    def __init__(self, threshold=BUFFERED_SECONDS, period=0.010, depth=4):
        #: Seconds the lock may be held before it is reported. Ordinary
        #: repaints hold it 10-18 ms; past BUFFERED_SECONDS samples are lost
        self.threshold = threshold
        #: Seconds between checks. Arming the timer starts a thread in C, so
        #: this is what the watch costs: 3.4% of a core at 10 ms, measured on
        #: an M1 Pro, where 2 ms cost 8.5%. The timer is armed before the
        #: sleep, so a hold longer than period + threshold is always caught,
        #: and one between threshold and that only if it starts late enough
        #: in the sleep
        self.period = period
        #: Innermost frames kept for each thread
        self.depth = depth
        self._events = []
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="lockwatch", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread = None

    def take(self):
        """Events since the last call, oldest first, as (when, held, stacks)

        `when` is wall clock time, `held` seconds, and `stacks` a list of
        (thread name, [(file, line, function), ...]) innermost frame first."""
        with self._lock:
            events, self._events = self._events, []
        return events

    def _run(self):
        dump = tempfile.TemporaryFile(mode="w+")
        try:
            while not self._stop.is_set():
                # From now, so it covers the sleep as well as any wait after it
                faulthandler.dump_traceback_later(self.period + self.threshold,
                                                  file=dump)
                due = time.monotonic() + self.period
                time.sleep(self.period)
                held = time.monotonic() - due
                faulthandler.cancel_dump_traceback_later()
                if dump.tell():
                    dump.seek(0)
                    text = dump.read()
                    dump.seek(0)
                    dump.truncate()
                    self._record(held, text)
        finally:
            faulthandler.cancel_dump_traceback_later()
            dump.close()

    def _record(self, held, text):
        names = {thread.ident: thread.name for thread in threading.enumerate()}
        stacks = []
        for block in text.split("\n\n"):
            lines = block.strip("\n").splitlines()
            header = _THREAD.match(lines[0]) if lines else None
            if header is None:
                # The "Timeout" line, or a dump cut short
                if len(lines) > 1:
                    header = _THREAD.match(lines[1])
                    lines = lines[1:]
                if header is None:
                    continue
            ident = int(header.group(1), 16)
            name = header.group(2) or names.get(ident, "thread {:#x}".format(ident))
            if name == "lockwatch":
                continue
            frames = [match.groups() for match in map(_FRAME.match, lines[1:]) if match]
            stacks.append((name, frames[:self.depth]))
        with self._lock:
            self._events.append((time.time(), held, stacks))


def describe(event):
    """An event from take() as lines of text"""
    when, held, stacks = event
    lines = ["lock: held {:.0f} ms at {} ({}) - each thread while it was held:".format(
        held * 1e3, time.strftime("%H:%M:%S", time.localtime(when)),
        "longer than the ~20 ms libhackrf buffers, so samples will have been lost"
        if held > BUFFERED_SECONDS + 0.005 else "about as long as libhackrf buffers")]
    for name, frames in stacks:
        where = " <- ".join("{}:{} {}".format(path.rsplit("/", 1)[-1], line, function)
                            for path, line, function in frames)
        lines.append("  {}: {}".format(name, where or "(no Python frames)"))
    return lines
