#!/usr/bin/env python3
"""
Generate original, royalty-free background music for AIM TRAINER.

Everything here is synthesized from scratch (no samples from existing
recordings), so the output can be released as CC0 / public domain.

Outputs (16-bit PCM stereo, 44.1 kHz, written next to this script):
  menu.wav     ~21s seamless cyberpunk/synthwave loop for the menu
  results.wav  ~11s "target cleared" outro for the results screen

Run:  python music/generate_music.py
"""
import math
import wave
from pathlib import Path

import numpy as np

SR = 44100
HERE = Path(__file__).resolve().parent

# deterministic noise
RNG = np.random.default_rng(20261021)


# ---------------------------------------------------------------- basics
def m2f(midi):
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def pan_gains(pan):
    pan = float(np.clip(pan, -1.0, 1.0))
    return math.sqrt((1.0 - pan) / 2.0), math.sqrt((1.0 + pan) / 2.0)


def add(bus, sig, start, gain=1.0, pan=0.0):
    """Mix a mono signal into a stereo bus at `start` seconds."""
    i = int(round(start * SR))
    if i >= len(bus):
        return
    n = min(len(sig), len(bus) - i)
    if n <= 0:
        return
    gl, gr = pan_gains(pan)
    seg = sig[:n] * gain
    bus[i:i + n, 0] += seg * gl
    bus[i:i + n, 1] += seg * gr


def env_ar(n, attack, release):
    env = np.ones(n)
    a = min(n, int(attack * SR))
    r = min(n, int(release * SR))
    if a > 1:
        env[:a] = np.linspace(0.0, 1.0, a)
    if r > 1:
        env[-r:] *= np.linspace(1.0, 0.0, r)
    return env


# ---------------------------------------------------------------- instruments
def pad(freq, dur, attack=1.0, release=2.2, bright=0.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    partials = [
        (1.0, 1.00, 0.0000),
        (1.0, 0.62, 0.0045),
        (1.0, 0.62, -0.0045),
        (2.0, 0.24 * bright, 0.0025),
        (3.0, 0.10 * bright, -0.0018),
        (4.0, 0.045 * bright, 0.0010),
    ]
    for mult, amp, det in partials:
        x += amp * np.sin(2.0 * np.pi * freq * mult * (1.0 + det) * t)
    x *= env_ar(n, attack, release)
    return x / 2.6


def bass(freq, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = (
        np.sin(2.0 * np.pi * freq * t)
        + 0.35 * np.sin(4.0 * np.pi * freq * t)
        + 0.12 * np.sin(6.0 * np.pi * freq * t)
    )
    x = np.tanh(1.5 * x)
    env = np.full(n, 0.62)
    a = min(n, int(0.008 * SR))
    d = min(n, int(0.11 * SR))
    r = min(n, int(0.22 * SR))
    if a > 0:
        env[:a] = np.linspace(0.0, 1.0, a)
    if d > 0:
        env[a:a + d] = np.linspace(1.0, 0.62, d)
    if r > 0:
        env[-r:] *= np.linspace(1.0, 0.0, r)
    return x * env


def pluck(freq, dur=0.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    env = np.exp(-t * 8.5) * (1.0 - np.exp(-t * 180.0))
    x = (
        np.sin(2.0 * np.pi * freq * t)
        + 0.30 * np.sin(4.0 * np.pi * freq * t)
        + 0.12 * np.sin(6.0 * np.pi * freq * t)
    )
    return x * env


def lead(freq, dur, attack=0.12, release=0.8):
    """Soft mid-range lead with a little vibrato."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    vib = 1.0 + 0.0035 * np.sin(2.0 * np.pi * 4.8 * t)
    phase = 2.0 * np.pi * np.cumsum(freq * vib) / SR
    x = np.sin(phase) + 0.34 * np.sin(2.0 * phase) + 0.13 * np.sin(3.0 * phase)
    return x * env_ar(n, attack, release) / 1.55


def bell(freq, dur=1.8):
    n = int(dur * SR)
    t = np.arange(n) / SR
    env = np.exp(-t * 2.8)
    x = (
        np.sin(2.0 * np.pi * freq * t)
        + 0.45 * np.sin(2.0 * np.pi * freq * 2.01 * t) * np.exp(-t * 5.0)
        + 0.22 * np.sin(2.0 * np.pi * freq * 3.97 * t) * np.exp(-t * 7.0)
    )
    return x * env


def shimmer(freq, dur, attack=1.5, release=2.0):
    """Soft high chord tone that fades in/out slowly."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2.0 * np.pi * freq * t) + 0.4 * np.sin(2.0 * np.pi * freq * 2.0 * t)
    trem = 0.75 + 0.25 * np.sin(2.0 * np.pi * 0.12 * t + 0.7)
    return x * env_ar(n, attack, release) * trem / 2.0


def air(dur, level=0.012):
    """Very quiet high-frequency air bed."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = RNG.normal(0.0, 1.0, n)
    x = np.diff(np.diff(x, prepend=0.0), prepend=0.0)
    x /= np.std(x) + 1e-9
    return x * level * (0.72 + 0.28 * np.sin(2.0 * np.pi * 0.05 * t))


def kick(dur=0.42):
    n = int(dur * SR)
    t = np.arange(n) / SR
    freq = 42.0 + 112.0 * np.exp(-t * 30.0)
    phase = 2.0 * np.pi * np.cumsum(freq) / SR
    x = np.sin(phase) * np.exp(-t * 7.5)
    x += 0.28 * np.sin(2.0 * phase) * np.exp(-t * 14.0)
    x += 0.10 * RNG.normal(0.0, 1.0, n) * np.exp(-t * 110.0)
    return np.tanh(1.15 * x)


def hat(dur=0.055, decay=0.014):
    n = int(dur * SR)
    x = np.diff(RNG.normal(0.0, 1.0, n), prepend=0.0)
    x *= np.exp(-np.arange(n) / (decay * SR))
    return x


def clap(dur=0.26):
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = np.diff(RNG.normal(0.0, 1.0, n), prepend=0.0)
    env = np.exp(-t * 16.0)
    for offset in (0.0, 0.011, 0.023):
        i = int(offset * SR)
        if i < n:
            env[i:] += np.exp(-t[: n - i] * 30.0) * 0.55
    return noise * env


def impact(dur=1.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    freq = 34.0 + 70.0 * np.exp(-t * 2.2)
    sub = np.sin(2.0 * np.pi * np.cumsum(freq) / SR) * np.exp(-t * 2.6)
    noise = np.diff(RNG.normal(0.0, 1.0, n), prepend=0.0) * np.exp(-t * 10.0)
    return sub * 0.95 + noise * 0.22


def riser(dur, f0=160.0, f1=1400.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    freq = f0 * (f1 / f0) ** (t / max(dur, 1e-6))
    tone = 0.35 * np.sin(2.0 * np.pi * np.cumsum(freq) / SR)
    noise = np.diff(RNG.normal(0.0, 1.0, n), prepend=0.0) * 0.5
    env = (t / max(dur, 1e-6)) ** 2
    return (tone + noise) * env


# ---------------------------------------------------------------- effects
def pingpong(x, delay, feedback=0.4, taps=4, wet=0.45):
    out = np.zeros_like(x)
    d = int(delay * SR)
    for k in range(1, taps + 1):
        shift = k * d
        if shift >= len(x):
            break
        g = wet * (feedback ** (k - 1))
        seg = x[: len(x) - shift] * g
        if k % 2 == 1:
            out[shift:, 0] += seg[:, 0] * 0.68
            out[shift:, 1] += seg[:, 1] * 0.32
        else:
            out[shift:, 0] += seg[:, 0] * 0.32
            out[shift:, 1] += seg[:, 1] * 0.68
    return x + out


def make_ir(seconds=1.15, decay=2.8):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = RNG.normal(0.0, 1.0, n) * np.exp(-t * decay)
    ir = np.convolve(ir, np.ones(10) / 10.0, mode="same")
    for tap, gain in ((0.013, 0.6), (0.027, 0.42), (0.043, 0.28), (0.061, 0.2), (0.089, 0.14)):
        i = int(tap * SR)
        if i < n:
            ir[i] += gain
    ir /= np.sqrt(np.sum(ir * ir)) + 1e-9
    return ir


def reverb(send, ir_l, ir_r, wet=1.0):
    n = len(send) + len(ir_l) - 1
    nfft = 1 << (n - 1).bit_length()
    out = np.zeros_like(send)
    for ch, ir in ((0, ir_l), (1, ir_r)):
        spec = np.fft.rfft(send[:, ch], nfft) * np.fft.rfft(ir, nfft)
        out[:, ch] = np.fft.irfft(spec, nfft)[: len(send)]
    return out * wet


def make_duck(total, kick_times, depth=0.3, decay=0.16):
    duck = np.ones(total)
    for when in kick_times:
        i = int(when * SR)
        if i >= total:
            continue
        n = min(total - i, int(0.5 * SR))
        t = np.arange(n) / SR
        env = 1.0 - depth * np.exp(-t / decay)
        duck[i:i + n] = np.minimum(duck[i:i + n], env)
    return duck


def spectral_highpass(x, cutoff, order=1):
    """Zero-phase FFT highpass, used to clean low mud from bus mixes."""
    n = len(x)
    nfft = 1 << (n - 1).bit_length()
    spec = np.fft.rfft(x, nfft, axis=0)
    freqs = np.fft.rfftfreq(nfft, 1.0 / SR)
    h = 1.0 / np.sqrt(1.0 + (cutoff / np.maximum(freqs, 1e-9)) ** (2 * order))
    y = np.fft.irfft(spec * h[:, None], nfft, axis=0)[:n]
    return y


def finalize(bus, peak=0.92, fade_in=0.0, fade_out=0.0):
    out = bus.copy()
    n = len(out)
    if fade_in > 0:
        k = min(n, int(fade_in * SR))
        out[:k] *= np.linspace(0.0, 1.0, k)[:, None]
    if fade_out > 0:
        k = min(n, int(fade_out * SR))
        out[-k:] *= np.linspace(1.0, 0.0, k)[:, None]
    out -= np.mean(out, axis=0, keepdims=True)
    peak_now = np.max(np.abs(out))
    if peak_now > 0:
        out *= peak / peak_now
    return np.clip(out, -1.0, 1.0)


# ---------------------------------------------------------------- menu theme
def make_menu():
    bpm = 90.0
    beat = 60.0 / bpm
    bar = 4.0 * beat
    bars = 8
    loop_n = int(round(bars * bar * SR))
    tail = int(2.5 * SR)
    total = loop_n + tail

    pad_bus = np.zeros((total, 2))
    arp_bus = np.zeros((total, 2))
    bass_bus = np.zeros((total, 2))
    drum_bus = np.zeros((total, 2))
    fx_bus = np.zeros((total, 2))

    chords = [
        ([57, 60, 64], 33),   # Am  (A3 C4 E4) / A1
        ([53, 57, 60], 29),   # F   (F3 A3 C4) / F1
        ([60, 64, 67], 36),   # C   (C4 E4 G4) / C2
        ([55, 59, 62], 31),   # G   (G3 B3 D4) / G1
    ]

    # pads: two bars per chord
    for ci, (tones, _root) in enumerate(chords):
        start = ci * 2 * bar
        for j, note in enumerate(tones):
            pan = (-0.5, 0.0, 0.5)[j % 3]
            sig = pad(m2f(note), 2 * bar + 2.4, attack=1.1, release=2.4, bright=0.65)
            add(pad_bus, sig, start, 0.34, pan)
            # quiet octave layer: adds presence without mud
            add(pad_bus, pad(m2f(note + 12), 2 * bar + 1.6, attack=1.2, release=1.8, bright=0.5),
                start, 0.13, pan * 0.7)
            # high shimmer chord tones
            add(pad_bus, shimmer(m2f(note + 24), 2 * bar + 2.0), start, 0.05, pan * 1.2)
            add(pad_bus, shimmer(m2f(note + 36), 2 * bar + 1.6), start, 0.03, -pan)

    # airy high drone + background air
    add(pad_bus, pad(m2f(81), (loop_n + tail) / SR, attack=3.0, release=3.0, bright=0.25), 0, 0.12, 0.65)
    add(fx_bus, air((loop_n + tail) / SR, 0.010), 0, 1.0, 0.0)

    # bass: two hits per bar
    for ci, (_tones, root) in enumerate(chords):
        start = ci * 2 * bar
        for b in range(2):
            for bt in (0, 2):
                add(bass_bus, bass(m2f(root), 1.35 * beat), start + b * bar + bt * beat, 0.52)

    # arpeggio, 16th notes
    pattern = [0, 1, 2, 1, 2, 0, 1, 2]
    for bar_i in range(bars):
        tones = chords[bar_i // 2][0]
        for step in range(16):
            when = bar_i * bar + step * (bar / 16.0)
            note = tones[pattern[step % 8]] + 12
            vel = (0.95, 0.72, 1.0, 0.78)[step % 4]
            add(arp_bus, pluck(m2f(note), 0.55), when, 0.52 * vel,
                pan=(-0.35 if step % 2 == 0 else 0.35))
            add(arp_bus, pluck(m2f(note + 12), 0.45), when, 0.18 * vel,
                pan=(0.35 if step % 2 == 0 else -0.35))
            add(arp_bus, pluck(m2f(note + 24), 0.35), when, 0.08 * vel,
                pan=(-0.5 if step % 2 == 0 else 0.5))

    # sparse lead melody (A minor pentatonic-ish)
    lead_notes = [76, 74, 72, 69, 72, 74, 76, 79]
    for i, note in enumerate(lead_notes):
        add(arp_bus, lead(m2f(note), bar * 0.85, attack=0.22, release=0.9),
            i * bar, 0.20, pan=(-0.22 if i % 2 else 0.22))

    # delay on arp
    arp_bus = pingpong(arp_bus, delay=beat / 2.0, feedback=0.38, taps=4, wet=0.5)

    # kick + hats
    kick_times = []
    for bar_i in range(bars):
        for bt in (0, 2):
            when = bar_i * bar + bt * beat
            kick_times.append(when)
            add(drum_bus, kick(), when, 0.62)
        for step in range(16):
            when = bar_i * bar + step * (bar / 16.0)
            if step % 8 == 2:
                add(drum_bus, hat(), when, 0.52, pan=0.45)
            elif step % 4 == 0:
                add(drum_bus, hat(dur=0.04), when, 0.14, pan=-0.35)
            elif step % 2 == 1:
                add(drum_bus, hat(dur=0.035), when, 0.10, pan=0.3)

    # gentle sidechain pump on pads / arp
    duck = make_duck(total, kick_times, depth=0.28, decay=0.16)
    pad_bus *= duck[:, None]
    arp_bus *= duck[:, None]

    # seat the pads/arp in the mix: remove sub mud, keep bass bus for lows
    pad_bus = spectral_highpass(pad_bus, 150)
    arp_bus = spectral_highpass(arp_bus, 120)

    ir_l = make_ir(1.15, 2.8)
    ir_r = make_ir(1.15, 2.8)
    send = pad_bus * 0.85 + arp_bus * 0.8 + fx_bus
    wet = reverb(send, ir_l, ir_r, wet=1.0)

    mix = pad_bus + arp_bus + bass_bus * 1.0 + drum_bus + wet * 0.34

    # fold the reverb/delay tail back into the loop start for a seamless loop
    out = mix[:loop_n].copy()
    out[:tail] += mix[loop_n:loop_n + tail]

    out = finalize(out, peak=0.9)
    return out


# ---------------------------------------------------------------- results theme
def make_results():
    bpm = 100.0
    beat = 60.0 / bpm
    bar = 4.0 * beat
    bars = 4
    body_n = int(round(bars * bar * SR))
    tail = int(2.4 * SR)
    total = body_n + tail

    pad_bus = np.zeros((total, 2))
    arp_bus = np.zeros((total, 2))
    bass_bus = np.zeros((total, 2))
    drum_bus = np.zeros((total, 2))
    fx_bus = np.zeros((total, 2))

    chords = [
        ([57, 60, 64], 33),          # Am
        ([53, 57, 60], 29),          # F
        ([60, 64, 67], 36),          # C
        ([57, 61, 64, 71], 33),      # A add9 (final)
    ]

    # pads, one bar each, longer on the final chord
    for ci, (tones, _root) in enumerate(chords):
        start = ci * bar
        dur = (bar + 2.0) if ci == 3 else (bar + 1.0)
        for j, note in enumerate(tones):
            pan = (-0.55, 0.15, 0.55, -0.2)[j % 4]
            add(pad_bus, pad(m2f(note), dur, attack=0.18, release=1.6, bright=0.9),
                start, 0.5, pan)
            add(pad_bus, pad(m2f(note + 12), dur, attack=0.18, release=1.4, bright=0.5),
                start, 0.09, -pan)
            add(pad_bus, shimmer(m2f(note + 24), dur, attack=0.4, release=1.2), start, 0.05, pan)
    add(fx_bus, air((body_n + tail) / SR, 0.012), 0, 1.0, 0.0)

    # bass: driving 8th pattern, root only
    for ci, (_tones, root) in enumerate(chords):
        start = ci * bar
        for step in range(8):
            when = start + step * (beat / 2.0)
            dur = 0.48 * beat
            add(bass_bus, bass(m2f(root), dur), when, 0.55)

    # arpeggio: rising 16ths through each chord + one octave
    for ci, (tones, _root) in enumerate(chords):
        start = ci * bar
        pool = tones + [t + 12 for t in tones]
        for step in range(16):
            when = start + step * (bar / 16.0)
            note = pool[(step * 3) % len(pool)]
            add(arp_bus, pluck(m2f(note), 0.5), when, 0.5 * (0.85 + 0.15 * (step % 2)),
                pan=(0.4 if step % 2 else -0.4))
            add(arp_bus, pluck(m2f(note + 12), 0.4), when, 0.16 * (0.85 + 0.15 * (step % 2)),
                pan=(-0.4 if step % 2 else 0.4))
        # final bar gets shimmering bells instead of busy arp
        if ci == 3:
            break

    # mid-range lead motif over the driving section
    for i, note in enumerate([76, 81, 84]):
        add(arp_bus, lead(m2f(note), bar * 0.8, attack=0.06, release=0.5),
            bar + i * beat, 0.18, pan=(-0.2 if i % 2 else 0.2))

    arp_bus = pingpong(arp_bus, delay=beat / 2.0, feedback=0.34, taps=3, wet=0.4)

    # drums: four-on-floor + claps for bars 1-2, stop before final chord
    kick_times = []
    for ci in range(3):
        start = ci * bar
        for bt in range(4):
            when = start + bt * beat
            # leave space at the end of bar 3 for the final impact
            if ci == 2 and bt > 1:
                continue
            kick_times.append(when)
            add(drum_bus, kick(), when, 0.7)
        if ci >= 1:
            for bt in (1, 3):
                add(drum_bus, clap(), start + bt * beat, 0.42, pan=-0.08)
        for step in range(16):
            when = start + step * (bar / 16.0)
            if ci == 2:
                break
            add(drum_bus, hat(), when, 0.28 if step % 2 == 0 else 0.16,
                pan=(0.4 if step % 4 == 0 else -0.4))

    # risers into bar 2 and into the final chord
    add(fx_bus, riser(bar, 140.0, 1200.0), bar, 0.55)
    add(fx_bus, riser(bar, 200.0, 1800.0), 2 * bar, 0.75)

    # impact + final chord at bar 4
    final_time = 3 * bar
    add(drum_bus, impact(1.8), 0.0, 0.42)
    add(drum_bus, impact(1.8), final_time, 0.72)
    for j, note in enumerate([81, 85, 88, 93]):  # A5 C#6 E6 A6 bells
        add(arp_bus, bell(m2f(note), 2.2), final_time + j * 0.055, 0.75, pan=(-0.5 + j * 0.33))

    duck = make_duck(total, kick_times, depth=0.22, decay=0.18)
    pad_bus *= duck[:, None]
    arp_bus *= duck[:, None]

    pad_bus = spectral_highpass(pad_bus, 130)
    arp_bus = spectral_highpass(arp_bus, 100)

    ir_l = make_ir(1.35, 2.4)
    ir_r = make_ir(1.35, 2.4)
    send = pad_bus * 0.9 + arp_bus * 0.85 + fx_bus
    wet = reverb(send, ir_l, ir_r, wet=1.0)

    mix = pad_bus * 1.0 + arp_bus + bass_bus + drum_bus + wet * 0.4
    out = finalize(mix, peak=0.94, fade_out=1.6)
    return out


# ---------------------------------------------------------------- write
def write_wav(path, stereo):
    data = np.clip(stereo, -1.0, 1.0)
    pcm = (data * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def report(name, data):
    peak = float(np.max(np.abs(data)))
    rms = float(np.sqrt(np.mean(data ** 2)))
    dur = len(data) / SR
    print(f"{name}: {dur:.2f}s  peak={peak:.3f}  rms={rms:.4f}  "
          f"size={data.size * 2 / 1024 / 1024:.2f} MiB")


def main():
    menu = make_menu()
    results = make_results()
    write_wav(HERE / "menu.wav", menu)
    write_wav(HERE / "results.wav", results)
    report("menu.wav", menu)
    report("results.wav", results)


if __name__ == "__main__":
    main()
