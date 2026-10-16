# FLOAT — Opus review packet

**Status: prepared handoff. Opus 5.5 has not been consulted from the originating ChatGPT session.**

This folder contains both actual final Momentum cuts, a neutral independent-review brief, the current source and 3D model, existing overview sheets, and 64 fresh timestamped frame samples. No font files are included. Audio is present in the MP4s; separate music stems are omitted to keep this packet smaller. `score.py` is included, but the packet is for review, not a guaranteed self-contained render environment.

## Use in Claude Code

Open this extracted folder as the project, select Opus 5.5, then send:

> Read REVIEW_PROMPT.md and perform the independent review it requests. Inspect the actual cuts and the provided image evidence with your available tools. State any limits on video/audio inspection. Write your critique and concrete next edit to OPUS_REVIEW.md. Do not render or publish anything yet.

Approve only the local read/inspection actions you intend. This packet does not require sharing an API key, enabling unsafe permissions, or buying anything.

## Use in an image-capable Claude chat

Paste REVIEW_PROMPT.md and attach the two existing overview JPEGs from `../../marketing/momentum/previews/`, plus the four JPEGs in `motion_sheets/`. Add the cuts only if that interface supports useful video inspection. A still-image-only review must not be described as a review of the soundtrack or fluid motion. Claude Code is the more complete route for inspecting the source and decoding clips locally.

## Return

Bring OPUS_REVIEW.md back to the original conversation for implementation. This packet contains no Opus result and makes no claim that any external consultation has occurred.

## Inventory

- `media/`: two original, unchanged MP4s.
- `../../marketing/momentum/`: source, GLB model, prior overview sheets and render metadata.
- `frames/`: 48 wide samples plus 16 feed samples.
- `motion_sheets/`: one three-column contact sheet per four wide shots.
- `frame_manifest.json`: exact timestamps and frame indices.
- `REVIEW_PROMPT.md`: independent-review instruction.
- `integrity.json`: sizes and hashes of included media, for verification.
