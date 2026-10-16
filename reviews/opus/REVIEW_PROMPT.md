# Independent creative-director review — FLOAT / Momentum

You are reviewing an existing product-concept film for the owner. Give an independent, critical review grounded in the supplied visual evidence and code. Do not simply agree with previous creative decisions. This package was prepared by ChatGPT; it contains no feedback from Claude or Opus. The user explicitly requested consultation with Opus 5.5. Report which model you actually are if known; never claim a model identity you cannot verify.

## Objective and user feedback

FLOAT is the working name for a small helium-supported conversational AI companion. The envisaged product has a camera, microphone, speaker, wireless connectivity and a shared charging dock. Finding objects, following people and fleet handoff are proposed experiences, not demonstrated capabilities. The current engineering concept is about 60–62 cm across, not palm-sized. It is slow and buoyant; do not suggest representing it as a fast, agile racing drone.

The user wants production value strong enough for a public Twitter/X launch and eventual crowdfunding communications. Their last two requests were:

“I need a lot more production value from this video. Way more. This needs to be fit for a Twitter release or a kickstarter campaign.”

“I think it still needs to be a bit more kinetic, hype, camera angles, etc”

They then requested your independent consultation. Assess whether the latest version actually answers those requests. Do not assume that more cuts, faster music, or more camera rotation automatically solve the underlying problem.

This is a CGI concept teaser, not a working-prototype demo. Preserve conspicuous concept labeling and do not introduce invented capabilities, battery-life promises, preorders, availability or crowdfunding eligibility. No need to turn the creative review into a legal essay.

## Evidence to inspect, in this order

1. `../../marketing/momentum/deliverables/FLOAT_Momentum_24s_1080p.mp4`: the actual 24-second landscape cut.
2. `../../marketing/momentum/deliverables/FLOAT_Momentum_24s_Feed.mp4`: the actual 4:5 feed cut, separately framed.
3. `../../marketing/momentum/previews/final_wide_sheet.jpg` and `final_feed_sheet.jpg`: existing shot overview images.
4. `motion_sheets/`: four sheets showing three sampled positions within each of the 16 landscape shots.
5. `frames/` and `frame_manifest.json`: 48 landscape stills and 16 feed stills, each mapped to the actual encoded frame index and timestamp. These supplement, not replace, playback.
6. `../../marketing/momentum/source/edit_decision_list.csv`: the current edit timeline. Its beat times and rounded 30 fps frame boundaries differ slightly; use the actual frame boundaries when making precise edit notes.
7. `../../marketing/momentum/source/momentum.py`, `core_scene.py`, `master.py`, and `score.py`: current camera choreography, geometry, rendering and original audio synthesis. The model is in `../../marketing/momentum/assets/FLOAT_concept_model.glb`.

The current source uses a procedural Python/VTK rendering pipeline. You may propose a different pipeline when it fixes a demonstrated bottleneck, but separate changes achievable with current assets from changes requiring a new renderer, external footage or paid services. Read code without executing it unless execution is needed and approved. Do not install software, subscribe to services, buy assets, publish, or overwrite the supplied cuts during this review.

## Evidence discipline

Begin by stating exactly what you inspected and how: decoded video frames, native playback, image sheets, source, audio actually heard, or audio measurements only. Do not claim to have watched fluid motion or heard the music when you only inspected stills or code. If direct playback/audio inspection is unavailable, give the useful visual/source review now and label judgments about motion, rhythm, timing and sound as provisional. Do not stall the whole review.

Treat previous README quality claims as context, not evidence that the creative result succeeds. Name specific timecodes and visible issues. Distinguish observations from interpretations and proposals.

## Required deliverable: OPUS_REVIEW.md

A. **Unvarnished verdict:** Does this look like a convincing public-launch teaser, a promising unfinished ad, or a technical demo? Explain the main reason in one paragraph. Judge independently; those labels are options, not a forced outcome.

B. **The five biggest issues, ranked by expected improvement:** For each give evidence/timecodes, the proposed fix, impact (high/medium/low), effort (quick edit / scene adjustment / substantial rebuild), and what uncertainty remains. Address art direction/materials/light, cinematography, editing rhythm, product comprehension, interaction payoff, sound, typography and mobile readability as relevant. Do not manufacture defects in every category.

C. **Shot-by-shot edit notes:** For all 16 existing shots, record KEEP / REWORK / REPLACE / CUT, the reason, and one concrete action. Use the actual shot names and timestamps.

D. **A better 24-second treatment:** Specify start/end times, shot subject, camera position/lens feeling/movement, subject movement, exact proposed copy, cut or transition, sound event and narrative purpose. Create kinetic contrast rather than constant motion. Give the first two seconds particular attention, and make the use-case payoff legible with sound off. Preserve the real product's slow physical movement; get excitement from cinematography and editing instead of false performance.

E. **Implementation plan:** Prioritize the three edits most likely to improve this materially in the next iteration. Then identify whether there is a hard visual-quality ceiling in the current rendering pipeline and exactly what would justify changing it. Point to source functions or files where useful. Include a bounded optional premium-production route; do not merely recommend spending more.

F. **Acceptance tests:** Give a practical release checklist and the minimum checks with viewers needed to establish that people understand what it is, want it, and distinguish concept visualization from working hardware. Do not invent survey results.

G. **One decisive intervention:** If you could change only one creative choice, what would it be and why?

Do not flatter the existing maker. Do not pad the answer with generic production advice. A precise dissenting opinion is more useful than agreeing with the prompt. Give detailed implementable reasoning, not private chain of thought. End with a compact handoff for the editor implementing your recommendations.
