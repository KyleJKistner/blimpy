# Blimpy: project handoff

A helium-assisted AI companion and rotating-dock fleet concept: camera, microphone, speaker, phone connectivity, and low-power indoor movement.

**FLOAT** is the historical working name in the CGI films. **Blimpy** is the project/repository name.

## Start here

| Area | Entry point |
|---|---|
| Latest engineering review | [Revision 3 design review](engineering/v3/DESIGN_REVIEW.md) |
| Parts and procurement | [Component list](engineering/v3/procurement/components_v3.csv) |
| Physical experiments still required | [Experiment plan](engineering/v3/hardware/EXPERIMENT_PLAN.md) |
| Camera/audio/network bench starter | [MVP](engineering/mvp/README.md) |
| Latest launch film (30 s, Cycles rebuild) | [Room](marketing/room/README.md) |
| Previous 24-second CGI film source | [Momentum](marketing/momentum/README.md) |
| Independent-review handoff | [Opus review brief](reviews/opus/REVIEW_PROMPT.md) |

## Validation boundary

- Engineering results are calculations and software tests, not physical validation.
- The three engineering suites were rerun locally during import: **27 + 36 + 48 = 111 tests passed**. This is not hardware validation or a claim of remote CI coverage.
- Embedded firmware remains a bench starter; compilation, flashing, and assembled flight behavior are unverified.
- Videos are **CGI concept visualizations**, not working-prototype footage. The film model is not manufacturing CAD.
- **No Opus feedback has been obtained.** The review folder contains a request and instructions, not an independent endorsement.
- Physical endurance, acoustics, navigation, docking, gas retention, thermal stability, and safe propulsion require measurement.

Earlier engineering and film versions are retained in separate folders for provenance. Do not combine their component assumptions indiscriminately.

## Source snapshot versus full package

The remote source snapshot contains 106 text files: editable Python/firmware, numerical results, specifications, film-generation scripts, editing instructions, and the review brief. It does **not** contain the large MP4/WAV/GLB/image/XLSX files or several large generated reports. Some historical subfolder READMEs describe those full-package assets.

The companion **Blimpy_Full_Project.zip** supplied in the project conversation contains all recovered assets in this same folder layout. [artifact_inventory.json](artifact_inventory.json) records each original file's size, SHA-256, and whether it is in the source import. It is an import inventory, not a continuously updated manifest.

To add the remaining assets, extract the full ZIP and run from its `Blimpy` folder with Git configured for your account:

```sh
python3 tools/upload_remaining.py          # Verify locally; no Git writes
python3 tools/upload_remaining.py --push   # Commit remaining files to this public repository
```

The uploader uses normal Git authentication, refuses changed-file overwrites, and never force-pushes. No tokens are accepted in the script. The full-asset uploader's network path has not been executed from the originating session.

## Reproduction

Run each engineering test suite from its own folder; the historical revisions intentionally reuse module names. Install their documented dependencies in an appropriate Python environment.

```sh
(cd engineering/mvp && python -m pytest -q)
(cd engineering/v2 && python -m pytest -q)
(cd engineering/v3 && python -m pytest -q)
```

For film rendering, follow [Room's rendering instructions](marketing/room/README.md#rendering) (Blender 4.5 Cycles; final frames on an NVIDIA GPU via `render_gpu.sh`) or, for the earlier VTK film, [Momentum's rebuild instructions](marketing/momentum/README.md). Both require locally provided Inter Display fonts. **No font files, credentials, private network settings, or third-party API keys are included.** Rendering was not repeated as part of the repository import.

The checksum-verified source transport is retained in `.import/`; its workflow expands ordinary repository files and refuses different existing content. No open-source license is newly granted by this import; third-party dependencies retain their own licenses.
