# FLOAT / Presence — launch teaser rebuild

## Deliverables
- Main film: 30 seconds, native 1920×1080, 24 fps, H.264, AAC stereo.
- Feed cut: 15 seconds, native 1080×1080, independently reframed and typeset.
- Cover image and editable procedural source.

These are original CGI concept visualizations. They are NOT recordings of a working prototype. Object finding, phone messaging and fleet docking are proposed interactions, not demonstrated engineering capabilities. The product design, motion, materials, lighting and sound effects are illustrative. No runtime, manufacturing, acoustic, safety, or shipping claim is made. FLOAT is a working name; no trademark clearance has been performed.

## Creative direction
Graphite and warm ivory; restrained amber interaction accents. Camera-detail opening, complete-product reveal, object-finding vignette, simulated phone notification, fleet handoff, and a development-stage call to action. Readable on-screen text carries the story with sound off. The sound-on mix uses an original synthesized 96bpm score and designed interaction sounds. There is no synthetic human voice or borrowed footage.

## Rebuild
Requires Python, NumPy, Pillow, SciPy, VTK with off-screen EGL support, and ffmpeg. The scripts expect the InterDisplay OpenType family to be locally installed; set FLOAT_FONT_DIR as needed. FONT FILES ARE NOT INCLUDED.

Place source/, assets/, renders/, previews/, deliverables/ under one project directory.

```sh
python source/launch_film.py --preview
python source/launch_film.py --audio
python source/launch_film.py --width 1920 --output main_silent.mp4
python source/social_cut.py --preview
python source/social_cut.py
python source/finalize.py
```

The composition uses explicit scene dimensions, perspective cameras, physically based material parameters and generated studio environment lighting. Lens blur and ambient occlusion are visual effects, not physical measurements. It is real rendered 3D motion, not a sequence of animated still images. It is not a path-traced live-action substitute.

The score and geometric models are generated in the supplied code. No stock music or downloaded footage is used. Standard third-party runtime libraries remain subject to their respective licenses and are not bundled.

## Publication boundary
Use as a transparently labeled early-concept social teaser. Do not present the imagery as a finished product or as functional prototype evidence. Kickstarter states that hardware projects need working prototypes and that realistic renderings cannot replace them. The campaign should document the actual device and its current capabilities before making manufacturing or performance promises.

Official guidance consulted:
https://updates.kickstarter.com/how-to-launch-a-product-on-kickstarter-part-1-creating-your-prototype-and-manufacturing-plan/
https://www.kickstarter.com/blog/2324

## Version notes
The rebuild uses a new model, edit, lighting, framing, set, typography and score. It does not reuse the previous 28-second video frames or its soundtrack. The original engineering design remains unvalidated by this animation.
