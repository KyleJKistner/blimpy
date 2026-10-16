# Helium companion — revision 3 design review

**15 October 2026.** Research, calculations and reduced-order numerical simulations, not a flight-qualified design. No new physical measurements, supplier communications, orders, firmware compilation or assembled-system tests were performed.

## Decision

There are two concrete component-level opportunities worth testing: a factory-integrated heat-sealable metallized film that reduces the modeled envelope from **33.36 g to 20.57 g**, and a **2.33 g geared motor** whose published larger-propeller data suggest materially better thrust per electrical watt than the old small-rotor reference. Neither is yet validated for our balloon and signed, guarded, current-limited workload.

The strongest architecture-level opportunity is to use the dock as a **measurement and trim station**, rather than a heater. Removing unnecessary continuous vertical thrust may be at least as useful as changing the motor. Keep a conservative four-axis actuator layout for a companion that needs to look at a person while resisting crosswind. The current dry hardware allocation is **79.82 g before envelope, helium, trim ballast and cargo**.

The objective is not to call ordinary materials or gearing a new invention. It is to find a small, measurable system improvement that makes this particular product practical.

## Evidence levels

The package contains 48 passing software tests, 81 seam-construction scenarios, five equal-volume shapes and six crosswind trajectories with numerical step checks. These tests establish arithmetic, conservation, allocation rank, numerical consistency and input-validation behavior. They do not establish helium retention, acoustic comfort, guarded thrust, navigation or battery endurance.

The source ledger distinguishes manufacturer data, merchant stock, assumptions and unmeasured assemblies. Supplier measurements are stored separately from our intentionally empty physical-measurement log. The thrust-map loader refuses extrapolation outside measured voltage/thrust coverage and refuses to mix guarded/unprotected or forward/reverse data.

## 1. A materially lighter envelope without inventing a material

The prior construction used 12 µm Capran metallized nylon at 13.94 g/m² plus an assumed full-area 8 µm polyethylene layer and an assumed full-area 2 g/m² adhesive. Those extra layers were not manufacturer-verified. Reference: [AdvanSix data](https://www.advansix.com/wp-content/uploads/2023/02/Capran-PIR-MT1200-TDS.pdf).

Toray's existing [PMX2 film](https://www.toraytpa.com/wp-content/uploads/2019/06/TFN-PMX2-Technical-Data-Sheet-Metric.pdf) has a metallized face and a heat-sealable face in the supplied film. The 15 µm version's nominal yield is 73.3 m²/kg, corresponding to **13.6426 g/m²**. Do not add a second full-area seal layer in the mass calculation.

For the same 62 cm nominal sphere and 12 gores with 5 mm flanges:

| Calculated item | Value |
|---|---:|
| Ideal sphere volume | 124.788 L |
| Ideal sphere surface area | 1.20763 m² |
| Film area including two mating seam flanges | 1.32450 m² |
| PMX2 film mass | 18.0695 g |
| Assumed complete valve/neck/patch allowance | 2.5000 g |
| **Complete calculated envelope** | **20.5695 g** |
| **Saving from previous construction** | **12.7912 g / 38.3%** |

PMX2 is packaging film, not a demonstrated standalone helium envelope. Its full-film helium permeation, metal pinholes after creasing, seal leaks, handling damage and actual fabricated volume remain unknown. Nominal manufacturer properties are not guaranteed batch limits. The predicted reduction is valuable enough to test; it is not enough to release a production balloon.

A second route keeps Capran and puts adhesive only at seams. Modeling 60 µm adhesive at an assumed density of 1 g/cm³, counting one adhesive interface rather than both flanges, yields **24.47 g**. The [3M 467MP data](https://multimedia.3m.com/mws/media/2366204O/3m-adhesive-transfer-tape-467mp.pdf) supplies thickness, not our density or compatibility assumptions. This route needs adhesive/nylon and helium testing. A factory-sealable CEL-MET PET option is another coupon candidate; the numeric yield remains provisional because its PDF image could not be retrieved for visual verification.

### What weight savings actually buy

At fixed volume, a neutrally buoyant robot's total mass is set by displaced air. Removing skin mass and then replacing it with ballast does not make that all-up vehicle easier to accelerate. The saving must be spent on a smaller envelope, additional useful hardware/battery, or margin—not counted a second time as reduced inertia.

Solving the mass balance with 80 g hardware, 3 g reserve, 96% of ideal sphere volume and the specified adverse separate-fill case gives minimum modeled diameters of **61.79 cm** for the old full laminate, **59.98 cm** for seam-only Capran and **59.18 cm** for PMX2. These are conditional roots, not manufacturable tolerances. A 38% skin reduction does not halve a hardware-dominated balloon. Keep 62 cm for the first prototype and use the margin to avoid fragile integration.

## 2. Match propulsion to millinewton loads

The previous small rotors were inherited from a quadcopter regime. Here most weight is already supported by helium. At fixed thrust, ideal static induced power is:

`P_induced = T^(3/2) / sqrt(2 rho A)`.

Thus a 101.6 mm rotor has **46.3% of the ideal induced power** of a 47 mm rotor at the same thrust. This is a lower-bound comparison, not an electrical-efficiency prediction. Profile drag, Reynolds number, bearing and gearbox losses, motor efficiency and guards remain. Reference: [ERAU rotor momentum theory](https://eaglepubs.erau.edu/introductiontoaerospaceflightvehicles/chapter/vtol-aircraft/).

[MicronWings](https://micronwings.com/product/gearbox-6mm-ball-raced/) publishes 13.6 gf at 3.8 V and 420 mA for its 2.33 g geared assembly with a GWS4025 propeller. That is **1.596 W**. Subtracting the historical Bitcraze fixture's stationary-current baseline and treating its thrust/current as a four-motor measurement gives approximately **3.249 W per motor** at 13.6 gf. The roughly 2:1 contrast justifies a controlled comparison; it does not establish one. [Reference data](https://www.bitcraze.io/documentation/repository/crazyflie-firmware/master/functional-areas/pwm-to-thrust/).

Important: the attractive supplier point is at 420 mA, above the proposed winding-current limit. Its low-thrust map is missing. The gearbox ships without a prop connector, and its 0.97 mm shaft needs a matched adapter. Reverse thrust, minimum starting duty, geared noise, exposed blade guarding and electrical transients are unknown. The complete propeller/adapter/guard assembly is not procurement-closed.

## 3. The charging strip can also correct trim

In a near-neutral vehicle, a few grams of excess weight can dominate steady propulsion. Hold battery, electronics, movement pattern and the old motor proxy unchanged, then vary only negative trim:

| Negative trim | Modeled total power | Runtime from 5.55 usable Wh |
|---|---:|---:|
| 1.5 g | 1.770 W | 3.13 h |
| 0.5 g | 1.456 W | 3.81 h |
| 0.3 g | 1.394 W | 3.98 h |

This is a sensitivity experiment, **not the finished four-gearmotor runtime prediction**. The old empirical map is itself uncertain at very low thrust. It nevertheless identifies a testable system lever: arrive, charge safely, measure net lift with the electronics in their intended state, adjust captive ballast, and depart with less unnecessary vertical thrust. Manual trim tests the principle before adding an automatic mechanism.

The harder requirement is maintaining trim. In the slack 120 L model, helium only 2 K warmer than ambient adds about **0.982 g of lift**. Electronics heating, gas loss and nylon moisture uptake can swamp a 0.3 g trim target. The dock must measure, not merely assume, the departure state; the mission must tolerate subsequent drift. Do not extrapolate a 10-minute stable test to an entire charge.

## 4. Heating needs a conserved-gas model and pressure margin

The v3 state model holds gas quantity fixed, lets volume respond to temperature and ambient pressure while slack, then imposes an ideal hard maximum volume. It distinguishes warming the helium relative to air from warming both together. For slack dry ideal gases, equal ambient/gas temperature changes cancel to first order in lift; refilling a fixed volume at each temperature describes a different experiment.

With a 120 L fill at 20°C and a 124.788 L maximum, the theoretical taut transition is **31.70°C**. Helium at 40°C would seek **128.187 L** at ambient pressure. Constrained to the maximum, the model predicts approximately **2.76 kPa excess pressure**. Real film stretches and seams have nonlinear behavior; this is a warning calculation, not a qualified pressure limit. Once volume is constrained, more heat does not add more displaced air.

Heat-loss runs bracket an assumed overall transfer coefficient of 1–5 W/m²/K. They are not measured coefficients or conjugate heat-transfer CFD. No dock heater belongs in the first build.

## 5. A fourth thruster serves the camera

Two forward thrusters plus one vertical thruster provide forward force, vertical force and yaw. They cannot provide independent lateral force while holding arbitrary heading. Three-motor blimps can turn into the wind, but that can turn the camera away from the person.

Adding one lateral thruster produces a full-rank allocation for forward/lateral/vertical force and yaw. Roll and pitch still rely on passive stability, and mounting geometry matters. A fixed-heading one-dimensional crosswind test with 0.3 m/s wind, ideal pose and an assumed 4 gf lateral limit produces approximately **11 cm peak drift** for the four-thruster branch. Without lateral thrust, it crosses 1 m of travel about **9 seconds after the gust begins**. A real room would interrupt that uncontrolled trajectory at a wall; the model has no walls.

These are conditional dynamics, not measured station-keeping accuracy. The solver uses instantaneous thrust, perfect pose, simple drag and constant added mass. It does not model envelope wake, latency, backlash or full six-degree-of-freedom attitude. Its reliable conclusion is the missing actuator direction, not a promise of 11 cm positioning.

A downward rangefinder plus IMU does not supply horizontal localization or 360-degree collision detection. The first room needs supervised external/fiducial pose; autonomous home navigation is a separate deliverable.

## 6. Geometry can narrow the robot without sacrificing volume

A 1.5:1 prolate spheroid with the same volume as the 62 cm sphere is approximately **54.2 cm wide × 81.2 cm long**. Surface area rises **2.74%**, and the seam-only skin model adds approximately **0.99 g**. Forward projected area falls 23.7%, but side projected area rises 14.5%. Do not assume unchanged drag coefficient or that narrower means better turning clearance.

This is a useful packaging option, not a miniaturization miracle. A sphere is the simplest initial control reference; a prolate sample should be compared after drag and handling measurements.

## 7. Component and electrical decisions

The detailed CSV totals **79.82 g**, including a 4 g reserve. The 80 g rounded concept budget is not a measured assembly. Notable updates:

- XIAO ESP32S3 Sense remains the camera/microphone/network board. Record the delivered camera revision; current documentation has incomplete OV5640 power data.
- XIAO nRF52840 **Sense Plus** replaces the standard Sense to expose enough pads for four bridges, sensors and an independent media link. Installed board/harness mass and software-core pin mapping remain tests.
- Keep the specified 34 g protected 2 Ah Adafruit 2011 pack. Although the manufacturer listing is out of stock, the exact DigiKey SKU is listed in stock; no order or reservation was made.
- Replace the unavailable reference speaker with the PUI AS01808AO-SC18-WP-R, a specified 1.8 g bare driver listed in stock. Its 96 dB figure is at **0.1 m and 1 W with a 1 cc back volume**, not at 1 m and not free of enclosure mass.
- Two DRV8833 carriers supply four motor channels. Factory current regulation is disabled until the sense links/resistors are modified. For the four-motor concept, the 0.82 Ω setting yields a 25°C static allocation just over 2 A. A 1 Ω, 1% starting point yields approximately **1.79 A** including the explicit media/other allowances. This is not proof against startup, ripple, regenerative overshoot or rail sag.

Sources and stock limitations are linked per row in `procurement/components_v3.csv`. The 9 g allowance for four propellers, guards, adapters and mounts is aggressive and unverified. Cargo, ballonet hardware, automatic ballast transfer and a camera gimbal are excluded. No generic battery substitute is accepted solely because it is labeled 2,000 mAh.

At 120 L, nominal support after gas weight is **123.28 g**; the adverse separate-fill support is **117.53 g**. With 80 g hardware and a PMX2-model skin, dry mass is **100.57 g**, leaving approximately **22.71 g nominal or 16.96 g adverse before trim**. With the old full laminate, adverse margin is only **4.17 g**. None of this margin is an automatic pickup rating after the robot has been ballasted to neutral.

## 8. A more speculative route: retain buoyancy adjustments without continual thrust

An internal air ballonet inside a **volume-constrained** outer envelope can add mass by pumping air in. For a fixed 120 L envelope, adding 1 g of air requires roughly **0.834 L intake**, approximately **704 Pa excess pressure**, and an ideal reversible pump-work lower bound of **0.293 J**. A freely expanding outer balloon would largely cancel that mass change with added displacement; constrained volume is essential.

The [Murata microblower datasheet](https://media.digikey.com/pdf/Data%20Sheets/Murata%20PDFs/MZB1001T02_DS.pdf) lists a 1.4 ± 0.2 g bare pump. It needs a driver, valves, pressure sensing and an internal bag. Its high-flow and static-pressure figures are different test points. Pressure qualification, leakage, total mass and actual electrical work are unresolved. This is a research branch, not included in the recommended MVP or its endurance.

## What deserves confidence now

High confidence: conservation-based sizing relationships, film-weight arithmetic conditional on supplied material, allocation-rank limitations, and the need to measure signed guarded propulsion rather than extrapolating headline specifications.

Moderate confidence: the identified films and geared assembly are worthwhile candidates to test. Low confidence until measured: a 21 g durable helium envelope, stable 0.3 g trim, low-noise four-hour autonomous roaming, and a useful lightweight ballonet.

The next spending should buy **material samples and competing propulsion assemblies**, not a fleet. Detailed acceptance criteria and raw-data schemas are in `hardware/EXPERIMENT_PLAN.md`. High-fidelity simulation becomes useful after geometry, actuator maps, thermal behavior and sensing latency are measured; a more elaborate uncalibrated model would not close these gaps.
