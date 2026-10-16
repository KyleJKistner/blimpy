# Assembly and validation gates
This is a prototype handoff, NOT a validated flight construction manual. The bench
media node can be built before a flight controller exists.

## 1. Media bench wiring (USB-powered; no battery or motors)
XIAO ESP32S3 Sense must have its supplied camera/microphone expansion attached.
Do not populate the SD slot; speaker pins share the SD bus.

| XIAO connection | Destination |
|---|---|
| 5V pad (USB supply) | MAX98357A VIN |
| GND | MAX98357A GND |
| D8 / GPIO7 | MAX98357A BCLK |
| D9 / GPIO8 | MAX98357A LRC / LRCLK |
| D10 / GPIO9 | MAX98357A DIN |
| D1 / GPIO2 | MAX98357A SD, with external 100k pull-down to GND |
| Amplifier OUT+ / OUT- | Two speaker leads, respectively |

Neither speaker lead goes to ground: the amplifier output is differential.
Keep gain low; firmware attenuates PCM amplitude by 8, but test actual acoustic/electrical
power. The 1W speaker is NOT a 3W speaker. Use thin flexible wires, strain relief and
insulated joints; never allow exposed solder to rub on the envelope.

The Sense board's internal PDM microphone uses GPIO42 clock and GPIO41 data.
Its camera uses the official Sense pin mapping in the sketch. Do not reassign internal
camera pins. An antenna outside a metallized balloon is required; do not enclose it
behind the envelope and assume RF performance will be unchanged.

### Bench pass gate
Capture 100 photos and play/record 30 voice exchanges without brownout, reboot or heap
collapse. Test both Wi-Fi and the intended hotspot. Test phone-to-hub and hub-to-node
reachability explicitly. Measure brightness-dependent image quality and speech
intelligibility with motors OFF before attempting in-motion conversation.
Cloud STT/vision/TTS are optional and incur API costs.

## 2. Flight power architecture — verify before wiring
Protected 1S cell -> bq25185 BATT
bq25185 LOAD -> TPS61023 input -> nominal 5V electronics rail
bq25185 LOAD -> current-limited motor rail -> DRV8833 bridges -> motors
Common ground. Charger input comes only from the supervised 5V dock/USB supply.

The MiniBoost is set to approximately 5.2V, not exactly 5.0V. Measure it under load and
confirm the permissible supply range for every connected board revision before connection.
The LOAD rail can reach 4.5V while docked, exceeding the motors' 4.2V rated voltage:
**hardware-disable propulsion whenever dock power is present.**

Leave the XIAO's battery pads unconnected when using the external charger. Do not put
two charger circuits in parallel on the same cell. Disconnect external 5V feed before
USB programming unless the combined power path has been independently checked.

### Battery limit is a hard design constraint
Adafruit 258 is a 1200mAh protected cell; its datasheet continuous discharge limit is
1C = 1.2A. Each selected motor is rated at up to 1A, so three unrestricted motors plus
electronics are NOT compatible with this pack. Average 1.5W does not protect against
stall and start-up current. Software PWM alone is not a physical current limit.

Use a current-limited bench supply before battery tests, fit appropriate motor-current
regulation / sensing, and verify combined pack current including start-up, stalled
rotors, Wi-Fi transmit and speech peaks. Initial acceptance ceiling: <=1.0A total,
below the pack's 1.2A rating. If measured thrust cannot support the intended motion
within that limit, revise motor/prop/battery selection and rerun the mass model.
No full-power three-motor bench run from this LiPo.

The two DRV8833 boards need external sleep pull-downs and an independent dock cutoff.
An independent controller/watchdog must command safe zero thrust on boot, stale command,
processor reset, low battery or sensor fault. This firmware does not yet exist.
A battery protection circuit is not a normal state-of-charge or flight reserve controller.

## 3. Charging
The bq25185 board defaults to **1A charge current**. Set it to **500mA** by the
manufacturer's jumper instructions before connecting Adafruit 258. Leave Li-ion
4.2V termination selected, not LiFePO4. Verify actual current and cell polarity with a meter.
Enable the thermistor input per the manufacturer's guide and place a compatible 10k
thermistor in contact with the battery's outer surface, without puncturing it.
Keep the battery cool and separate from any thermal experiment.
Use only supervised charging on a noncombustible surface. Do not charge damaged,
swollen, hot or suspect packs; keep LiPo and helium equipment away from children.

## 4. Envelope acceptance is before propulsion integration
Need >=113L actual cold volume and ideally <=32g envelope including valve, for the
nominal 60cm design. The practical alternative is to measure **net envelope lift**
directly: helium-supported envelope with valve/tethers must lift at least ~85g,
before adding hardware. Non-envelope hardware budget is 73.3g. This gives roughly
12g integration margin, not cargo allowance after trim. Reject samples with inadequate
lift rather than claiming a "24-inch" retail label closes the design.

Weigh every installed part to 0.1g or better. Measure initial lift, 6h lift and 24h lift.
Record ambient temperature, pressure if available, and helium purity. Check electrical
noise, camera field of view and antenna range near the actual film.

Use supplier-stated >=99% helium. An 80% He/20% air mixture only supports ~93.9g dry
mass at this volume and does not carry the current 105.3g baseline.
Do not overinflate foil. The preheat scenario requires ~6.8% available volume expansion;
a fully inflated envelope cannot provide it. Never substitute hydrogen.
Secure gas cylinders and use the matching supplier regulator; ventilate and do not inhale gas.

## 5. Mechanical layout / initial flight
Build a light balsa/foam gondola below the balloon so its center of gravity is below the
center of buoyancy. Put the camera forward and clear of the envelope; battery low,
secured and insulated; antenna clear of metalized film. Two horizontal motors provide
forward/reverse and differential yaw. The third supplies vertical trim. This does not
provide arbitrary direct sideways movement or strong wind rejection.

Install fully effective lightweight propeller guards; verify guards cannot bend into
rotors under expected incidental contact. Three ordinary quadcopter propellers may
provide asymmetric reverse thrust; characterize both directions. Keep speeds low.
Weigh the complete guarded assembly; thick 3D-printed parts can consume the entire margin.

First test: tethered at room temperature, 1–2g heavy cold, power-limited, adults only,
away from fans, windows, stairs, children and pets. Then manual operation in a controlled
room with a spotter. Do not assume that slow gas leakage or temperature changes preserve trim.
Autonomous positioning, collision avoidance and return-to-dock are separate test gates.

## 6. Dock / fleet, only after one reliable robot
Stage 0 is manual USB-C charging, not pogo pins. Then build one mechanically constrained
dock with a funnel, stable capture, alignment markers and guarded/insulated contacts.
Use contact/latch detection and motor disarm before energizing the dock contacts.
A dock supply is low voltage, fused/current-limited and commercially safety-listed.
Do not connect bare power directly to the cell; contacts feed the charger INPUT.

For a later 3-bay strip, approximately 2m wide and >=0.65m deep accommodates 60cm
balloons at 10cm gaps. Use parallel supervised charging; allow ~2.75h turnaround.
A nominal 5V/5A supply is a planning choice for three <=1A charger inputs plus margin;
verify actual power distribution, fusing and connector ratings. Heaters are NOT included.

Fleet pass gate: repeated approach/abort/capture/charge cycles, temperature monitoring,
reliable low-battery return and safe power failure. Begin with 20 tethered docking trials,
then 100 supervised repetitions. Neither count proves household safety; log all rescues.

## 7. Thermal test, isolated
Separate tethered envelope, no flight battery inside and no free ascent. Instrument gas
temperature, ambient temperature and lift. Use a controlled, low-temperature heat source
and the film manufacturer's temperature/pressure limits; no flame, hot-air gun or glowing
element. Start with small temperature rises. Measure cooldown; fit U to data rather than
presume the illustrative U=2 coefficient. Heating the dock can make a cold-heavy robot
positively buoyant and invalidate motor-off behavior.

## 8. Object test
First detect and report visible marked objects in known locations. Store image timestamp,
camera pose estimate, confidence and human correction, not just a confident object label.
For carrying, begin with a known 1–3g foam token and a prepared fixture, supervised.
Grip mass and force, payload pickup/release and loaded/unloaded trim all need measurement.
A single ToF sensor does not produce room localization; IMU dead reckoning drifts.
Never authorize physical action by forwarding arbitrary LLM text directly to the motors.
