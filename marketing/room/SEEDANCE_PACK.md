# FLOAT / Room: generated live-action inserts

Production brief for an optional "with people" cut. The 30-second CG film is complete without these shots. The inserts add the one thing the CG film lacks: a person whose problem FLOAT solves.

## Division of labour

| Owner | Shots | Why |
|---|---|---|
| **Blender (CG)** | Anything where FLOAT itself is the subject: pod, lens and indicator, fans, envelope, dock, fleet, end card | Product truth. Fan count, pod geometry, seams and scale must not drift between shots. |
| **Image-to-video model** | Human beats only: hands, a person in the room, reactions | CG people would look worse than no people. |

Every insert starts from a **plate**: a frame of the CG film rendered with the same set, light, lens and product (`source/plates.py`; committed as JPEGs in `plates/stills/`). The model animates a person *into* that frame. Where the model supports first- and last-frame conditioning, supply both plates.

## General settings

- **Input:** plate image as the first frame. Use the matching `_end` plate as the last frame where provided and supported.
- **Output:** 1080p, 16:9, 24 fps if offered (otherwise 24/25/30; the edit conforms to 24 fps). Generate the longest duration the model offers and trim; the action should finish within the first ~3 seconds.
- **Camera:** locked off or a very slow push, matching the plate. No orbit, no zoom, no handheld shake.
- **FLOAT:** must stay still or nearly still, with geometry unchanged. Do not describe FLOAT doing anything in the prompt beyond "remains hovering, unchanged".
- **No dialogue lip-sync:** people are seen from behind or in profile. Dialogue comes from the existing voice track.
- **No text, logos, UI or phone screens** in generated frames. The phone notification is a designed overlay, labelled as simulated.

**Shared negative prompt:** `morphing, melting, extra propellers, extra fans, changing shape, deformed sphere, balloon popping, string, tether, cartoon, toy, text, captions, watermark, logo, extra fingers, distorted hands, face close-up, fast camera move, zoom, shaky camera, flicker`

## Inserts

### P1 · The ask (≈2 s, opens the film before S01)

- Plate: `P1_ask_start.jpg`
- Prompt: *Photorealistic interior, late-afternoon sun through tall black-framed windows. A person in a soft grey knit sweater walks into frame from the right foreground, seen from behind and slightly to the side, patting their jacket pockets and glancing around the living room as if looking for something. In the background, the mirrored silver sphere with a small dark camera pod beneath it remains hovering, unchanged, near the window. Static camera, natural motion, shallow depth of field, cinematic, 35mm film look.*
- Keep: person never faces camera; sphere does not move or change; sunlight patches on the wall stay put.
- Edit: cut to S01 (FLOAT turns) on the question "Float, have you seen my keys?".

### P2 · The pickup (≈2 s, after S07 "Found them")

- Plates: `P2_pickup_start.jpg` (keys between cushions), `P2_pickup_end.jpg` (keys gone)
- Prompt: *Close-up at seat level on a beige bouclé sofa. A hand enters from the bottom of frame, fingers slide into the gap between the seat cushions and lift out a ring of brass keys with a tan leather tag. Above and behind, out of focus, the hovering silver device with a glowing amber ring remains still. Static camera, shallow depth of field, warm natural light, photorealistic.*
- Keep: one hand with five fingers; keys stay brass with a tan tag; FLOAT unchanged.
- Edit: replaces the last ~1.5 s of S07 or extends it. Add a key-jingle effect in `score.py`.

### P3 · Thanks (≈2.5 s, between S08 and S09)

- Plate: `P3_thanks_start.jpg`
- Prompt: *Over-the-shoulder view from behind a person standing beside a sofa in a sunlit living room. The person steps into the left foreground holding up a ring of brass keys, gives a small relieved nod toward the hovering silver sphere at eye level in front of them. The sphere and its small dark pod with an amber ring remain hovering, unchanged. Static camera, shallow depth of field, photorealistic, warm late-afternoon light.*
- Keep: only shoulder, hair and hand visible; no face; FLOAT unchanged.
- Optional line (new voice take): "Thanks, Float." Generated with `voice.py` if added to `timeline.DIALOGUE`.

## Acceptance check per clip

Reject any take with:

- FLOAT moving, rotating, changing size, gaining or losing fans, or the pod changing shape or position;
- warped hands, extra fingers, or keys changing form;
- a visible face (avoids an identifiable or "real-looking" individual being taken as a real customer);
- text or UI;
- lighting that no longer matches the plate.

## Placing returned clips

1. Save the clips as `plates/wide/P1.mp4`, `plates/wide/P2.mp4` and `plates/wide/P3.mp4` (4:5 versions under `plates/feed/`).
2. Add the inserts to `source/timeline.py` and retime the affected shots. `finish.py` uses a clip in `plates/<format>/<SHOT>.mp4` in place of renders for that shot ID, conformed to 24 fps and the output frame size.
3. Re-run `score.py`, then `finish.py` and `master.py`.

The film keeps its on-screen "CGI concept · proposed experience" label and end-card disclosure. With photoreal people in it, that label matters more, not less. Generated people and settings must not be presented as customers, testimonials or real use. This cut is for social; crowdfunding pages need footage of the actual prototype.
