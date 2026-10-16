# Physical receiving and bench tests — not yet performed

Use calibrated scales and a current-limited laboratory supply. First propulsion tests are restrained, guarded and away from people, pets and loose hair. Keep helium cylinders secured and use a compatible regulator; no deliberate battery heating. Never charge unattended or with flying electronics connected to the external charger.

## A. Envelope receiving and retention
1. Mark samplesA/B/C and record film/valve lot, approximate room temperature, relative humidity and barometric pressure. Condition the empty material in the intended indoor environment before weighing. Use a0.01g-resolution scale for small parts and at least0.1g for complete assemblies. Repeat tared readings3times; do not report more precision than repeatability permits.
2. Weigh finished dry envelope including all mounts that stay with it. Pass<=36.0g. A dimensioned photo is not a volume measurement.
3. Fill with supplier-stated>=99.5% helium at the supplier's allowed pressure, settle at room temperature, measure3orthogonal inflated axes. The ellipsoid estimate pi*a*b*c/6 is a diagnostic, not exact for wrinkled/pillow shapes. Obtain actual volume or rely on the net-lift measurement as primary acceptance.
4. Measure upward tension using a calibrated load cell or a secured tether to a calibrated force/scale fixture. Tare fixture/tether carefully; a kitchen scale does not directly measure upward pull without an appropriate fixture. Convert force to grams-equivalent once. Record NET standalone lift (after envelope mass), target>=85g at reference conditions. Do not subtract envelope mass twice.
5. Record again at1h,24h,48h,72h in controlled conditions. Target<=1g loss/24h after settling. Record temperature/pressure/humidity and deformation; observed buoyancy change is not automatically helium permeation. No leakage-rate prediction substitutes for this test.
6. Attach all hardware, satisfy GLOBAL<=78g hardware cap, then cold-trim to about1.5g negative buoyancy. Secure ballast; never eject it in flight. Verify gentle descent with motors off in a contained area. Overweight hardware/envelope fails receiving; do not compensate by depending on warmth.

## B. Media/electrical characterization
1. Record exact XIAO PCB, camera part (OV3660 vs OV5640), Arduino core, sensor driver version, sensor resolution/frame rate and Wi-Fi mode. Original Arduino firmware remains uncompiled/unflashed.
2. Begin USB-only with no battery/motors. Complete100snapshot requests and30record/playback cycles. Board-specific sensor initialization and full-duplex limits must be resolved, not hidden by host mock tests.
3. Change to a current-limited bench supply feeding intended BAT points, not3V3. Sweep3.5,3.7,4.2V. Test connection/reconnection, continuous video, mic capture, speaker playback, autofocus, simultaneous required operations and poor-signal retries. Record average/peak current and3V3 sag with adequate time resolution. The media budget is0.7A peak ALLOCATION, not a known sensor maximum.
4. Check complete stationary workload's battery-side average against the stated mission allocations; measure audio at usable conversational volume and1m listening distance. A silent or inaudible speaker is not a successful low-power test. Do not ground either bridge-tied amplifier output.
5. Check Wi-Fi home network and intended2.4GHz hotspot separately, with the antenna outside/near/away from the foil envelope. Test loss of Internet and Wi-Fi. No cloud dependency may hold a motor enabled.

## C. Current-limited guarded propulsion
1. Verify three0.82ohm sense resistors and removed sense-ground links. Check zero-power input defaults and repaired nSLEEP pull-up arrangement. Fit the actual flight props, full guards and mounts; weigh complete hardware.
2. With a suitable thrust stand, independently characterize EACH motor at3.5,3.7,4.2V, forward and reverse, PWM sweep, and the actual driver chopping configuration. Record thrust, input watts, winding current where measurable, temperature and noise. Initial acceptance objective:>=2g forward/reverse per horizontal motor and>=2g vertical thrust, without exceeding combined current limits. This objective may fail; the historical unguarded table does not establish it.
3. Perform controlled startup and brief blocked-rotor fault tests within component limits on the restrained bench. Verify firmware latch-off/manual rearm and guard integrity. Stop if there is overheating, wire damage, battery-protection trip or any exceedance of the rated envelope.
4. Combine motors with worst media workload. Target<=1.8A continuous at the pack and no out-of-spec transient, undervoltage reset or protection trip. Observe driver blanking spikes with suitable equipment. Do not infer compliance from average USB meter readings.

## D. Endurance and motion
Measure a COMPLETE battery discharge under the specified slow-roaming duty cycle, not only a5-minute extrapolation. Initial target>=2.5h with defined reserve and payload. Log watt-hours and cell voltage; low-voltage threshold must be validated for both regulators under peak load. Repeat at least3cycles.

Only after controller integration, run restrained or soft-contained low-speed motion trials at<=0.3m/s. Measure reverse thrust, stopping distance, altitude drift, loss-of-command response and real passive descent. Room-wide following/docking/obstacle avoidance are separate release gates. No unrestricted operation around children or reliance on simulated stopping distance.

## Empty measurement template

`reports/physical_measurements.csv` contains only its header. No measurements have been invented or inferred from simulated data.
