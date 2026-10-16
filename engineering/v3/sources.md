# Primary-source ledger — checked 15 October 2026

Published values are not receiving-inspection results. Stock is a snapshot, not a reservation. No supplier has accepted a specification or order.

| ID | Source | Used for | Limitation |
|---|---|---|---|
| S01 | https://www.advansix.com/wp-content/uploads/2023/02/Capran-PIR-MT1200-TDS.pdf | 12 µm metallized nylon, 13.94 g/m²; balloon application reference | Not a finished heat-sealable envelope; oxygen data do not establish helium retention |
| S02 | https://www.advansix.com/wp-content/uploads/2023/02/Films-Handling-Guide-for-Converting-Industry-Eng.pdf | Moisture uptake, conditioning, surface treatment and conversion cautions | No quantitative humidity-to-lift model supplied |
| S03 | https://multimedia.3m.com/mws/media/2366204O/3m-adhesive-transfer-tape-467mp.pdf | 60 µm transfer-adhesive candidate; liner excluded | Density 1 g/cm³ is our assumption; nylon adhesion and helium leakage unqualified |
| S04 | https://www.toraytpa.com/wp-content/uploads/2019/06/TFN-PMX2-Technical-Data-Sheet-Metric.pdf | Torayfan PMX2 15 µm, 73.3 m²/kg, integrated sealing surface and metallization | Packaging film; standalone helium retention, damage tolerance and sample stock unverified |
| S05 | https://www.celplast.com/product-type/standard-barrier-metallized-films/ | CEL-MET heat-sealable metallized PET, 12 µm option | Converter sample/MOQ inquiry required |
| S06 | https://www.celplast.com/wp-content/uploads/2013/04/CEL-MET-HS-PET_48-120.pdf | Parsed 41,900 in²/lb yield for thinnest option | PDF image retrieval blocked; numeric yield/full construction must be confirmed before final mass commitment |
| S07 | https://micronwings.com/product/gearbox-6mm-ball-raced/ | 2.33 g motor/gearbox; supplier's GWS4025/4040 tests; 0.97 mm shaft | No prop connector included; no low-thrust, reversed, guarded or current-limited map; 11 listed in stock |
| S08 | https://www.bitcraze.io/documentation/repository/crazyflie-firmware/master/functional-areas/pwm-to-thrust/ | Historical four-motor current/thrust data | Power supply/fixture/voltage differ; only a screening proxy for our assembly |
| S09 | https://www.bitcraze.io/documentation/hardware/motor_7mm/motor_7mm-datasheet.pdf | Baseline 7 × 16 mm motor, 2.7 g | Controller and guard performance unmeasured |
| S10 | https://eaglepubs.erau.edu/introductiontoaerospaceflightvehicles/chapter/vtol-aircraft/ | Momentum-theory static induced-power lower bound | Not total electrical power or a low-Reynolds propeller performance prediction |
| S11 | https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/ | Camera/mic/network board; camera revisions and power examples | OV5640 power table incomplete; exact shipped hardware must be identified |
| S12 | https://www.seeedstudio.com/Seeed-Studio-XIAO-nRF52840-Sense-Plus-p-6360.html | Sense Plus variant, additional bottom GPIO pads; $16.99, listed in stock | Installed mass and firmware compatibility need verification |
| S13 | https://wiki.seeedstudio.com/XIAO_BLE/ | Physical GPIO, onboard motion sensor and power inputs | Arduino numeric aliases differ between cores; do not treat physical names as compiled constants |
| S14 | https://www.pololu.com/product/2130 | DRV8833 dual carrier; disabled-by-default current limiting | Board modification and default-off behavior require physical inspection; stock not established by add-to-cart alone |
| S15 | https://www.ti.com/lit/ds/symlink/drv8833.pdf | Threshold/current formula and 25°C tolerance | Winding-current thresholds are not a battery transient-current guarantee |
| S16 | https://www.adafruit.com/product/2011 | Protected 2 Ah, 34 g pack | Manufacturer out of stock; use exact distributor SKU, not a generic replacement |
| S17 | https://cdn-shop.adafruit.com/datasheets/LiIon2000mAh37V.pdf | Minimum 1.9 Ah capacity and 2 A continuous-discharge limit used in v2 | Receiving pack must match this datasheet |
| S18 | https://www.digikey.com/en/products/detail/adafruit-industries-llc/2011/6612469 | Exact battery SKU 1528-1857-ND, $12.50, listed in stock | Ground shipping restriction; stock count varies |
| S19 | https://puiaudio.com/file/specs-AS01808AO-SC18-WP-R.pdf | 1.8 g, 8 Ω, 1 W speaker; sensitivity conditioned on 1 cc back-volume | Source says 96 dB at 0.1 m, not 1 m; does not establish complete robot speech quality |
| S20 | https://www.digikey.com/en/products/detail/pui-audio-inc/AS01808AO-SC18-WP-R/9687113 | Exact speaker, $4.86, listed in stock | Distributor parametric sensitivity differs from newer manufacturer sheet; use exact delivered revision |
| S21 | https://www.adafruit.com/product/3006 | MAX98357A carrier reference | Gain, clipping, input rail, mounting and aggregate media current must be measured |
| S22 | https://www.pololu.com/product/3415 | Downward VL53L1X carrier reference | Not a 360-degree collision sensor or a horizontal localization solution |
| S23 | https://media.digikey.com/pdf/Data%20Sheets/Murata%20PDFs/MZB1001T02_DS.pdf | Ballonet research lead: 1.4±0.2 g bare pump; specified pressure/flow test conditions | Requires drive circuit, valves, pressure sensing and constrained outer volume; bare pump mass is not subsystem mass |
| S24 | https://www.murata.com/en-us/products/mechatronics/fluid | Current microblower lineup | Max-flow and static-pressure numbers cannot be used simultaneously |
| S25 | https://www.theleeco.com/disc-pumps/ | Alternative micropump architecture | Not included in recommended first prototype |

Only short numeric extracts and paraphrases are embedded; manufacturer documents are linked, not republished.
