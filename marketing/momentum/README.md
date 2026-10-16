# FLOAT / Momentum

A 24-second, 16-shot product-concept film with a new 140 BPM score, new camera choreography, synchronized sound effects, and independently framed landscape and 4:5 feed versions.

## What changed

The opening is an immediate lens/rotor/foil montage. The product reveal uses a rapid pull-back and orbit, followed by a low-angle flyby, a tighter camera-pod pass, an overhead search move, a keys/phone match, and four different camera angles on a continuous docking/departure action. The closing beat resolves to a readable brand card. Faster camera travel and editorial cutting create the energy; no racing-drone performance is implied for the buoyant robot.

The balloon material was refined to remove the earlier latitude-band surface artifact. The scene uses real rendered 3D geometry, not animated still images. Select fast shots integrate two temporal samples for restrained motion blur. A VTK screen-space ambient-occlusion pass that produced large planar artifacts was removed before final rendering. Lighting, emissive accents, camera optics, and motion are illustrative, not physical engineering measurements.

## Deliverables

- Landscape: 1920 × 1080, 30 fps, 24 seconds, 720 frames.
- Feed: 1080 × 1350, 30 fps, 24 seconds, 720 frames. Independent camera framing and typography, not a center crop.
- Stereo AAC at 48 kHz; original synthesized music and sound design.
- JPEG cover frames.
- Source code, an edit decision list, editable WAV stems, and a portable GLB.

## Rebuild

Requires Python 3, ffmpeg on PATH, the packages in `source/requirements.txt`, VTK with functioning off-screen EGL rendering, and a locally installed Inter Display font family. Set `FLOAT_FONT_DIR` to the directory containing `InterDisplay-Medium.otf`, `InterDisplay-Bold.otf`, and `InterDisplay-Regular.otf`. **No font files are included.**

Run from this project root:

```sh
python source/score.py
python source/momentum.py --preview --format wide
python source/momentum.py --preview --format feed
python source/momentum.py --format wide --output wide_silent.mp4
python source/momentum.py --format feed --output feed_silent.mp4
python source/master.py
```

The master script waits for completed renders, normalizes audio, writes the final videos to the parent directory, exports covers, checks frame counts/dimensions/codecs/duration, and performs a full decode. The source WAV stems are pre-master levels; use their common gain relationships when remixing. The EDL expresses the beat-aligned edit. Source geometry is not manufacturing CAD.

## Publication boundary

This is a **CGI concept visualization, not footage of a functioning prototype**. Object finding, conversation, phone messages, docking, and fleet handoffs are proposed experiences. The video does not validate any mechanical design, acoustics, runtime, navigation, safety, manufacturability, delivery date, or physical performance. A concise concept label is present throughout, and the closing card identifies the development stage.

FLOAT is a working name. The model and original synthesis code are included; external runtime libraries retain their own licenses. No recorded third-party music, stock video, identifiable person, cloned voice, or font file is bundled.
