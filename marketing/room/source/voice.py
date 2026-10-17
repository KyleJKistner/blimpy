"""Synthesize the three spoken lines with Kokoro-82M (Apache-2.0 open TTS).

Uses stock Kokoro voices; no voice cloning and no recording of a real person.
Writes dry 48 kHz mono WAVs plus timing.json (duration and a 24 fps loudness
envelope that drives FLOAT's amber indicator in render.py).

Requires a Python environment with `kokoro`, `soundfile`, `scipy` and espeak-ng.
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

sys.path.insert(0, str(Path(__file__).resolve().parent))
import timeline as T  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'voice'
VOICES = {'person': ('am_michael', 1.02), 'float': ('af_heart', 0.96), 'grandma': ('bf_emma', 0.92)}
SR_IN, SR_OUT = 24000, 48000


def trim(x, thresh_db=-45, pad_s=.03):
    level = 20 * np.log10(np.abs(x) + 1e-9)
    idx = np.where(level > thresh_db)[0]
    if not len(idx):
        return x
    pad = int(pad_s * SR_IN)
    return x[max(0, idx[0] - pad):idx[-1] + pad]


def envelope(x, sr, fps):
    hop = sr // fps
    frames = int(np.ceil(len(x) / hop))
    rms = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(frames)])
    rms = rms / max(rms.max(), 1e-9)
    # Fast attack, slower release so the light reads as speech, not flicker.
    out, level = [], 0.0
    for v in rms:
        level = v if v > level else level * .72 + v * .28
        out.append(round(float(level), 4))
    return out


def main():
    from kokoro import KPipeline
    pipe = KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M')
    OUT.mkdir(parents=True, exist_ok=True)
    lines = []
    for d in T.DIALOGUE:
        voice, speed = VOICES[d['who']]
        chunks = [np.asarray(audio, np.float32) for _, _, audio in pipe(d['text'], voice=voice, speed=speed)]
        x = trim(np.concatenate(chunks))
        y = resample_poly(x, SR_OUT, SR_IN).astype(np.float32)
        y *= .5 / max(np.abs(y).max(), 1e-6)
        sf.write(OUT / f"{d['id']}.wav", y, SR_OUT, subtype='PCM_24')
        dur = len(y) / SR_OUT
        lines.append(dict(id=d['id'], who=d['who'], text=d['text'], voice=voice, speed=speed,
                          start_s=d['start_s'], duration_s=round(dur, 3), fps=T.FPS,
                          envelope=envelope(y, SR_OUT, T.FPS)))
        print(f"{d['id']}: {voice} {dur:.2f}s  '{d['text']}'", flush=True)
    meta = dict(model='hexgrad/Kokoro-82M', license='Apache-2.0', sample_rate=SR_OUT,
                note='Stock synthetic voices; no cloned or recorded human voice.', lines=lines)
    (OUT / 'timing.json').write_text(json.dumps(meta, indent=1))


if __name__ == '__main__':
    main()
