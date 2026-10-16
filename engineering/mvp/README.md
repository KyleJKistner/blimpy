# Helium Companion MVP
**Engineering package — 15 October 2026. One supervised indoor prototype first.**

## Decision
Build a cold-trimmed, approximately 60 cm actual-diameter helium robot. Keep the LLM
offboard. Validate camera, microphone, speaker and phone connectivity on the bench
before purchasing flight hardware. Treat thermal preheating as a separate experiment.
Do not buy or heat a fleet yet.

## What exists in this package
- A parameterized, unit-tested lift / mass / battery / heat / fleet model.
- Source-linked procurement CSV and a browser-readable purchasing checklist.
- An Arduino **bench firmware draft** for XIAO ESP32S3 Sense camera, microphone and
  MAX98357A speaker. It has NOT been compiled or tested on the hardware.
- A stdlib Python LAN hub and phone-browser console: snapshot, four-second microphone
  recording, optional typed or push-to-talk cloud conversation and synthesized speech.
- 27 passing tests for calculations and mocked host communications. Mock tests do not
  establish physical device compatibility, model access, flight, audio quality or runtime.
- Wiring constraints, envelope supplier questions, measurement templates and pass/fail gates.

**Not implemented:** flight firmware, autonomous navigation, return-to-dock, reliable
charging-contact engagement, object grasping, fleet scheduling, mobile/cloud relay,
full-duplex audio, robust echo cancellation, product-grade privacy/security.
No physical prototype has been assembled, and no orders have been placed.

## Calculated baseline (all performance estimates, not measurements)
A true 0.60m sphere at 20°C and 101325Pa contains 113.1L of helium. Pure helium permits
117.36g of supported dry mass (helium mass already deducted). Target dry build mass is
105.3g including a **32g envelope allowance**, but excluding helium, trim ballast and cargo.
That leaves 12.06g of untrimmed allowance, NOT unconditionally usable pickup capacity.
The mass allocations for frame, guards, envelope and several modules still need weighing.

For 1.5g cold-negative trim at the full volume, this baseline would require 13.56g of
secure ballast. Trimmed inertial mass including helium is about 137.7g. Alternatively,
reduce helium fill, then remeasure shape and stability. Do not intentionally fly
positively buoyant in a home; never release ballast in flight.

A 1.2Ah / 3.7V pack supplies nominal 4.44Wh. Reserving 20% leaves 3.552Wh.
At battery-side average loads of 0.9 / 1.5 / 3W, modeled runtime is 3.95 / 2.37 / 1.18h.
The 0.9W case means intermittent sensing and little movement, not continuous streaming.
The base power split is 0.65W camera/Wi-Fi, 0.10W control/sensors, 0.10W average speaker,
0.15W conversion/miscellaneous losses and 0.50W propulsion. Measure at the battery.

At 500mA charge current, allow 2.75h for recharge/taper/turnaround from the reserve point.
Three staggered robots and enough parallel charging can keep one active at the 1.5W
budget. This is deterministic duty-cycle arithmetic, not demonstrated fleet uptime.
With 60cm balloons and 10cm spacing, three stored robots occupy about a 2m-wide strip.

## Purchase sequence
Open `procurement/purchase_checklist.html`.
Stage A: $66.50 listed electronics, before tax/shipping, one working audio node plus
a spare Sense board and battery. Add cables and test tools only as needed.
Stage B: approximately $93.44 additional listed/allowanced flight components; two
Pololu prices are ALLOWANCES, not quotes. Envelopes, helium, mounts/guards, wiring,
current-limit hardware, thermal sensor, dock and tools are extra.
Plan roughly $350–650 total for an initial investigation if basic soldering and test
equipment is already available. This is a planning range, not a merchant quote.
A new lab setup or custom envelope may cost more.

## Quick start: calculations and tests
Requires Python 3.10 or newer; no third-party Python packages.
```sh
python -m engineering.model
python -m unittest discover -s tests -v
```
Edit `engineering/assumptions.json` rather than silently substituting optimistic numbers.
The spreadsheet is a parallel editable engineering model; edits do not auto-sync to JSON.

## Quick start: first physical bench node
1. Read `hardware/BUILD_AND_SAFETY.md`. Begin with USB power and NO battery or motors.
2. Install Arduino IDE and an Arduino-ESP32 3.x board package. Select XIAO ESP32S3,
   enable PSRAM and follow current Seeed board setup. The code has not been compiled here;
   log the exact working board package version once hardware validation is done.
3. Copy `firmware/bench_node/config.example.h` to `config.h`, set a 2.4GHz SSID and
   password, and replace the token with a random 24+ character string.
4. Wire the MAX98357A and speaker as specified. Keep the SD slot empty. Flash the sketch;
   read its local IP from Serial at 115200 baud. Camera/microphone revision differences
   must be resolved against current Seeed documentation before proceeding.
5. On the hub computer, configure:
```sh
export DEVICE_URL="http://192.168.1.100"  # replace with the printed node IP
export DEVICE_TOKEN="your-private-device-token-at-least-24-characters"
export HUB_TOKEN="a-different-private-hub-token-at-least-24-characters"
python -m host.hub --bind 0.0.0.0
```
6. On the same trusted Wi-Fi, open `http://HUB_COMPUTER_LAN_IP:8765/` in the phone
   browser and enter HUB_TOKEN. Use the capture and recording buttons before enabling
   any cloud features. Private firewall permission may be required.
7. Optional cloud voice/vision: set `OPENAI_API_KEY` and `VISION_MODEL` on the computer,
   then restart the hub. Use an image-capable Responses API model available to your
   account; no model access is presumed. Defaults for speech are
   `gpt-4o-mini-transcribe` and `gpt-4o-mini-tts`, overridable with STT_MODEL/TTS_MODEL.
   Cloud audio/image upload requires checking consent and pressing Ask/Speak.
   This is deliberately four-second, push-to-talk, half-duplex audio, not a realtime agent.
   The AI-generated speaker answer is capped at 12 seconds.
8. The API key never goes on the robot. The demo does not persist media to disk.
   **Both local links use plain HTTP by default. Do not port-forward this service or
   expose it on the public Internet.** Product deployment needs TLS, provisioning,
   privacy controls and authenticated network relay.

## Phone hotspot
The radio is 2.4GHz Wi-Fi, not cellular. For compatible iPhones, enable Personal Hotspot
and Maximize Compatibility. For the first test, connect BOTH the node and hub computer
to the hotspot. Check that the phone browser reaches the hub and the hub reaches the node:
host/client reachability is not guaranteed by Internet access alone. A hotspot is a router,
not the LLM server. Later replace the laptop hop with an authenticated outbound cloud
relay / mobile app; that relay is NOT implemented in this package.

## Bandwidth budget
Assuming a 40KB JPEG once per second gives ~320kb/s. Raw mono 16kHz PCM16 microphone
audio is 256kb/s; 24kHz PCM16 playback is 384kb/s. Half-duplex snapshots plus speech
fit in an approximate 0.6–1Mb/s engineering allowance including overhead. Actual
JPEG sizes and hotspot reliability must be measured. The supplied bench code uses
explicit snapshots, not a continuous video stream.

## Preheat is not stored hours of flight
At constant pressure with a flexible, not-yet-full envelope, heating the cold 113.1L
helium charge from 20°C to 40°C expands it to 120.8L and adds ~9.29g lift. The outer
diameter must expand to about 61.3cm. A taut fixed-volume balloon does not gain that lift.
At assumed U=2W/m²/K, the simplified gas+film thermal time constant is ~60 seconds:
extra lift falls to 3.43g after a minute and 0.47g after three minutes. The uncertain
U=1–5 range gives roughly 120–24 seconds. This lumped model is not a measurement.
Stored heat is ~0.76Wh thermal; holding the initial temperature difference takes ~45W.
There is no direct equivalence between a thermal Wh and a battery Wh of useful flight.

Warm-launch and cold trim are incompatible unless modeled explicitly: a unit trimmed
1.5g heavy cold becomes about 7.8g positively buoyant immediately after this preheat.
No untethered thermal flights. Do not heat the battery or use preheat to compensate
for an under-sized envelope. Recovering 1W of waste heat adds only ~0.2g lift under
the same assumed heat-transfer coefficient.

## Finding and moving things
The camera can supply views to an object model. Reliable room search additionally needs
localization, coverage planning and recovery behavior. A single range sensor and IMU
do not solve that. The initial test is a visible, prepared target, with ground truth.
First cargo experiment: 1–3g foam token on a prepared dock, not a phone, keys or a
general-purpose gripper. Extra gripper and cargo mass changes both trim and energy.
Untrimmed lifting margin, actuator thrust capacity and useful payload are different.

## Source documentation
Product URLs and status live in the BOM. Manufacturer setup and physical references:
- https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/
- https://wiki.seeedstudio.com/xiao_esp32s3_sense_mic/
- https://docs.espressif.com/projects/arduino-esp32/en/latest/api/i2s.html
- https://www.grc.nasa.gov/www/k-12/airplane/glussac.html
- https://www.grc.nasa.gov/www/k-12/airplane/eqstat.html
- https://webbook.nist.gov/cgi/cbook.cgi?ID=C7440597&Mask=1
- https://support.apple.com/guide/security/wi-fi-security-with-apple-devices-secfd166f620/web
- https://developers.openai.com/api/docs/guides/images-vision
- https://developers.openai.com/api/docs/guides/speech-to-text
- https://developers.openai.com/api/docs/guides/text-to-speech

All prices/status are observations checked 15 October 2026; recheck before checkout.
