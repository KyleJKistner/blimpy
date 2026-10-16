"""Declarative interface review. Passing these checks is NOT hardware validation."""
MEDIA_PINS={
'amp_shutdown':2,'speaker_bclk':7,'speaker_ws':8,'speaker_data':9,
'mic_clock':42,'mic_data':41,'uart_tx':43,'uart_rx':44,
'camera_xclk':10,'camera_pclk':13,'camera_vsync':38,'camera_href':47,
'camera_sda':40,'camera_scl':39,'camera_d0':15,'camera_d1':17,'camera_d2':18,
'camera_d3':16,'camera_d4':14,'camera_d5':12,'camera_d6':11,'camera_d7':48,
'privacy_led':21}
SAFETY_PINS={'left_in1':'D0','left_in2':'D1','right_in1':'D2','right_in2':'D3',
 'tof_sda':'D4','tof_scl':'D5','driver_fault':'D6','command_uart_rx':'D7',
 'vertical_in1':'D8','vertical_in2':'D9','motor_enable':'D10'}
# Initial safety link is receive-only UART. D6 reads common open-drain driver faults.
# No flight telemetry return is implemented. ESP GPIO44 remains unused/reserved.
# LSM6DS3 uses the nRF board's internal bus, not the external D4/D5 pins.
# Battery ADC uses internal pins; official Seeed caveat for P0.14 must be followed.
BAT_RAIL=(3.5,4.2) # proposed acceptance operating range, not battery protection cutoff
DEVICES={'MAX98357A':(2.5,5.5),'DRV8833':(2.7,10.8),'VL53L1X_carrier':(2.6,5.5)}

def unique_pins(pins):return len(set(pins.values()))==len(pins)
def rail_compatible(rail,device_range):return device_range[0]<=rail[0] and rail[1]<=device_range[1]

def review(sd_enabled=False,current_limit_enabled=True,separate_chargers_connected=False):
    issues=[]
    if not unique_pins(MEDIA_PINS):issues.append('media GPIO collision')
    if not unique_pins(SAFETY_PINS):issues.append('safety GPIO collision')
    if sd_enabled:issues.append('SD SPI conflicts with speaker I2S GPIO7/8/9')
    if not current_limit_enabled:issues.append('DRV8833 carrier default current limiting DISABLED')
    if separate_chargers_connected:issues.append('parallel chargers prohibited: disconnect load and USB before dock charge')
    for name,limits in DEVICES.items():
        if not rail_compatible(BAT_RAIL,limits):issues.append(name+' supply range mismatch')
    return issues
