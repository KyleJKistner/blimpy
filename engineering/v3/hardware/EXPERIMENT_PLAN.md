# Experiments that decide the design

Revision 3 • 15 October 2026 • **Protocol only: no experiments below have been performed.**

## Decision order

Test envelope material and propulsion before constructing multiple robots. These two experiments can reject the highest-value hypotheses with the least integration effort. Then measure trim stability and complete media power. Only after those pass should the integrated prototype undergo tethered control, supervised room navigation and docking trials.

A passing calculation is not a passing assembly. Retain exact part revision, raw readings, calibration records, photos of the fixture and uncertainty for each physical result. Do not pool supplier points, synthetic interpolation tests and our measurements into one dataset.

## 1. Film and seams: test the actual construction, not its marketing category

Request samples of Torayfan PMX2 15 µm, a manufacturer-confirmed thin CEL-MET heat-sealable PET, and the Capran reference material plus a converter-proposed compatible seam process. The 3M seam-only model is an alternative coupon experiment, not a qualified material system. Sources S01–S06 are in `sources.md`.

For each sample, record complete film construction, orientation, nominal yield, actual conditioned areal weight and lot. A 100 × 100 mm PMX2 coupon is only approximately 0.136 g: use an appropriate calibrated balance or weigh a larger accurately measured area. A display with 0.001 g increments does not by itself establish 0.001 g accuracy. Include cut-area error, static charge and environmental drift. Condition specimens together and use at least three independently fabricated test pouches per process, not three repeated readings of one pouch.

Ask the converter to determine the sealing process window. Do not interpret published seal temperature as a universal household-sealer setting. Measure peel resistance, pinholes, crease damage and retention before and after handling. Compare helium pouches with an identically fabricated air-filled/empty conditioning control to help distinguish film moisture effects from gas loss. Oxygen or water-vapor barrier figures are not a substitute for helium tests.

Only after coupon screening, build three independent complete envelopes. Record mass of finished neck, valve, seams, patches and markings. Measure actual axes/volume under a stated low differential pressure, rather than treating a flat pattern's dimensions as inflated dimensions. Thin flat panels are not guaranteed to form the modeled sphere without wrinkles or strain.

**Acceptance gates:** baseline finished envelope ≤36 g and actual cold volume ≥120 L. The mass-saving branch targets roughly 21–26 g, but is not accepted until retention and handling pass. Retain the earlier ≤1 g/day corrected net-lift-loss target over 72 h. It is an acceptance target, not demonstrated product performance. A near-zero trim launch will need substantially better short-term stability than a one-day average alone proves.

Measure net lift on a tared, calibrated force fixture, with the force direction and all tether contributions controlled. Record room pressure, temperature, humidity and settling time. Recheck every few hours. For sealed-gas temperature changes, use the conserved-gas model, not an equation that implicitly refills the envelope at each temperature. Internal gas temperature requires a separately qualified, sealed instrumented sample; a new feedthrough can itself create leakage. Never pierce a test article and assume its original leak rate still applies.

**Pressure:** no safe working pressure has yet been assigned. Obtain converter seam/valve limits before pressure testing; use a bounded, relieved laboratory fixture. The 2.76 kPa hot-gas example and 704 Pa ballonet example are calculations, not pressure permissions. No dock heater in this experiment.

## 2. Propulsion: controlled comparison at the thrust we actually need

Compare the reference Bitcraze direct-drive assembly with a complete supplier-matched 6 mm geared assembly and approximately 102 mm propeller. The MicronWings assembly has no included prop connector; confirm hub/shaft fit and retention before purchase. Sources S07–S10.

Use at least three independently assembled examples per finalist. Test actual propeller, guard, adapter and mount together. Keep the force fixture out of recirculating flow, with adequate separation from the ground and walls; record spacing in rotor diameters. Randomize the testing order to reduce temperature/battery-order confounding. Supply voltage at the driver, not the remote power supply, is the relevant value.

Measure forward and reverse separately at 3.3, 3.7 and 4.2 V. Include approximately 0.3, 0.5, 1, 2 and 4 grams-force where reachable, with a zero-command/no-load point and repeated starts. Use the actual 1 Ω current-sense configuration, motor driver switching mode and intended PWM scheme. Record current, voltage, thrust, RPM where feasible, warm-up, starts that fail to spin, and thrust settling/reversal delay. Deadband at very low thrust can invalidate the interpolated v2 model. Keep acoustic measurements at a fixed distance with background noise recorded; fewer RPM does not guarantee quieter gears.

Capture electrical transients with an appropriate shunt/current probe and oscilloscope. Mean winding-current regulation does not prove maximum battery current or bus-voltage safety during startup, braking and reversal. Check regenerative bus overshoot, local capacitance, fault assertion and battery protection behavior. Do not intentionally abuse or hard-short a lithium battery.

**Acceptance gates:** measured guarded combined horizontal reverse thrust ≥4 gf and lateral authority ≥4 gf where required by the control scenario, while meeting the aggregate power/current contract. These are engineering requirements, not certified motor ratings. A preferred geared solution should deliver at least 25% lower duty-weighted energy than the reference at the mission's signed thrust distribution, without violating installed mass, acoustics, startup or guarding requirements. Failure means retain the reference or redesign the gearing/propeller; do not extrapolate from 13.6 gf unguarded data.

Log thrust-map rows using `assembly_id,direction,guarded,voltage_v,thrust_g,current_a`. In the schema, thrust is a positive magnitude and direction is explicit. Use `engineering.measurements.MeasuredMap` only within the measured voltage/thrust convex hull. Save environmental and configuration metadata alongside the CSV. Never extrapolate an unguarded, forward-only map into a reverse/guarded operating point.

## 3. Dock trim and thermal stability

Build a manual instrumented restraint before an automatic dock. Separate charging from launch measurement. Measure lift with the real electronics awake on their battery, after the relevant thermal settling time, with motors stopped. USB/dock power and charging heat can otherwise bias the launch trim.

Use secure removable trim increments with individually measured masses. No loose magnets or dropped ballast; this is a supervised adult bench, not a product around children. Establish fixture uncertainty of approximately 0.05 g or better before trying a 0.3 g target. A 0.3 g displayed reading from an uncalibrated fixture is insufficient.

Begin at 1–1.5 g negative trim. Progress toward 0.3 g only after repeated measurements demonstrate stability. Record the next 10 minutes, then the complete intended mission duration. Include media-idle, camera transmission, speech, motor activity and representative ambient changes. A helium–air differential of only 0.1 K corresponds to about 0.049 g of lift in the nominal slack model. Do not attribute all changing lift to leakage.

**Acceptance gate:** reduce negative trim only to a value that remains controllable over the actual operating interval, including cooldown, sunlight exclusion, humidity and gas loss. The initial stretch target is ±0.1 g drift during a 10-minute steady-state interval, followed by mission-length validation. This does not demonstrate safe motors-off behavior. Abort near-neutral operation when drift exceeds the tested control margin.

A later docking mechanism can transfer captive ballast cartridges and recalibrate; automatic transfer hardware and its mass are currently unspecified. Manual trim makes it possible to test the energy hypothesis before inventing that mechanism.

## 4. Full media, radio and power budget

Record camera revision (OV3660/OV5640 or other), firmware revision, antenna, frame rate, resolution, Wi-Fi signal, microphone sampling, speaker gain and audio duty cycle. Test the speaker in the specified acoustic back chamber; bare-driver sensitivity is not complete-robot intelligibility. Sources S11–S22.

Test USB-powered logic without motors first; then a current-limited bench source; then the matching protected pack. Never connect board USB chargers and an external charger indiscriminately. First charging is manual with airborne loads disconnected. Validate polarity and actual BAT input compatibility at the lower cell voltage.

A repeatable slow-roaming workload should specify movement speed/duty, camera activity, microphone activity, speaking time, ambient airflow and network conditions. Log battery-side watt-hours, rather than multiplying an advertised battery capacity by an assumed efficiency. Target average ≤1.8 W for approximately three hours under the earlier usable-energy assumption, then replace that assumption with measured usable energy to the selected reserve.

**Acceptance gates:** total continuous current below the pack's 2 A rating, with a conservative initial 1.8 A engineering ceiling and validated transient behavior; no brownout/reset, unsafe heating or battery protection trips. No healthy-pack conclusion follows from one successful run. Repeat across at least three pack cycles and record delivered pack identity/capacity.

Place the antenna outside the metallized envelope and measure RSSI, packet loss and latency across orientations and motor states. Home Wi-Fi is the first bench network; the actual phone hotspot and its 2.4 GHz mode are separate tests. Verify phone-to-hub and robot-to-hub reachability explicitly. A hotspot providing Internet access does not automatically prove peer connectivity.

## 5. Navigation, force geometry and payload

The first control test uses external/fiducial pose in a controlled room with a physical safety perimeter. An IMU plus one downward range sensor does not yield room x/y position or all-direction obstacle detection. The numerical crosswind model assumes perfect pose and instantaneous thrust, so it is not a navigation demonstration.

Measure center of gravity and buoyancy, motor force lines, roll/pitch pendulum response, yaw response, balloon wake interference and motion drag in both principal directions. Step inputs should identify actuator delay and damping before tuning a full coupled model. Initially limit speed to roughly 0.3 m/s. Verify local watchdog/kill behavior without cloud connectivity. Add measured sensor latency and error to braking clearance; include body radius and guarded propulsion dimensions.

Four thrusters improve instantaneous control of forward/lateral/vertical force and yaw; they do not independently control roll/pitch. A three-motor vehicle may turn into a crosswind, but then camera heading cannot remain arbitrary. An alternative camera gimbal must earn its mass/power before displacing the lateral thruster.

No cargo in the first stability test. A prepared 1–3 g token is a later controlled trial with measured pickup/release transients. Untrimmed lift margin is not an unloaded robot's free pickup capacity. General object search, manipulation and autonomous docking are not supplied by this package.

## 6. Only later: pressure-ballast experiment

The Murata pump lead warrants a separate pressure-rated fixture after the base robot works. The 1.4 g figure excludes its driver, valves, pressure sensing, internal air bag, attachments and wiring. Map actual flow versus pressure and electrical input; never combine maximum flow with shutoff pressure. Verify hold leakage and that outer-envelope expansion does not cancel the intended ballast effect. This subsystem is not in the 79.82 g BOM and must not be silently added.

## Evidence storage and decision rule

`reports/physical_measurements.csv` starts empty and is never overwritten by model reruns. Supply raw data before replacing model assumptions. Reject a candidate when it fails a hard safety/retention/fit requirement even if its best test point looks efficient. Rank survivors by complete installed mass and measured mission energy, not by isolated component headline numbers.
