# Faster wideband scanning with the HackRF One

Briefing for work on `lakjdfalken/qspectrumanalyzer` and `lakjdfalken/hackrf_stream`.
Goal: scan wide ranges faster than the current `hackrf_sweep` backend.

The limit and the usable bandwidth below are measured (2026-10-19, HackRF One r10,
firmware v2.4.0, libhackrf 2026.01.3) or read from the firmware source. The rest
are suggestions; measure before and after every change.

## Current state

- `qspectrumanalyzer/backends/hackrf_sweep.py` runs `hackrf_sweep` as a subprocess:
  `-f start:stop -B -w <bin_hz>`, plus `-d`, `-l`/`-g`, `-a 1`, `-1` when set.
  With the Bands field filled in it passes one `-f` per band, up to 10 (idea 1, done).
- Output is read as binary records (`read(4)` length, then `read(n)`), each tile parsed
  in `parse_output()`: `np.linspace` x-axis per tile, chunks collected, then
  `concatenate` + `argsort` once per sweep, converted to float64.
- Sweeps arriving sooner than `interval` are silently dropped.
- `hackrf_stream` (own library, ctypes-style loading of libhackrf) stays on one tune:
  ~1500 spectra/s, 100% of the USB stream, max 20 MHz span. Wider spans are handed
  to another backend.
- Measured ceiling of `hackrf_sweep`: ~405 steps of 20 MHz per second (~8 GHz/s).

## The real limit

The ceiling is set by the firmware's sample timing, not by the host and not by
waiting for the PLLs to lock. From `firmware/hackrf_usb/usb_api_sweep.c`:

- For every 16 KB block it keeps (8192 samples, 0.41 ms at 20 MSPS), the firmware
  discards two more (`THROWAWAY_BUFFERS 2`, 0.82 ms) while it retunes. The retune is
  ~760 µs worst case, per a comment in the source.
- So each kept block costs 3 × 0.41 = 1.23 ms of samples: **~814 blocks/s**,
  ~13 MB/s over USB.
- `hackrf_sweep` uses INTERLEAVED style: two blocks per 20 MHz step (tuned +0 and
  +5 MHz), **10 MHz used per block**. 814 × 10 MHz ≈ 8 GHz/s, which matches the
  measured 405 steps/s exactly.
- The discard happens after every block, even when dwelling without retuning
  (`dwell_blocks > 1`).

Bin size does not change the rate (measured constant from 40 kHz to 5 MHz bins).
A full 0–6 GHz pass is ~0.75 s. Real gains come from: fewer blocks (scan less),
more usable MHz per block, more radios, or less discard per block in firmware.

## Usable bandwidth of one block (measured)

With `hackrf_stream` held on one tune, 39 kHz bins. Noise shape is the median over
24 quiet L-band tunes. Signal response and aliasing come from a 300 kHz slice of the
AP's frames on 5 GHz ch 124, stepped from −13 to +13 MHz across baseband and gated
on the AP transmitting.

| | 15 MHz filter (default) | 20 / 24 / 28 MHz filters |
|---|---|---|
| Noise floor to ±7.5 MHz | flat within ±0.2 dB | rising from ~4–5 MHz |
| Noise floor at ±9.9 MHz | −2.5 dB | +1.5 to +2.7 dB (folded noise) |
| Source 0.5–1 MHz past Nyquist folds in | ~5–9 dB down | ~2–6 dB down |
| Source 2–3 MHz past Nyquist folds in | ~10–15 dB down | ~2–6 dB down |
| DC spike | ±1 bin: +32 dB at centre, +26 dB at ±39 kHz, floor by 80 kHz | same |

- The noise figures agree within 0.3 dB over two runs. The alias figures are rough
  (±3–5 dB, AP traffic varies; the 28 MHz run drifted 8.5 dB and is unreliable).
- **Aliasing sets the edge, not filter roll-off.** Wider filters let more of what lies
  beyond ±10 MHz fold back in. Keep the 15 MHz filter; no profile should rely on a
  wider one.
- `hackrf_sweep` discards ±2.5 MHz around the centre to avoid a spike that is
  ~120 kHz wide. That is where the spare bandwidth is.
- Side effect worth checking before trusting a weak find: `hackrf_sweep` keeps up to
  ±7.5 MHz, so its edges already take aliases of sources at ±12.5 MHz and beyond,
  ~13 dB down. A weak signal 20 MHz away from a strong one may be a ghost.
- IQ images land mirrored about the centre in every style, so they are no reason to
  prefer interleaved.
- Spurs: an internal spur at 100.0 MHz (strongest thing at LNA 0 / VGA 0).

## Ideas, by expected payoff

### 1. Scan less spectrum
- **Done: the Bands field** (Frequency, under Stop), e.g. `2400-2500, 5150-5850`, and
  the "Wi-Fi activity — 2.4 and 5 GHz at once" preset. One `-f` per band to the
  existing subprocess backend. Measured: **10.1 sweeps/s against 2.0** for one range
  over 2400–5850 MHz, the 405 steps/s ceiling either way. Time scales with total MHz
  covered; each band is rounded up to whole 20 MHz steps.
  - `hackrf_sweep` goes through the bands in the order given, so a sweep still starts
    at the lowest band's start and ends at the top of the highest.
  - The gaps are filled with NaN bins at the same spacing, so the axis stays evenly
    spaced for the waterfall. Auto-range, waterfall levels and the scope's peak across
    bins use `np.fmin`/`np.fmax` so the gap does not win. Smoothing still spreads NaN
    half a window into each band's inner edge.
  - Bands apply only while Start/Stop show their overall span; anything that moves the
    span (a survey slice, the interference retune) sweeps that one range instead.
- Two-stage scan: fast coarse sweep with large bins, flag tiles standing above their
  own running median (same idea as the survey's `active_sweeps`), then dwell on those
  tiles with `hackrf_stream`.
- Weighted revisits: busy tiles swept more often than quiet ones.

### 2. More radios
- Two HackRFs, split ranges, each via `-d <serial>` (or `serial=` in native mode).
  `list_hackrfs()` already enumerates devices. Merge results per sweep. Only route to a
  true 2x without firmware work.

### 3. Native sweep mode in `hackrf_stream`
Drive libhackrf's firmware sweep directly instead of the `hackrf_sweep` subprocess.
Same firmware ceiling (~814 blocks/s) and no speed gain by itself, but it enables:
- LINEAR style with a custom step (idea 4), the main speed lever,
- changing ranges without restarting a process (needed for ideas 1b/1c),
- a peak detector across frames per tune instead of hackrf_sweep's averaged output,
- no pipe of binary records into Python.

Work breakdown (estimate ~1 week for a solid version, 1–2 days for a prototype):

| Piece | Estimate | Notes |
|---|---|---|
| Bindings | ½ day | `hackrf_init_sweep(device, freq_list, num_ranges, num_bytes, step_width, offset, style)` and `hackrf_start_rx_sweep()`. Verify signatures against installed `hackrf.h`. Up to 10 ranges. |
| Block parsing | ~1 day | Split each transfer into 16 KB blocks; each starts with `0x7f 0x7f` and the tuned frequency as a little-endian uint64 (bytes 2–9), then samples. `hackrf_sweep.c` is the reference. |
| Spectrum assembly | 1–2 days | FFT per block, keep the usable slice (idea 4), place it on a precomputed frequency axis, detect sweep wrap. Add peak detector across frames if dwell > 1 block. |
| QSA backend | ~1 day | New backend class next to `hackrf_stream`; wire into settings and the >20 MHz hand-off. |
| Validation | 1–2 days | Side by side with `hackrf_sweep` on 2400–2500 MHz (busy control band per HUNTING.md): levels, bin placement, sweep rate. Tests in the existing no-radio style (`python3 -m hackrf_stream.tests`). |

Risks:
- Slice placement off-by-one-bin errors. The side-by-side comparison catches them.
- GIL: the receive callback must stay copy-only (same as today), since libhackrf only
  buffers ~20 ms of transfers.
- Measure early how long a sweep re-init takes; adaptive scanning depends on it being fast.

### 4. Use more of each block (host side, no firmware change)
Interleaved geometry: 15 MHz baseband filter, tune 7.5 MHz above the step, keep only
2.5–7.5 MHz either side of the centre, repeat 5 MHz higher. Half of each block is
discarded, mostly the centre.

The measurements above say the edges should stay at ±7.5 MHz, but the centre can be
kept almost entirely:
- **LINEAR style, step 15 MHz, keep |bb| ≤ 7.5 MHz minus a ±1-bin DC notch:**
  ~15 MHz per block instead of 10, **~1.5x**, with the same edge and alias exposure
  as `hackrf_sweep` today. The firmware supports LINEAR; `hackrf_sweep` hard-codes
  INTERLEAVED, so this needs native mode (idea 3).
- Keeping ±8 MHz (16 MHz step) gives ~1.6x at somewhat more alias exposure.
- The notch leaves ~120 kHz unmeasured per block. Fill it by shifting alternate sweeps
  by half a step, or show it as a gap; don't interpolate it silently.
- Optional: a per-bin flatness correction from the noise shape (0.2 dB to ±7.5 MHz on
  the 15 MHz filter is already small).
- HackRF issue #864 discusses other profiles (e.g. 12 MHz filter, 10 MHz offset,
  16 MHz step). Check them against the alias figures before adopting a narrower filter.

### 5. Firmware (greatscottgadgets/hackrf, GPL-2.0)
Firmware is open source (LPC43xx, ARM GCC, flashed with `hackrf_spiflash`, DFU button
for recovery). Firmware and libhackrf versions must match.
The settling question is answered by the source: a fixed discard of two 16 KB blocks
(0.82 ms) per kept block, against a ~760 µs worst-case retune. Avenues:
- **Skip the discard when not retuning.** With `dwell_blocks > 1` the discard still
  runs after every block. Skipping it there makes dwelling (and a peak detector) ~3x
  cheaper per block.
- **Discard one block where the retune is fast.** 3 → 2 blocks per kept block is at
  most ~1.5x, and only where the retune fits in 410 µs (e.g. ~2.2–2.7 GHz, where the
  external mixer is bypassed). Needs a per-band or measured lock time; instrument the
  retune (cycle counter or GPIO toggle) first.
- **Retune less hardware (hypothesis, unverified).** Moving only the transceiver IF
  across several steps while keeping the mixer LO fixed could avoid the slower relock.
- Check board revision: newer HackRF One revisions changed RF parts, so timing tuned on
  one may not hold on another.

### 6. Small code wins in `hackrf_sweep.py` (only if Python falls behind)
- Precompute the x-axis once per sweep layout; write each tile into a preallocated array
  at its offset instead of `linspace` + `concatenate` + `argsort` every sweep.
- Keep data float32; convert only for drawing.
- Read the pipe in large chunks and split records with numpy instead of two `read()`
  calls per record.
- Ensure `interval = 0` when maximum rate is wanted.
- At ~1600 records/s the parser is unlikely to be the bottleneck. Profile first.

### 7. Setup checks
- Firmware matches libhackrf / hackrf-tools version.
- HackRF plugged directly into a USB port, not a hub or dock.
- Bin size does not affect the sweep rate (measured flat from 40 kHz to 5 MHz).

### 8. Hardware (if 20 MHz per tune is the wall)
SDRs with ~56 MHz instantaneous bandwidth (bladeRF 2.0, USRP B210) cover nearly 3x per tune.

## Suggested order
1. ~~Multi-range band list in the existing `hackrf_sweep` backend (repeated `-f`).~~ Done.
2. Native sweep mode bindings + block parser, tested against a real HackRF.
3. LINEAR 15 MHz profile (idea 4), measured against `hackrf_sweep` for rate, levels
   and ghosts.
4. Two-stage / weighted scanning on top of native mode.
5. Firmware: skip the discard while dwelling; per-band discard only if the
   instrumented retune times justify it.

## References
- Fork: https://github.com/lakjdfalken/qspectrumanalyzer (README, HUNTING.md,
  `qspectrumanalyzer/backends/hackrf_sweep.py`)
- Library: https://github.com/lakjdfalken/hackrf_stream
- HackRF source (firmware, libhackrf, `hackrf_sweep.c`): https://github.com/greatscottgadgets/hackrf
  - Sweep firmware: `firmware/hackrf_usb/usb_api_sweep.c` (tag v2024.02.1)
- Sweep geometry / profiles discussion: https://github.com/greatscottgadgets/hackrf/issues/864
- Sweep mode description (block size, interleaved sub-steps):
  https://docs.rs/waverave-hackrf/latest/aarch64-unknown-linux-gnu/waverave_hackrf/struct.Sweep.html
- Sweep mode release notes: https://github.com/greatscottgadgets/hackrf/releases/tag/v2017.02.1
