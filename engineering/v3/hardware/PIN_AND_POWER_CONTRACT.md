# Preliminary pin / power contract — NOT flashed or hardware verified

## Controller allocation

Use the XIAO nRF52840 **Sense Plus**, not the standard Sense pinout. Physical labels below are not assumed Arduino numeric constants. Confirm port mappings in the selected board support package and continuity on the delivered board before assigning signals.

| Function | Proposed physical pads |
|---|---|
| Forward motor A inputs | D0, D1 |
| Forward motor B inputs | D2, D3 |
| Lateral motor inputs | D8, D9 |
| Vertical motor inputs | D10, D11 |
| External I²C | D4 SDA, D5 SCL |
| Media-controller UART | D6 TX, D7 RX |
| Shared driver sleep | D12 |
| Wired fault input | D13 |

The Plus exposes additional bottom pads; access requires a real soldered harness/carrier, whose mass must fit the allocation. The eight bridge inputs need correct PWM/direction timing. Do not connect motor power while identifying pins. Verify IMU operation and onboard resources under the selected core. Roll and pitch are passively stabilized, not independent controlled-force axes.

## Sense/media allocation

Reserve native camera and microphone pins. Use exposed D1/D2/D3 for speaker I²S only after checking the exact board/camera examples and boot behavior. UART D6/D7 communicates signed low-level commands to the independent controller. Do not reuse camera GPIO39/40, microphone GPIO41/42, or SD pins accidentally. SD storage is optional and not required for first flight.

## Power

Single protected 3.7 V nominal pack feeds appropriate BAT inputs and rated peripherals; no assumption that every board accepts the cell through its 3V3 pad. Keep USB, board charging paths and external dock charger isolated. The first charge connection is manual with the flying loads disconnected. No unattended charging or fleet operation is qualified.

Two DRV8833 boards provide four channels. On the Pololu board the sense links must be opened and sense resistors installed. For four channels, 1.00 Ω, 1%, 1206, ≥0.25 W is a bench starting point. Using 160–240 mV trip thresholds at 25°C gives approximately 0.158–0.242 A per winding. The proposed static envelope is 4×0.242 + 0.70 A media + 0.12 A other ≈1.79 A; startup/blanking/current ripple and rail sag must be observed with an appropriate current probe/shunt and oscilloscope.

A 0.82 Ω resistor, previously budgeted for three motors, would produce a four-channel static allocation just over 2 A. Do not silently retain it when adding the fourth motor. Conversely, the more restrictive limit may prevent required thrust: the thrust test decides.

Require hardware-default-disabled motor power, verified bridge coast/brake behavior, fault monitoring, watchdog timeout, bounded command duration and a physical kill switch. The LLM never commands raw unbounded motor duty. Networking/localization failure must enter a tested recovery state; “motors off” on a nearly neutral balloon is not guaranteed station keeping.

## Navigation and RF limitations

The downward rangefinder and six-axis IMU do not determine room x/y position or observe obstacles in every direction. Crosswind simulations use perfect pose data. First test a supervised fiducial/external-camera room with a local computer; no household-wide autonomous navigation is implied.

Keep the antenna outside the metallized envelope. Measure packet loss, latency and RSSI over orientation, camera operation and motor commutation. Verify home Wi-Fi first, then the actual phone's 2.4 GHz hotspot and phone/hub reachability. Neither radio link nor flight safety depends on cloud/LLM response timing.
