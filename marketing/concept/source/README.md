# FLOAT — concept film 01

A 28-second, 16:9 animated product-concept film for a helium-supported AI companion.
**Working title only. This is not footage of a functioning prototype.**

## Editorial sequence

- 00:00–00:05 — Hero introduction; approximately 60 cm envelope shown.
- 00:05–00:10.5 — Slow indoor following, with a stylized adult for scale.
- 00:10.5–00:16.7 — Proposed visual object-finding interaction and phone notification.
- 00:16.7–00:23 — Proposed docking and fleet handover.
- 00:23–00:28 — Closing product shot.

## Scope

The robot is an illustrative approximately 62 cm spherical helium envelope, small camera/audio gondola, and four guarded propellers. Dimensions and movements are artistic, not a mechanical release or validation. The film does not claim demonstrated autonomy, battery life, payload capacity, charging speed, or consumer safety. The camera tilts in the finding scene as an illustrative gimbal, not an already validated part of the hardware BOM.

The soundtrack is procedurally composed from synthesized tones and noise in the included source. There is no voiceover. Spoken interactions appear as captions. No third-party footage, human likeness, or music recording is included.

## Build

The source uses Python, NumPy, Pillow, VTK 9.6.2 with off-screen EGL, and ffmpeg. Install equivalent dependencies in your environment. The Inter font is referenced from the system and is **not bundled**. Set `FONTP` to your local compatible font directory or change the font loader. Change `ROOT` to your output directory.

```sh
python make_film.py --previews
python make_film.py
```

The 3D scene renders at 1440 × 810, is resized to 1920 × 1080, and receives typography at output resolution. Final format: H.264, yuv420p, 24 fps, with AAC stereo audio. The source creates the complete scenes, animated character, product, motion, titles, and score. This is not a slide pan/zoom export.

## Deliverables

- `FLOAT_concept_film.mp4`: final 28-second video.
- `poster.jpg`: closing-shot still.
- `source/make_film.py`: editable procedural source.

