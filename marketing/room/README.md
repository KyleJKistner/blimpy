# FLOAT / Room

A 30-second launch film for FLOAT, rebuilt from scratch in Blender Cycles: a path-traced, sunlit apartment, a refined product model, an original score, two synthetic voice lines, and finishing in Python. Formats are 16:9 for X and web, and 4:5 for feeds.

**Status:**
- **Verified here:** source, low-resolution preview stills and a 480×270 CPU animatic.
- **Not yet done:** the full-quality frames. They need a GPU; see [Rendering](#rendering).
- **Audio:** checked by measurement and speech-to-text only. A person still needs to listen to it.

## Why a rebuild

*Momentum* (`../momentum`) answered "more kinetic" with 16 shots in 24 seconds, camera roll, a 140 BPM score and a one-word title card per shot. Rendering its own source shows the underlying problem: speed was never the issue.

- **No world.** 12 of 16 shots are a grey sphere on a black void. VTK's material model gives a dull grey ball rather than a mirror, because there is no room for it to reflect.
- **No story.** "WAKE. MOVE. FLOAT. SEES. LISTENS. ANSWERS. FOUND. DOCK." are labels, not a use case anyone feels.
- **Product read.** Spoked fan guards looked like bicycle wheels; the pod looked like an old projector.
- **Speed against the product.** A slow buoyant robot cut like a racing-drone ad works against itself.

*Room* keeps the facts and fixes the craft:

- **A real space.** The metallized envelope is now a mirror of a warm, sunlit room. That reflection is the product's most striking visual property.
- **One relatable use case, told end to end, legible with the sound off.** The film runs ask → look → search (FLOAT's simulated camera view) → found (rack focus, spoken answer) → simulated phone notification.
- **The differentiator.** The shared dock gets a payoff: one unit docks, another lifts off.
- **Kinetic contrast.** Energy comes from cutting on the beat, macro details, a drop on the title, low tracking shots and parallax. FLOAT itself never exceeds roughly 0.35 m/s or 45°/s.
- **A voice.** It is a conversational companion, so it speaks: two short lines, captioned.
- **Restrained type.** Three title moments, dialogue captions and an end card. No word per shot.

## Edit (24 fps, 120 BPM, one beat = 12 frames)

| Shot | Time | Content | Copy / sound |
|---|---|---|---|
| S01 The ask | 0.0–3.0 | Wide, golden hour. FLOAT hovers by the window and turns toward the speaker; its indicator wakes. | "Float, have you seen my keys?" (off-screen) |
| S02 Listening | 3.0–5.0 | 85 mm on the pod: lens and amber ring. | FLOAT: "Let me look." |
| S03 Spin-up | 5.0–6.0 | Macro: guarded fan starts on the beat. | Riser, fan spin-up |
| S04 Set off | 6.0–7.0 | Low three-quarter; the room curves across the envelope. | Fill into the drop |
| S05 Meet FLOAT | 7.0–11.0 | Low tracking shot through the sun, counter-moving camera. | **Meet FLOAT.** / A floating AI companion. (drop) |
| S06 Point of view | 11.0–13.0 | FLOAT's camera view; brackets lock on the keys. | "Simulated" label, UI blips |
| S07 Found | 13.0–16.0 | Seat-level rack focus from FLOAT to the keys. | FLOAT: "Found them. They slipped between the cushions." |
| S08 On your phone | 16.0–18.0 | FLOAT over the sofa with the notification overlay. | "Keys found", labelled simulated |
| S09 Shift change | 18.0–22.0 | Three bays: FLOAT docks, another unit lifts off. | **One rests. / Another takes over.** |
| S10 Lift | 22.0–24.0 | Low angle as the fresh unit rises. | Build |
| S11 In the room | 24.0–27.0 | Backlit by the window. | **Not on a screen. / In the room.** |
| S12 End card | 27.0–30.0 | FLOAT wordmark on the bell motif, call to action, disclosure. | Logo hit |

Exact frames are in `source/edit_decision_list.csv`. Shot timing, dialogue and copy live in `source/timeline.py`.

## Source

| File | Runs in | Role |
|---|---|---|
| `source/timeline.py` | anywhere | Shots, dialogue, copy, notification text. Single source of timing. |
| `source/textures.py` | Python | Procedural oak, walnut, plaster, bouclé, rug, knit, artwork and window-view textures. |
| `source/scene.py` | Blender 4.5 | Set, FLOAT model, dock, lighting, Cycles configuration. |
| `source/shots.py` | Blender | Performances (FLOAT motion, indicator, rotors) and the 12 cameras. |
| `source/render.py` | Blender | Renders frames per quality preset; resumable; `--shard i/n`; writes overlay tracks. |
| `source/voice.py` | Python + Kokoro | Generates the three lines and an indicator envelope (`assets/voice/`, committed). |
| `source/score.py` | Python | Original score, sound design and dialogue mix (stems in `assets/audio/`). |
| `source/finish.py` | Python | Grade, POV treatment, typography, notification, end card, plate substitution. |
| `source/master.py` | Python | Two-pass loudness (−14 LUFS, −1 dBTP), mux, SRT captions, cover, contact sheet, QA record. |
| `source/plates.py` | Blender | Start/end plates for generated live-action inserts ([SEEDANCE_PACK.md](SEEDANCE_PACK.md)). |
| `render_gpu.sh` | GPU host | One-command full render, finish and master. |

## Rendering

### Previews and animatic (any CPU)

Download Blender 4.5 LTS. Install `source/requirements.txt` in a Python 3 environment (the virtual environment in the commands below) and make sure `ffmpeg` is available. Then, from this folder:

```sh
python source/textures.py
python source/score.py
blender -b --python source/render.py -- --quality preview              # one still per shot
blender -b --python source/render.py -- --quality animatic             # 480×270, ~5 s/frame on 4 cores
blender -b --python source/render.py -- --quality animatic --track-only
python source/finish.py --format wide --quality animatic
python source/master.py --format wide --quality animatic
```

### Final (NVIDIA GPU)

A 4-core CPU needs roughly two to three minutes per 1080p frame for this interior, so finals run on a rented GPU. The recommended host is an RTX 4090 GPU pod on RunPod, Vast.ai or Lambda, with any Ubuntu + CUDA image and about 80 GB of disk. Then:

```sh
git clone -b claude/practical-johnson-6qm853 https://github.com/KyleJKistner/blimpy.git
cd blimpy/marketing/room && bash render_gpu.sh            # both formats
```

The script fetches Blender 4.5.14 and Inter (SIL Open Font License) into `.cache/`, renders 96-sample frames with OptiX (adaptive sampling plus OpenImageDenoise, 16-bit PNG, motion blur), and runs finishing and mastering. Results land in `deliverables/`.

- **Measured:** on this repository's 4-vCPU build container, final-setting 1080p frames at 48 samples took 437–641 s each. They were already clean after denoising.
- **Estimated, not measured:** public Cycles benchmarks put an RTX 4090 at roughly 50–80× such a CPU. That suggests about 10–25 s per frame at 96 samples, or 2–5 hours per format on one GPU.
- **Speeding it up:** a pod with two or four GPUs is used automatically in one process. To split frames across separate machines, use `SHARD=i/n`, as described in the script header.
- **GPU choice:** pick GPUs with ray-tracing cores (RTX 4090, RTX 5090, L40S). A100 and H100 have none and are a poor fit for Cycles.
- **Haze:** sun-beam haze is off by default (`--haze on` enables it on S01, S05, S11 and S12). In tests it read as a milky lift rather than visible beams, at roughly 30–40% more render time.

### Fonts and voices

- **Fonts:** none are committed. Set `FLOAT_FONT_DIR` to a folder containing the Inter Display OTFs (Regular, Medium, SemiBold).
- **Music:** `python source/score.py --music track.wav` replaces the synthesized score with a supplied (for example licensed) track, gain-matched and ducked under dialogue; sound design and dialogue are kept.
- **Voices:** the voice WAVs are committed so the GPU host needs no ML stack. To regenerate them, use Python 3.12 with `kokoro`, `soundfile`, `scipy`, espeak-ng and the spaCy `en_core_web_sm` model.

## What was checked

- **Preview stills:** every shot, at 640×360 and 24 samples. Overlay layout (captions, titles, notification, POV brackets, end card) was checked on composited stills.
- **Animatic:** 480×270, 16 samples, no motion blur. Its job is to check timing, camera motion and the edit, not image quality. `master.py` QA passed on the animatic master (720 frames, 24 fps, −14.1 LUFS, −1.0 dBTP, full decode).
- **1080p test frames** (S05 and S09) rendered with final settings on CPU at 48 samples, to check motion blur, denoising and the final render path.
- **Voice:** each line was transcribed back by Whisper `small.en`; all three match the script word for word.
- **Score:** levels were measured per second and per stem. Dialogue sits 12–24 dB above the bed while lines play. The spectrogram matches the intended structure (intro, riser, drop at 7 s, breakdown at 13 s, groove at 18 s, logo hit at 27 s). **Not yet listened to by a person.**
- **Master:** `master.py` asserts dimensions, 24 fps, 720 frames, 30 s, BT.709, 48 kHz stereo, a full decode, −14 ± 1 LUFS and true peak ≤ −0.5 dBTP, and writes a QA JSON.

## Publication boundary

This is a **CGI concept visualization of a proposed product, not footage of a working prototype**. Object finding, the camera view, spoken answers, phone notifications, docking and fleet handoff are proposed experiences.

- **Labelling:** a "CGI concept · proposed experience" label is burned into every frame before the end card, and the end card states the disclosure in full.
- **Claims:** no runtime, speed, noise level, battery, price, availability or crowdfunding claim is made. The UI is labelled simulated.
- **Model:** the product model follows the engineering concept lock (about 62 cm envelope, twelve gores, four guarded fans, camera/audio pod, three-bay dock). It is illustrative, not manufacturing CAD.
- **Licensing:** the score is original synthesis with no samples. The voices are stock Kokoro-82M voices (Apache-2.0), with no cloned or recorded person. Textures are procedural.
- **Kickstarter:** hardware campaigns need real prototype footage. Use this film for social; it is not a substitute for a working prototype.
