Hunting an intermittent signal
==============================

Notes on finding something that is only there occasionally — a radar, a burst,
anything with a duty cycle measured in fractions of a per cent. The reasoning
lives here rather than in the application, which reports measurements and lets
you draw the conclusions.

Every figure below was measured on a HackRF at 20 MSPS. Yours will differ; the
ordering will not.


Why sweeping fails
------------------

A surveillance radar lights a fixed point for about 20 ms every 5 seconds, and
its pulses last a microsecond at a kilohertz. The transmitter is therefore on
about four ten-thousandths of one per cent of the time.

A sweep across 200 MHz visits any given 20 MHz tile a tenth of the time, so it
throws away nine pulses in ten: 250 caught in ten minutes against 2500 for a
receiver that stays put. Use **Survey the range**, which camps on each tune for
a dwell before moving on, rather than sweeping across the lot.


Why the settings matter more than the sweeping
----------------------------------------------

What a 1 us pulse reads as, by bin size and detector. The frame count is not
held constant here, because the application does not hold it constant: it
keeps one delivered sweep at 665.6 us however fine the bins are, so 40 kHz
bins average 26 frames and 1250 kHz bins average 832.

    bins        frame      frames/sweep    mean       peak
    40 kHz      25.6 us         26        -28.2 dB   -14.1 dB
    625 kHz      1.6 us        416        -28.2 dB    -2.0 dB
    1250 kHz     0.8 us        832        -28.2 dB     0.0 dB

Read the mean column again: **it does not move.** A mean spreads the pulse
over the whole sweep, and the sweep is 665.6 us whatever the bins are, so the
loss is 10*log10(665.6/1) and the bin size cannot touch it. Every decibel the
bin size is worth is a decibel it is worth *to the peak detector*.

* **Sweep detector** (Settings) decides how the frames making up one delivered
  sweep are combined. *Average* pulls the noise floor down and is right for a
  signal that is always there. *Peak* keeps the loudest frame, so a pulse
  survives at its own height. Choose this first: nothing else in this section
  matters until it is on peak.
* **Bin size** sets the frame length, and a pulse shorter than a frame is
  spread across the whole of it. Coarser bins mean shorter frames, and 28 dB
  of the 28 dB below is bin size — but only once the detector is peak.

An empty survey taken with 40 kHz bins and the average detector says nothing
about pulsed signals. The header of every survey file records which was used,
for exactly this reason.


Gain, and the two amplifiers that are not the same
--------------------------------------------------

The **gain** control fills the LNA first and then the VGA, and the two boxes
below it show the division for a HackRF; either can be set by hand to overrule
it. The LNA sets what the receiver can hear; the VGA is at baseband and lifts
the noise along with the signal. Gain is safe to raise — the worst it does is
compress the reading, and compression is visible: change the gain by 10 dB and
watch whether the trace moves by 10.

At gain 40 the LNA is already full and the VGA reads 0, which is not wasted
headroom: baseband gain cannot make the radio hear anything the LNA did not
pass. The one case where it buys something is a band quiet enough that the
8 bit converter, rather than the air, is setting the floor. The test takes a
minute: add 12 dB of VGA and watch the noise floor. If it rises by 12 there was
nothing there to win; if it rises by less, that difference is signal-to-noise
you were losing in the converter.

The **RF amp** is a separate 14 dB stage ahead of everything. It is never set
by a preset, because it can overload a receiver near a transmitter, and gain
cannot give back headroom lost in front of it.


Reading a survey
----------------

Two columns per bin:

* `loudest_db` — the highest that bin ever reached.
* `active_sweeps` — how many sweeps it stood more than 10 dB above its own
  median.

Together they separate a signal that comes and goes from one that is always on,
which max hold alone cannot: a carrier and a burst can reach exactly the same
height, and the carrier is active in *none* of the sweeps, because a carrier
never stands above its own median.

The application lists what stood out when a survey finishes. The same reading
is available for files already saved:

    python -m qspectrumanalyzer.findings survey-*.csv


Proving a negative
------------------

An empty band means nothing on its own — it looks identical to a broken
measurement. Run the same survey, with the same antenna and settings, over a
band you know is busy: 2400-2500 MHz is full of Wi-Fi and Bluetooth and takes
three minutes.

    band                  floor     loudest   active bins
    2400-2500 (control)   -48.7 dB  -21.5 dB  58 of 160
    2700-2900 (the hunt)  -49.5 dB  -48.2 dB   0 of 320

That is a negative worth trusting. Without the control it is just an absence.


Looking at what you found
-------------------------

**Look at this one** in the findings dialog sets the tune, the band and the
trigger from the measurement. Doing it by hand invites two silent failures:

* **The band outside the tune.** Move the frequency range and the band stays
  where it was. A scope watching 2814.7 MHz while the radio listens to
  2790-2810 hears nothing, and looks exactly like a band with nothing in it.
* **The trigger level under the trace.** A trigger fires where the trace
  crosses the level going *up*. The scope's tap reads the peak across a band's
  bins frame by frame, so its floor sits well above the spectrum's — a level
  chosen by looking at the plot above can be 20 dB too low, and will wait for
  ever. Aim for about 5 dB above the *scope's* floor, or leave the level on
  `auto`.

The readout in the corner of the scope says which of these is wrong, and a
single shot that fires prints what it caught: the window's floor, its peak,
and whether the reading that fired the trigger is in the window at all. Read
that line before believing a capture. A window whose peak stands 2-3 dB above
its own floor caught noise, however much the trace looks like a signal — the
pane scales itself to whatever it holds, so noise fills it exactly as a burst
does.

That is the trap on the other side of a level set too low. At 625 kHz bins the
tap reads 600,000 times a second, so a level 3 dB above the floor is one the
noise itself crosses about fifty times a second and a single shot catches
within seconds, every time. Measured on this receiver: the tap's noise is
0.5 dB wide (median to the 16th percentile) and reaches 3.0 dB above its own
floor in 12,500 readings. Anything to be triggered on has to stand clear of
*that*, not of the average.


Finding a pulse train that cannot be triggered on
-------------------------------------------------

A trigger asks whether a reading is loud, and that question has a floor which
is not set by the receiver. The tap reads 600,000 times a second, and the
loudest of that many samples of noise stands about 6 dB above the floor within
a single sweep and 11 dB over a minute of looking. So **a pulse less than about
11 dB above the floor cannot be told from noise by its height**, wherever the
level is put. Measured on this receiver: the tap's noise is 0.67 dB wide
(median to the 16th percentile) and reached 8.8 widths in one 20 ms window.

**Look for a repeating pulse...** asks a different question. A radar sends a
pulse every 0.8-4 ms and keeps the interval to a fraction of a microsecond for
hours; noise never repeats. Stacking a thousand pulses in step lifts them
30 times clear of noise stacked out of step, so where a trigger gets worse the
longer it looks, this gets better. Verified against this receiver's own
recorded noise: a 1 kHz train **6 dB below the loudest noise reading** — with
nothing whatever visible on the trace — is found at 1000.00 Hz.

Two settings decide whether it can work:

* **The zero span step, in Settings.** The tap buffer holds a million readings
  however fine they are: 1.7 s at the finest step, 10 s at 10 us. A rotating
  radar points this way for 30-80 ms every several seconds, so 1.7 s usually
  misses it entirely. A coarser step costs the pulse nothing — the **peak**
  detector keeps the loudest frame of each group, so a 1 us pulse still reads
  at full height in a 10 us reading — and only the pulse's measured *shape*
  is lost, which is not what the search is reading. Measured: a 60 ms dwell of
  632 Hz pulses 6 dB above the floor is invisible at the finest step (the
  buffer does not reach it) and found at 632.09 Hz at 10 us.
* **The detector must stay on peak.** Averaging a group destroys a pulse
  shorter than the group, which is the whole signal.

The report gives the interval between pulses, how wide each one is, how many
were stacked and how far the stack stands above the noise. A rate under about
5 sigma is not reported at all; the search looks at tens of thousands of rates,
so it has to be strict.


Telling one thing from another
------------------------------

By the time structure:

* **Pulse width** — a plain radar pulse is around a microsecond and occupies a
  couple of megahertz. Something several megahertz wide is either chirped
  (pulse compression) or is not a radar.
* **Spacing within a burst** — even spacing is a pulse repetition frequency.
  Ragged spacing is data traffic.
* **Between bursts** — the antenna's rotation. Roughly 4-12 s for air traffic
  surveillance. A weather radar steps through elevations, so it gives a burst
  every 15-25 s for a few minutes and then a gap of minutes.

Use **Single sweep** and **Arm** to freeze one burst and measure it, and
**Save sweep** to keep it. Park the cursor on the leading edge and the readout
gives width and repetition rate directly.


A worked example: the 2777.5 MHz emitter
---------------------------------------

Measured 2026-08-31 over about half an hour, twelve single-shot captures.
HackRF at 20 MSPS tuned 2760-2780 MHz, 1250 kHz bins (0.8 us frames), gain 64
dB as LNA 40 + VGA 24 with the RF amp on, peak detector throughout.

Three pulses in a group, then a long silence:

        217 us ON  --24 us--  121 us ON  --142 us--  87 us ON  --- silence ---
        |<-- starts 241 us apart -->|<-- 265-281 us apart -->|

    pulse 1    216.0-217.7 us    seen in 8 of 8 captures
    pulse 2    120-123 us        seen in 6 of 8, 240-243 us after pulse 1
    pulse 3    86-88 us          seen in 2 of 8, only where the window reached

All three sit about 12 dB above the floor on a four-bin band and about 16 dB on
one bin. Every capture that caught the sequence caught the same sequence; two
caught it at a different phase, which is what the odd 356 and 416 us spacings
in the log are.

**Each pulse is continuous, not a train.** At one frame a reading, only 0.8% of
the readings inside pulse 1 fall back into the noise; a train of microsecond
pulses a few microseconds apart would put half to four fifths of them there.
The giveaway is that the spread of readings *inside* the pulse is 7.8 dB from
the 10th to the 90th percentile and the spread of pure noise is 7.7 dB — the
same distribution, lifted 12.6 dB. A single-frame FFT reading of a steady
signal fluctuates exactly as noise does, which is why a trigger set part way up
counts one 217 us pulse as a hundred and thirteen. That is the measurement
wobbling, not the signal.

**Each pulse is narrowband.** Widening the band from four bins to five left
pulse 1 at 217.68 us where a chirp filling the band would have stretched it to
271; narrowing to the single 2777.5 MHz bin left it at 211 us where a chirp
over 5 MHz would have cut it to 54. Narrowing also *gained* 3.8 dB of signal to
noise, which is the three bins of noise no longer being collected. So the
energy fits inside 1.25 MHz and the width is the real pulse width.

That last pair of measurements is the general method: **change the band width
and see whether the measured duration follows it.** If it does, you are timing
how long a chirp takes to cross your window, not how long the pulse is.

**The group repeats no faster than once per 20 ms.** In a 20 ms window at a 5
us step, zero of the 2396 readings after the group are more than 6 dB above the
floor. A surveillance radar runs at 300-1500 Hz, which is a group every 0.7 to
3.3 ms, so either this is not one, or most of its pulses are not landing in the
band being watched. See below.


Why a rotating radar can look continuous
----------------------------------------

Six revolutions a minute is ten seconds a turn. An antenna with a 1.4 degree
azimuth beam therefore lights a fixed point for 1.4/360 of ten seconds, which
is **39 ms every 10 s** — four tenths of one per cent of the time. If what you
were hearing were the main beam, the display would be empty for ten seconds at
a stretch and you would be waiting for it.

Seeing something continuously means you are not hearing the main beam. You are
hearing the **sidelobes**, which are there at every antenna angle and do not
care where the dish is pointing. Near sidelobes run 25-30 dB below the main
beam and the back lobe 35-45 dB below, so a transmitter close enough or strong
enough puts its sidelobes well above the noise on their own.

That is worth knowing because it is testable, and the test is not subtle. Set
the scope span to a second or two — long enough to hold several dwells — and
count how many readings clear the floor in each 20 ms of it. Amplitude is the
wrong thing to watch when the pulses are near the level: what a beam sweeping
past changes most visibly is the *rate* at which pulses get over it.

Measured on the 2777.5 MHz emitter, a 2 s window at a 5 us step:

    -830 to -140 ms    0 readings clear the floor by 6 dB
    -120 ms            the first ones appear
    +100 to +240 ms    44-57 per 20 ms, the peak of the beam
    +400 ms            down to a handful
    +600 to +1230 ms   nothing again

That looks like scanning: on for about 600 ms, then nothing. The lesson about
the span stands whatever it turns out to be — **the span has to be longer than
the thing you are asking about.** A 2 ms span answers what a pulse looks like;
it cannot answer how often the beam comes round, and it will report "present"
either way.

But that measurement was taken on the whole tune, with the floor 15 dB up for
the reasons in the next section, and a later 4 s capture on a proper band shows
no envelope at all — a steady rhythm right across it. Its peak also differs,
-20.1 dB on the whole tune against -24 on the band. So the 600 ms envelope is
most likely **a different emitter somewhere else in the 20 MHz**, and folding
the two into one story would have been wrong. When a wide band and a narrow one
disagree about whether something is intermittent, believe the narrow one and
assume the wide one is showing you two things at once.


A stable rhythm, and a phase step
---------------------------------

The same emitter measured properly — band 2775.5-2779.5 MHz, 4 s span, 5 us
step, no trigger — gives 38 pulse groups and this:

    interval between groups   102.3339 ms   (9.7719 Hz)
    scatter about that        0.015 ms rms over 36 intervals
    group width               365 us median (the 217 + 24 + 121 us sequence)

That is a rhythm held to about one part in seven thousand, and the residual is
mostly the 4.77 us reading step rather than the emitter. Nothing is modulating
it across the four seconds.

One interval is different: 191.87 ms, where a missed group would have given
204.67. Lining every group up against a 102.3339 ms grid shows why. The phase
sits within +-0.010 ms for twenty-four periods, steps by -12.797 ms, and then
sits within +-0.010 ms again for twelve more. It is not drift and it is not
jitter — it is one instantaneous move, and **12.797 ms is one eighth of
102.3339 ms** to within 5 us.

Folding the whole four seconds on that eighth-period shows nothing at the other
seven slots, at any threshold, so there is no faster train being caught one
time in eight. The emitter really does repeat at 102.33 ms and really did
advance itself by exactly an eighth of that, once.

Worth writing down as a method rather than as a conclusion about this emitter:
**an interval that is not a whole multiple of the period is worth more than the
period is.** A missed detection gives exactly 2x, 3x, 4x. Anything else means
the source moved, and the size of the move — here a clean eighth — says
something about how it is built that a stable rhythm never could.


Watching the whole tune costs more than it looks
------------------------------------------------

The obvious way to catch a frequency-agile emitter is to untick **One frequency
band only** so the tap reads every bin. It is usually the wrong move, and the
numbers say why:

    band                  floor      10th-90th spread of the floor
    one bin, 2777.5 MHz   -43.9 dB          5.0 dB
    whole tune, 16 bins   -29.3 dB          1.3 dB

Peak-detecting sixteen bins of noise instead of one should lift the floor about
6.6 dB and narrow its spread to about 3. The floor went up 14.6 dB and the
spread collapsed to 1.3, which noise cannot do: a spread that small means the
reading is pinned by something deterministic. It is the receiver's own DC
carrier. The whole tune includes the centre bins, and **the band tap reads raw
bins — it is never flattened, whatever the spectrum shows.**

So watching everything cost 15 dB of sensitivity and put a signal that stood
16 dB clear on one bin down to 6-9 dB. If you must widen the band, widen it to
one side of the centre — 2772-2779 rather than the lot — or offset-tune so the
spike is outside the span in the first place. The scope readout says so when
the band covers the centre; it is worth believing.


Antenna lengths
---------------

A monopole works at odd quarter waves, so an adjustable whip is several
antennas:

    target              1/4 wave   3/4 wave
    airband 127 MHz      561 mm     1682 mm
    1030 MHz             69 mm       207 mm
    1090 MHz             65 mm       196 mm
    2800 MHz             25 mm        76 mm
    5625 MHz             13 mm        38 mm

A whip left at airband length is twenty-two quarter waves at 2800 MHz: a comb
of nulls rather than an antenna. A directional panel, even badly matched,
usually beats a well-matched whip — 8-14 dBi of gain against 2, and it rejects
what is behind it.
