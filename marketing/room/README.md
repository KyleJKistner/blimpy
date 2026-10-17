# FLOAT / Room

A 40-second launch film for FLOAT: one day with it, rebuilt from scratch in Blender Cycles. It has a path-traced apartment lit from morning to night, a refined product model, an original score, nine short synthetic voice lines, and finishing in Python. Formats are 16:9 for X and web, and 4:5 for feeds.

**Status:**
- **Verified here:** source, low-resolution preview stills and a 480×270 CPU animatic.
- **Not yet done:** the full-quality frames. They need a GPU; see [Rendering](#rendering).
- **Audio:** checked by measurement and speech-to-text only. A person still needs to listen to it.

## Why a rebuild

*Momentum* (`../momentum`) answered "more kinetic" with 16 shots in 24 seconds, camera roll, a 140 BPM score and a one-word title card per shot. Rendering its own source shows the underlying problem: speed was never the issue.

- **No world.** 12 of 16 shots are a grey sphere on a black void. With no room to reflect, the VTK render gives a dull grey ball instead of a mirror.
- **No story.** "WAKE. MOVE. FLOAT. SEES. LISTENS. ANSWERS. FOUND. DOCK." are labels, not things anyone needs done.
- **Product read.** Spoked fan guards looked like bicycle wheels; the pod looked like an old projector.
- **Speed against the product.** A slow buoyant robot cut like a racing-drone ad works against itself.

*Room* is built around one claim: FLOAT is an AI that can **go and look**. Every beat shows something an assistant in a phone or a speaker cannot do.

- **A real space.** The metallized envelope mirrors a warm apartment. That reflection is the product's most striking visual property.
- **Breadth, made legible with the sound off.** Five concrete uses in one day, each with a spoken line, a caption and a small feature label:
  - finds the keys (its camera view);
  - checks the stove for you while you're out (remote live view);
  - notices the olive tree needs water;
  - stays with you in the kitchen;
  - brings Grandma into the room on a call.
- **The differentiator.** The shared dock gets a payoff at night: the day unit docks, a charged one lifts off.
- **Kinetic contrast.** Energy comes from cutting on the beat, a drop on the title, macro details, parallax and a lighting arc from morning to night. FLOAT itself never exceeds roughly 0.35 m/s or 45°/s.
- **Restrained type.** Three title moments, feature labels, captions and an end card.

## Edit (40 s, 24 fps, 120 BPM, one beat = 12 frames)

| Shot | Time | Light | Content | Copy / sound |
|---|---|---|---|---|
| S01 The ask | 0.0–2.5 | morning | FLOAT by the window turns toward a voice; indicator wakes. | "Float, have you seen my keys?" |
| S02 Listening | 2.5–3.5 | morning | 85 mm on the pod. | FLOAT: "Let me look." |
| S03 Search view | 3.5–5.0 | morning | Simulated camera view locks on the keys. | label *Finds what you lost* |
| S04 Found | 5.0–7.0 | morning | Seat-level rack focus to the keys. | FLOAT: "Found them. Between the cushions." |
| S05–S06 | 7.0–8.0 | morning | Fan spin-up macro; low three-quarter as it sets off. | Riser, fill |
| S07 Meet FLOAT | 8.0–12.0 | morning | Low tracking shot through the sun. | **Meet FLOAT.** / A floating AI companion. (drop) |
| S08 From anywhere | 12.0–13.5 | (app) | Simulated app: "Did I leave the stove on?" | label *Checks in while you're out* |
| S09 Into the kitchen | 13.5–15.0 | midday | FLOAT crosses to the kitchen. | |
| S10 Live view | 15.0–17.0 | midday | Simulated live view; each knob reads OFF. | FLOAT: "All four burners are off." |
| S11 Notices | 17.0–20.0 | golden | Beside the olive tree; note "Last watered 9 days ago". | FLOAT: "Your olive tree looks thirsty." |
| S12 Cooking | 20.0–22.0 | evening | At the stove with the under-shelf lights on. | "What's next?" |
| S13 Next step | 22.0–24.0 | evening | Pod over the sizzling pan; simmer timer. | FLOAT: "Two cloves of garlic. I'll time the simmer." |
| S14 The call | 24.0–27.0 | evening | Over a child's crayon drawing; call indicator. | Grandma, via FLOAT: "Did you draw that? It's beautiful!" |
| S15 Shift change | 27.0–31.0 | night | The day unit docks; a charged one lifts off. | **One rests. / Another takes over.** |
| S16 Lift | 31.0–33.0 | night | Low angle as it rises. | Build |
| S17 In the room | 33.0–36.0 | night | Backlit by the night window. | **Not on a screen. / In the room.** |
| S18 End card | 36.0–40.0 | night | Wordmark on a bell per letter, call to action, disclosure. | Logo hit |

Exact frames are in `source/edit_decision_list.csv`. Shot timing, dialogue, copy and interface text live in `source/timeline.py`.

## Source

| File | Runs in | Role |
|---|---|---|
| `source/timeline.py` | anywhere | Shots, time of day, dialogue, copy, feature labels, interface text. Single source of timing. |
| `source/textures.py` | Python | Procedural wood, plaster, fabric, tile, rug, artwork, window view, crayon drawing and recipe page. |
| `source/scene.py` | Blender 4.5 | Set (living room, kitchen, dock), FLOAT model, practical lamps, time-of-day lighting, Cycles configuration. |
| `source/shots.py` | Blender | Per-shot performances (FLOAT motion, indicator, rotors, burner) and the 17 rendered cameras. |
| `source/render.py` | Blender | Renders frames per quality preset; resumable; `--shard i/n`; writes overlay tracks. |
| `source/voice.py` | Python + Kokoro | Generates the nine lines and indicator envelopes (`assets/voice/`, committed). |
| `source/score.py` | Python | Original score, sound design and dialogue mix (stems in `assets/audio/`). |
| `source/finish.py` | Python | Grade, camera-view treatment, typography, app screen, live view, timer, call and plant notes, end card, plate substitution. |
| `source/master.py` | Python | Two-pass loudness (−14 LUFS, −1 dBTP), mux, SRT captions, cover, contact sheet, QA record. |
| `source/plates.py` | Blender | Start/end plates for generated live-action inserts ([SEEDANCE_PACK.md](SEEDANCE_PACK.md)). |
| `render_gpu.sh` | GPU host | One-command full render, finish and master. |

## Rendering

### Previews and animatic (any CPU)

Download Blender 4.5 LTS. Install `source/requirements.txt` in a Python 3 environment and make sure `ffmpeg` is available. Then, from this folder:

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

A 4-core CPU needs several minutes per 1080p frame for this interior, so finals run on a rented GPU. The recommended host is an RTX 4090 GPU pod on RunPod, Vast.ai or Lambda, with any Ubuntu + CUDA image and about 100 GB of disk. Then:

```sh
git clone -b claude/practical-johnson-6qm853 https://github.com/KyleJKistner/blimpy.git
cd blimpy/marketing/room && bash render_gpu.sh            # both formats
```

The script fetches Blender 4.5.14 and Inter (SIL Open Font License) into `.cache/`, renders 96-sample frames with OptiX (adaptive sampling plus OpenImageDenoise, 16-bit PNG, motion blur), and runs finishing and mastering. Results land in `deliverables/`. There are 912 rendered frames per format; the app screen is pure graphics.

- **Measured:** on this repository's 4-vCPU build container, final-setting 1080p frames at 48 samples took 437–641 s each. They were already clean after denoising.
- **Estimated, not measured:** public Cycles benchmarks put an RTX 4090 at roughly 50–80× such a CPU. That suggests about 10–25 s per frame at 96 samples, or 2.5–6.5 hours per format on one GPU.
- **Speeding it up:** a pod with two or four GPUs is used automatically in one process. To split frames across separate machines, use `SHARD=i/n`, as described in the script header.
- **GPU choice:** pick GPUs with ray-tracing cores (RTX 4090, RTX 5090, L40S). A100 and H100 have none and are a poor fit for Cycles.
- **Haze:** sun-beam haze is off by default (`--haze on` enables it on S01, S07 and S11). In tests it read as a milky lift rather than visible beams, at roughly 30–40% more render time.

### Fonts, music and voices

- **Fonts:** none are committed. Set `FLOAT_FONT_DIR` to a folder containing the Inter Display OTFs (Regular, Medium, SemiBold).
- **Music:** `python source/score.py --music track.wav` replaces the synthesized score with a supplied (for example licensed) track, gain-matched and ducked under dialogue; sound design and dialogue are kept.
- **Voices:** the voice WAVs are committed so the GPU host needs no ML stack. To regenerate them, use Python 3.12 with `kokoro`, `soundfile`, `scipy`, espeak-ng and the spaCy `en_core_web_sm` model.

## What was checked

- **Preview stills:** every shot, at 640×360 and 24 samples, in 16:9. Every overlay (captions, feature labels, titles, app screen, camera and live views, plant note, timer, call indicator, end card) was checked on composited stills.
- **Animatic:** 480×270, 16 samples, no motion blur, used for timing, camera motion and the edit, not image quality. The `master.py` result is recorded in `deliverables/*_animatic_qa.json`.
- **1080p test frames:** two frames rendered with final settings on CPU at 48 samples, to check motion blur, denoising and the final render path.
- **Voice:** each line was transcribed back by Whisper `small.en`; all nine match the script.
- **Score:** levels were measured per stem and per line. Dialogue sits 8–22 dB above the bed while lines play. **Not yet listened to by a person.**
- **Master:** `master.py` asserts dimensions, 24 fps, frame count, duration, BT.709, 48 kHz stereo, a full decode, −14 ± 1 LUFS and true peak ≤ −0.5 dBTP, and writes a QA JSON.

## Publication boundary

This is a **CGI concept visualization of a proposed product, not footage of a working prototype**. Object finding, the camera and live views, remote check-ins from the app, noticing the plant, cooking help, calls through FLOAT, docking and fleet handoff are all proposed experiences.

- **Labelling:** a "CGI concept · proposed experience" label is burned into every frame before the end card, and the end card states the disclosure in full. Every interface element is labelled simulated.
- **Claims:** no runtime, speed, noise level, battery, price, availability or crowdfunding claim is made.
- **Model:** the product model follows the engineering concept lock (about 62 cm envelope, twelve gores, four guarded fans, camera/audio pod, three-bay dock). It is illustrative, not manufacturing CAD.
- **Licensing:** the score is original synthesis with no samples. The voices are stock Kokoro-82M voices (Apache-2.0), with no cloned or recorded person. Textures are procedural.
- **Kickstarter:** hardware campaigns need real prototype footage. Use this film for social; it is not a substitute for a working prototype.
