"""Compose the original 70-second demo score; refuses to overwrite a prior take."""
from pathlib import Path
import wave
import numpy as np

RATE, SECONDS = 48000, 70
track = np.zeros((RATE * SECONDS, 2), dtype=np.float64)
chords = [(48, 55, 60, 64), (45, 52, 57, 60), (41, 48, 53, 57), (43, 50, 55, 59)]
for beat in range(112):
    start = beat * .6
    chord = chords[(beat // 8) % len(chords)]
    midi = chord[beat % 4] + 12
    length = min(2.2, SECONDS - start)
    if length <= 0:
        break
    t = np.arange(round(length * RATE)) / RATE
    frequency = 440 * 2 ** ((midi - 69) / 12)
    envelope = (1 - np.exp(-t * 80)) * np.exp(-t * 2.8)
    note = (np.sin(2 * np.pi * frequency * t) + .22 * np.sin(4 * np.pi * frequency * t)) * envelope * .08
    offset = round(start * RATE)
    pan = .3 if beat % 2 else .7
    track[offset:offset + len(note), 0] += note * np.sqrt(pan)
    track[offset:offset + len(note), 1] += note * np.sqrt(1 - pan)
for bar in range(9):
    start = bar * 7.2
    length = min(8, SECONDS - start)
    if length <= 0:
        break
    t = np.arange(round(length * RATE)) / RATE
    envelope = np.sin(np.linspace(0, np.pi, len(t))) ** 2
    chord = sum(np.sin(2 * np.pi * 440 * 2 ** ((m - 69) / 12) * t) for m in chords[bar % 4])
    offset = round(start * RATE)
    track[offset:offset + len(t)] += (chord * envelope * .009)[:, None]
track[:RATE] *= np.linspace(0, 1, RATE)[:, None]
track[-3 * RATE:] *= np.linspace(1, 0, 3 * RATE)[:, None]
assert np.isfinite(track).all() and .01 < np.max(np.abs(track)) < .8
path = Path(__file__).with_name('music.wav')
with path.open('xb') as stream, wave.open(stream, 'wb') as wav:
    wav.setparams((2, 2, RATE, 0, 'NONE', 'not compressed'))
    wav.writeframes((track * 32767).astype('<i2').tobytes())
print(path)
