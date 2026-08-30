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

What a 1 us pulse reads as, by bin size and detector:

    40 kHz bins, mean of 26 frames    frame 25.6 us    -28.2 dB
    625 kHz bins, mean of 26 frames   frame  1.6 us    -16.2 dB
    40 kHz bins, peak of 26 frames    frame 25.6 us    -14.1 dB
    625 kHz bins, peak of 26 frames   frame  1.6 us     -2.0 dB

Two settings, 26 dB between them:

* **Bin size** sets the frame length, and a pulse shorter than a frame is
  spread across the whole of it. Coarser bins mean shorter frames.
* **Sweep detector** (Settings) decides how the frames making up one delivered
  sweep are combined. *Average* pulls the noise floor down and is right for a
  signal that is always there. *Peak* keeps the loudest frame, so a pulse
  survives at its own height.

An empty survey taken with 40 kHz bins and the average detector says nothing
about pulsed signals. The header of every survey file records which was used,
for exactly this reason.


Gain, and the two amplifiers that are not the same
--------------------------------------------------

The **gain** control fills the LNA first and then the VGA. The LNA sets what
the receiver can hear; the VGA is at baseband and lifts the noise along with
the signal. Gain is safe to raise — the worst it does is compress the reading,
and compression is visible: change the gain by 10 dB and watch whether the
trace moves by 10.

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

The readout in the corner of the scope says which of these is wrong.


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
