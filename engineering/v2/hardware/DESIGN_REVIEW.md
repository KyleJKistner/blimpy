# Component and envelope review

## 1. Envelope: calculate the actual stack, not just 'Mylar'

Nominal outer sphere diameter 0.62 m, 12 shaped panels (gores), 5 mm flange on EACH mating edge. Ideal sphere area = pi*d^2 = 1.207628 m2. Approximate seam length = 12*pi*d/2 = 11.686725 m. Additional seam area = 2*0.005*length = 0.116867 m2. Total installed cut-film area = 1.324495 m2. This is a first-order gore/seam area model, not a membrane finite-element prediction or a validated cutting pattern. Scrap outside the cut panels does not fly and is excluded.

The AdvanSix Capran PIR-MT1200 TDS gives 12-micron metallized biaxially oriented Nylon 6, typical basis weight 13.94 g/m2. The aluminum barrier is already in that weight: do not add it a second time. This film alone is NOT specified as a complete heat-sealable balloon laminate.

Proposed additional construction: 8-micron PE seal layer at an assumed density of 0.92 g/cm3, plus 2 g/m2 lamination adhesive. These are converter-design assumptions, not a verified purchasable laminate. Complete nominal basis = 13.94 + 8*0.92 + 2 = 23.30 g/m2.

| Flying material | Mass |
|---|---:|
| Metallized nylon across body AND seam margins | 18.463 g |
| PE sealant across body AND seam margins | 9.748 g |
| Adhesive across body AND seam margins | 2.649 g |
| Neck/valve allowance | 1.000 g |
| Pole/attachment reinforcement allowance | 1.500 g |
| **Complete predicted envelope** | **33.361 g** |

Specify a finished helium-barrier, heat-sealable laminate <=25 g/m2; total valve/neck/reinforcement <=2.8 g. At the nominal installed area this totals <=35.912 g, supporting a 36 g receiving limit. The actual fabricated envelope must still be weighed. A material listing without a seal layer and helium-retention evidence is not an approved substitute.

15 sealant/adhesive combinations were evaluated. For example, 15-micron sealant with 2 g/m2 adhesive increases predicted envelope mass to 41.89 g: this fails the 36 g gate. Thickness matters, but inflated shape/volume can matter more. A 10% volume shortfall at this scale costs roughly 12 g of support. Package width and nominal party-balloon diameter are not evidence of actual displaced volume.

Manufacturer oxygen-transmission data were NOT used as helium-transmission data. No leakage rate has been inferred from oxygen barrier performance. Nylon humidity conditioning, seams and valve leakage remain physical measurements.

## 2. Mass closure and acceptance hierarchy

Nominal hardware allocation is 76.3 g, including 4 g unallocated integration reserve. Nominal envelope 33.36 g gives 109.66 g before helium and ballast. At 120 L and the reference conditions (20 C,101325 Pa,50% RH,99.5% He), gas lift after gas weight is 123.28 g, leaving 13.62 g before trim.

At the deliberately adverse fill-capacity corner of 120 L,27 C,100000 Pa,70% RH,99% He, available support is 117.53 g. With the finished envelope at 36 g and hardware at the GLOBAL 78 g cap, 3.53 g remains before trim. Allowing every individual component its full separate tolerance raises the hardware budget to 81.2 g and leaves only 0.33 g. **Therefore the 78 g aggregate cap is mandatory; individual tolerances cannot all be spent independently.** The 128-case table records the unconstrained individual-tolerance stress test, not a probability of success.

These environmental calculations compare separately filled, approximately ambient-pressure envelopes. They are NOT the trajectory of one sealed gas charge changing temperature. A slack sealed envelope expands/contracts, while a taut one can change pressure; operating thermal effects require their own volume/pressure model.

Trim the cold robot slightly negative, initially 1.5 g equivalent downward weight, using securely attached removable-at-dock ballast. At the nominal full-volume point this uses roughly 15.12 g of ballast; its inertia is included in the near-neutral dynamics model. Gas weighs approximately 20.59 g under the same nominal 120 L conditions. The inertial flying mass is therefore about 145.36 g, not 109.66 g. Payload picked up AFTER trimming adds motor load; it does not automatically consume 'free buoyancy'.

## 3. Component decisions

1. **Battery:** Adafruit2011 protected 2000mAh, manufacturer34 g; replaces Adafruit258 1200mAh23 g. The linked pack datasheet specifies 2 A maximum continuous discharge and minimum1900mAh capacity. A 25% assumed usable-energy derating gives5.55Wh nominal, or5.2725Wh at minimum nameplate capacity. At1.8W these correspond to3.08h and2.93h.
2. **Power:** remove separate flying charger6091 and boost4654 (5 g in v1). Feed each XIAO's BAT pads from protected1S and power the amplifier/drivers from the appropriate filtered battery branch. Do NOT use a raw battery on3V3. Ground is common in flight. Motor current must not flow through a microcontroller regulator or its ground return trace.
3. **Charging:** keep bq25185 on the dock, configured500mA with appropriate thermistor. Initial charging must physically disconnect the entire flying load, including both XIAOs, from the pack. Both XIAOs have their own chargers: never connect USB while the external battery/charger path is active. The automated make/break connector and interlock are NOT yet engineered or tested. A 4h recharge-turnaround allowance supports a three-robot rotation for one active unit at the3.08h case, not for every mission.
4. **Safety controller:** replace RP2040 plus separate IMU with Seeed102010469 XIAO nRF52840 Sense (onboard LSM6DS3TR-C). Allocate3g installed. The declared first interface uses UART RECEIVE ONLY from the ESP32; the freed D6 reads driver faults. No return flight telemetry is implemented. This is an interface choice, not completed safety firmware.
5. **Camera/radio/mic:** XIAO ESP32S3 Sense. Seeed now warns the delivered camera may be OV3660 or OV5640, and OV5640 current data are not provided in its comparison table. Record exact board and camera revision. An older measured web-camera run reports155mA average at3.8V and366mA peak, but that is NOT a bound for the new sensor. Reserve0.7A for the media branch pending measurement; reject/rework an assembly that exceeds it under required workloads. The antenna and microphone remain OUTSIDE the metallized envelope. Range and noise cancellation are not simulated.
6. **Audio:** keep MAX98357A +8-ohm1W3g speaker3923, but the latter is currently out of stock at Adafruit. It is a design reference, not a buy-ready flight part. No heavier 'equivalent' may be substituted silently. Constrain output to roughly0.3W initially (about1.55V RMS across8ohm), verify loudness and average supply current. The class-D output is bridge-tied: neither speaker lead goes to ground. Baffle mass is included in the frame allocation.
7. **Propulsion:** test3 Bitcraze7x16mm2.7g motors with matching0.8mm-shaft47-17props, two horizontal and one vertical, through2 Pololu2130 carriers. Guard/mount/prop allocation5.5g. These are BENCH CANDIDATES until forward/reverse thrust passes with actual guards, driver current chopping and low battery voltage. Not certified safe near faces, hair or children.
8. **Altitude:** Pololu3415 VL53L1X bare carrier0.5g, powered3.3V from the safety controller; published typical20mA/peak40mA. Its rangefinder does not supply complete room localization or obstacle coverage.

## 4. Current limiting is a real build modification

Pololu2130 shorts both sense terminals to ground by default: current regulation is disabled. Cut the specified links and fit three1206 sense resistors (one per used channel), initially0.82ohm,1%,>=0.25W. At25 C the TI trip threshold spans160-240mV. Predicted trip span is0.193-0.296A per winding, nominal0.244A. Three maximum trip allocations +0.7A media +0.12A other gives1.707A.

This is a static allocation, NOT a transient-current guarantee. The driver has current-sense blanking and switching delays; startup and a blocked rotor must be measured on a current-limited bench. PWM battery current is not winding current. The historical motor table cannot prove that a0.244A winding limit produces the assumed thrust. If the guarded limited motor cannot supply at least2g forward/reverse under required voltage, propulsion is rejected, not 'fixed' by silently removing current limits.

The carrier's nSLEEP has a47k pull-up to the motor rail. Remove that pull-up and use a verified default-low enable circuit; a100k pull-down alone against the existing pull-up is not a reliable default-off design. Proposed enable: MCU through1k,100k pull-down at the common SLP node, docking interlock clamps it low; verify logic levels. Shared open-drain nFAULT outputs feed nRF D6 with3.3V pull-up. Supervisor firmware must latch faults and require deliberate rearming; it has not been written/integrated here.

No pack fuse, thermistor, current limiting or protected-cell label is a substitute for the assembled electrical and thermal test. The entire system must remain within a1.8A continuous bench-acceptance ceiling and the pack's specifications across the intended operating range. Scope current spikes and rail sag. A protection-board trip is a test failure, not a normal operating mode.

## 5. Runtime and motion models

The manufacturer's old Crazyflie table contains FOUR motors plus electronics. Subtract its0.24A stationary baseline and divide by4 before deriving incremental motor watts. The code also supports subtracting constant baseline power as a sensitivity check. The resulting table is only a proxy for our motor/prop lot and not for guarded/reversed/chopped operation.

The three mission cases use thrust_eff0.75 (assumed guard/installation derating),1.5g negative trim, Cd0.6 (assumed), and explicit base-load/correction allocations:

| Case | Speed | Moving share | Base W | Extra correction W | Proxy total W | Runtime |
|---|---:|---:|---:|---:|---:|---:|
| Quiet presence |0.15m/s|10%|0.75|0.10|1.367|4.06h|
| Slow roaming |0.30m/s|30%|0.95|0.20|1.770|3.13h|
| Active roaming |0.60m/s|75%|1.20|0.40|3.100|1.79h|

These are conditional projections, not verified endpoints or product claims. Media average includes camera/radio/mic, controller/sensor, audio duty and conversion/driver overhead. No conversion loss is deducted a second time. The cold-trim rotor is not treated as power-free. Minimum2000mAh-pack capacity reduces these runtimes5% before further aging/temperature differences.

Braking was numerically integrated in1D, then checked against the closed-form integral. It includes gas/ballast inertia and an assumed added-fluid-mass coefficient0.5. Assuming4g TOTAL reverse thrust and0.3s detection/actuation latency:0.3m/s stops in0.313m;0.6m/s in0.872m;1m/s in1.627m. These are centre-of-mass travel distances: obstacle clearance must additionally account for the0.31m body radius, sensing uncertainty and margin. The4g reverse thrust is a requirement to measure, not a demonstrated capability.

At1m/s the62cm sphere requires about11.1g of steady horizontal thrust in the chosen drag model. That alone exceeds the initial4g combined-thrust test target. Thus the first operating envelope is slow indoor motion, not accompanying a walking adult outdoors. Crosswind, HVAC jets, pendulum dynamics, six-degree-of-freedom stability and docking are not simulated.
