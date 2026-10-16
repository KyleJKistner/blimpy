# Primary-source ledger — checked 15 October 2026

Links are evidence for individual inputs, not proof that the assembled robot works. Retail stock and hardware revisions can change. No manufacturer datasheets are redistributed in this package.

1. AdvanSix Capran PIR-MT1200 technical data: https://www.advansix.com/wp-content/uploads/2023/02/Capran-PIR-MT1200-TDS.pdf
   - Page1 table visually checked: typical13.94g/m2,12um,thickness+/-5%, metallized nylon6, balloon application. No finished seal layer; no helium transmission specification. PE8um,density0.92,adhesive2g/m2,neck/valve1g and reinforcement1.5g are engineering assumptions.
2. Seeed XIAO ESP32S3 official introduction: https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/
   - Current camera shipment may beOV3660 orOV5640. OV5640 current comparison isTBD. Older web-camera measurement3.8V/155mAaverage/366mApeak cannot be applied as a new-camera bound. Direct1S BAT operation; integrated camera,mic,Wi-Fi.
3. Seeed ESP32S3 v1.5 schematic: https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/new-res/202003753_XIAO%20ESP32S3%20Sense_v1.5_SCH_260226.pdf.pdf
   - Pages3-4 visually inspected: BAT path and3V3 regulator; board has an onboard charger. Component revision must be recorded.
4. Seeed XIAO nRF52840 documentation: https://wiki.seeedstudio.com/XIAO_BLE/
   - Sense version's integrated IMU; BAT operation; internal battery-ADC caveat: follow official P0.14 guidance, do not drive it high when measuring/charging.
5. Seeed nRF52840 schematic: https://files.seeedstudio.com/wiki/XIAO-BLE/Seeed_Studio_XIAO_nRF52840_PDF.pdf
   - Page3 inspected: internal IMU bus, external GPIO mapping, LDO and charger. Board mass remains an installed allocation.
6. XIAO nRF52840 Sense product (SKU102010469): https://www.seeedstudio.com/Seeed-XIAO-BLE-Sense-nRF52840-p-5253.html
7. Adafruit2011 battery product: https://www.adafruit.com/product/2011
   - Nominal34g,3.7V,2000mAh. Product recommends500mA-or-less charging. Verify supplied pack model against linked datasheet.
8. Linked LP803860 pack datasheet: https://cdn-shop.adafruit.com/datasheets/LiIon2000mAh37V.pdf
   - Page2 visually inspected: nominal2000/minimum1900mAh,1C maximum continuous discharge,4.2V charge,3.0V discharge cutoff,charge0-45C. A product-level robot cutoff must leave adequate regulator/current margin.
9. Bitcraze7mm motor datasheet: https://www.bitcraze.io/documentation/hardware/motor_7mm/motor_7mm-datasheet.pdf
   - 7x16mm,0.8mm shaft,2.7g including connector,4.2V,1000mA rating. Do not confuse with different newer high-thrust7mm variants.
10. Bitcraze PWM-to-thrust experiment: https://www.bitcraze.io/documentation/repository/crazyflie-firmware/master/functional-areas/pwm-to-thrust/
    -2015 FOUR-motor measured table transcribed inreports/manufacturer_thrust_proxy.csv.0.24A zero-thrust baseline. Different driver/guards/reverse/current limit invalidate direct performance transfer.
11. Pololu2130 motor carrier: https://www.pololu.com/product/2130
    - Sense links grounded by default,current limiting disabled,1206resistor pads,3V-compatible input,nSLEEP pulled HIGH. Schematic shows47k pull-up. Manufacturer bare mass1g: https://www.pololu.com/product/2130/specs
12. TI DRV8833 datasheet: https://www.ti.com/lit/ds/symlink/drv8833.pdf
    - Page7 visually inspected:160/200/240mV trip at25C,3.75us blanking. Supply2.7-10.8V. Current chopping is winding-current control, not a general battery-current limiter.
13. AdafruitMAX98357A: https://www.adafruit.com/product/3006
    - Bare board mass1.2g. IC supply details: https://www.analog.com/media/en/technical-documentation/data-sheets/max98357a-max98357b.pdf
    -2.5-5.5V supply; class-D bridge output; quoted92% efficiency at1W is not assumed at all loads.
14. Adafruit3923 speaker: https://www.adafruit.com/product/3923
    -8ohm,1W,3g,30x20x5mm; OUT OF STOCK at review. Reference selection only until sourced. DigiKey lists it as available to order, not stocked; no immediate delivery is assumed. Distributor listing: https://www.digikey.com/en/products/detail/adafruit-industries-llc/3923/9658610
15. Pololu3415 rangefinder: https://www.pololu.com/product/3415/specs
    -0.5g bare,2.6-5.5V,20mAtypical/40mApeak. Not a complete localization solution.
16. Matching prop family: https://store.bitcraze.io/collections/spare-parts/products/propeller-47-17-black
17. External dock charger: https://www.adafruit.com/product/6091
    -bq25185 module: configure500mA,do not use shipping1A setting with the prescribed charging plan; correct battery temperature sensing required.

## Model assumptions not sourced measurements

12gores,5mmseam allowance per mating edge,PE/adhesive layer stack,valve/reinforcement allocation,actualvolume120L,shape0.96 in diameter sweep,ambient range18-27C/100-102kPa/30-70%RH,gas purity99-99.9%,Cd0.6,added-fluid-mass coefficient0.5,guard/installation thrust efficiency0.75,3.5-4.2V operating acceptance interval,media peak0.7A,other peak0.12A,mission-average watt allocations,4g total reverse force,0.3s latency,75%usable battery energy,4hcharging turnaround.

The material's published thickness tolerance is not a guarantee on a finished fabricated assembly. The deterministic corners are stress scenarios, not Bayesian posterior probabilities.
