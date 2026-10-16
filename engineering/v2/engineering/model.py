"""Reproducible design calculations, NOT validated flight predictions. Python 3.10+.
No external packages. All mass inputs are dry (helium excluded) unless named otherwise.
"""
from dataclasses import dataclass, asdict
from pathlib import Path
import csv, itertools, json, math
G=9.80665
R_AIR=287.05
R_HE=2077.1
R_VAPOR=461.5


def positive(name, x):
    if not math.isfinite(x) or x <= 0:
        raise ValueError(f'{name} must be positive and finite')


@dataclass(frozen=True)
class Envelope:
    diameter_m: float=.62
    gores: int=12
    flange_m: float=.005  # allowance ON EACH of the two mating panel edges
    base_g_m2: float=13.94 # Capran PIR-MT1200 typical manufacturer basis weight
    sealant_um: float=8.0 # proposed laminate, NOT a sourced seal-ready material
    sealant_density_g_cm3: float=.92 # engineering assumption for PE
    adhesive_g_m2: float=2.0 # engineering allowance, entire laminate area
    valve_g: float=1.0 # allowance, includes neck
    reinforcement_g: float=1.5 # allowance, patches incl pole closure and attachments
    def __post_init__(self):
        for k,v in asdict(self).items():
            if not math.isfinite(v) or v<0: raise ValueError(k)
        positive('diameter',self.diameter_m)
        if not isinstance(self.gores,int) or self.gores<4: raise ValueError('gores')
    @property
    def area(self): return math.pi*self.diameter_m**2
    @property
    def volume_l(self): return math.pi*self.diameter_m**3/6*1000
    @property
    def seam_length(self): return self.gores*math.pi*self.diameter_m/2
    @property
    def seam_area(self): return 2*self.flange_m*self.seam_length
    @property
    def cut_area(self): return self.area+self.seam_area
    @property
    def basis(self): return self.base_g_m2+self.sealant_um*self.sealant_density_g_cm3+self.adhesive_g_m2
    @property
    def mass(self): return self.cut_area*self.basis+self.valve_g+self.reinforcement_g
    def breakdown(self):
        return dict(sphere_volume_l=self.volume_l,sphere_area_m2=self.area,
            seam_length_m=self.seam_length,seam_allowance_area_m2=self.seam_area,
            cut_area_m2=self.cut_area,laminate_basis_g_m2=self.basis,
            base_film_g=self.cut_area*self.base_g_m2,
            sealant_g=self.cut_area*self.sealant_um*self.sealant_density_g_cm3,
            adhesive_g=self.cut_area*self.adhesive_g_m2,
            valve_g=self.valve_g,reinforcement_g=self.reinforcement_g,envelope_g=self.mass)


def air_density(temp_c=20., pressure_pa=101325., rh=.5):
    """Ideal moist air + Tetens saturation approximation, intended 10-35 C.
    This is a fill-capacity comparison, not a sealed balloon thermal trajectory.
    """
    positive('temperature K',temp_c+273.15); positive('pressure',pressure_pa)
    if not 0<=rh<=1 or not -30<=temp_c<=50: raise ValueError('humidity/temperature range')
    pv=rh*610.78*math.exp(17.2694*temp_c/(temp_c+237.29))
    if pv>=pressure_pa: raise ValueError('vapor pressure')
    return (pressure_pa-pv)/(R_AIR*(temp_c+273.15))+pv/(R_VAPOR*(temp_c+273.15))


def gas_lift_g(volume_l,temp_c=20.,pressure_pa=101325.,rh=.5,purity=.995):
    positive('volume',volume_l)
    if not 0<=purity<=1: raise ValueError('purity')
    # impurity is ambient air at the same T/P; mol/volume-fraction approximation.
    return volume_l*purity*(air_density(temp_c,pressure_pa,rh)-pressure_pa/(R_HE*(temp_c+273.15)))


def gas_mass_g(volume_l,temp_c=20.,pressure_pa=101325.,rh=.5,purity=.995):
    return volume_l*air_density(temp_c,pressure_pa,rh)-gas_lift_g(volume_l,temp_c,pressure_pa,rh,purity)


# Whole-aircraft current and thrust from the manufacturer's FOUR-motor experiment.
# Do not interpret current below as motor winding current or as our limited-driver result.
RAW_THRUST=[
(.24,0,4.01,0),(.37,1.6,3.98,6.25),(.56,4.8,3.95,12.5),(.75,7.9,3.92,18.75),
(.94,10.9,3.88,25),(1.15,13.9,3.84,31.25),(1.37,17.3,3.80,37.5),
(1.59,21,3.76,43.25),(1.83,24.4,3.71,50),(2.11,28.6,3.67,56.25),
(2.39,32.8,3.65,62.5),(2.71,37.3,3.62,68.75),(3.06,41.7,3.56,75),
(3.46,46,3.48,81.25),(3.88,51.9,3.40,87.5),(4.44,57.9,3.30,93.75)]


def interpolate(x,xs,ys):
    if not math.isfinite(x) or x<xs[0] or x>xs[-1]: raise ValueError('outside calibrated proxy range')
    for i in range(1,len(xs)):
        if x<=xs[i]:
            a=(x-xs[i-1])/(xs[i]-xs[i-1])
            return ys[i-1]+a*(ys[i]-ys[i-1])
    return ys[-1]


def motor_power_proxy(thrust_g, thrust_eff=.75, baseline='current'):
    """Provisional incremental per-motor watts inferred from old four-motor data.
    Guards/voltage/driver mismatch represented ONLY by explicit thrust_eff assumption.
    Current chopping can alter these curves: do NOT use this as flight release evidence.
    """
    if not 0<thrust_eff<=1: raise ValueError('thrust_eff')
    xs=[r[1]/4 for r in RAW_THRUST]
    if baseline=='current': ys=[max(0,(r[0]-.24)*r[2]/4) for r in RAW_THRUST]
    elif baseline=='power': ys=[max(0,(r[0]*r[2]-.24*4.01)/4) for r in RAW_THRUST]
    else: raise ValueError('baseline')
    return interpolate(thrust_g/thrust_eff,xs,ys)


def drag_n(speed_m_s,diameter_m=.62,cd=.6,rho=None):
    if not math.isfinite(speed_m_s): raise ValueError('speed')
    positive('diameter',diameter_m);positive('cd',cd)
    rho=air_density() if rho is None else rho
    positive('density',rho)
    return .5*rho*cd*math.pi*diameter_m**2/4*speed_m_s*abs(speed_m_s)


def runtime_h(ah,watts,usable=.75,nominal_v=3.7):
    for k,v in [('capacity',ah),('watts',watts),('voltage',nominal_v)]:positive(k,v)
    if not 0<usable<=1: raise ValueError('usable')
    return ah*nominal_v*usable/watts


def mission(speed=.3,moving_fraction=.3,base_w=.95,trim_g=1.5,
            thrust_eff=.75,extra_corrections_w=.2,diameter=.62,cd=.6):
    if not 0<=moving_fraction<=1: raise ValueError('duty')
    hthrust=abs(drag_n(speed,diameter,cd))/G*1000/2
    vertical=motor_power_proxy(trim_g,thrust_eff)
    horizontal=2*motor_power_proxy(hthrust,thrust_eff)
    p=base_w+vertical+horizontal*moving_fraction+extra_corrections_w
    return dict(speed_m_s=speed,moving_fraction=moving_fraction,trim_g=trim_g,
       horizontal_thrust_per_motor_g=hthrust,vertical_power_proxy_w=vertical,
       moving_horizontal_power_proxy_w=horizontal,total_power_proxy_w=p,
       runtime_2000mah_h=runtime_h(2,p),
       status='PROXY ONLY; measured current-limited thrust and onboard workload required')


def effective_mass_kg(volume_l=120.,negative_trim_g=1.5,added_mass_coefficient=.5):
    # near-neutral all-up mass includes helium + ballast; displaced air + negative trim.
    displaced=volume_l/1000*air_density()
    return displaced*(1+added_mass_coefficient)+negative_trim_g/1000


def braking(speed=.3,reverse_thrust_g=4.,latency_s=.3,dt=.001,diameter=.62):
    """1D numerical stop: latency = maintained speed, then reverse thrust + quadratic drag.
    Force limit ASSUMED, not measured with guards/current limits. Not 6-DOF/CFD.
    """
    for k,v in [('speed',speed),('thrust',reverse_thrust_g),('dt',dt)]:positive(k,v)
    if latency_s<0:raise ValueError('latency')
    mass=effective_mass_kg(); f=reverse_thrust_g*G/1000
    v=speed;x=speed*latency_s;t=latency_s
    while v>0 and t<120:
        a=(f+drag_n(v,diameter))/mass
        h=min(dt,v/a)
        new_v=max(0,v-a*h)
        x+=(v+new_v)/2*h;v=new_v;t+=h
    k=drag_n(1.,diameter)
    exact=speed*latency_s+mass/(2*k)*math.log(1+k*speed**2/f)
    return dict(speed_m_s=speed,stop_distance_m=x,stop_time_s=t,
        analytic_distance_m=exact,effective_mass_kg=mass,reverse_thrust_assumed_g=reverse_thrust_g,
        latency_s=latency_s)


def current_budget(rs=.82,resistor_tol=.01,media_a=.7,other_a=.12):
    positive('rs',rs)
    if not 0<=resistor_tol<1:raise ValueError('resistor_tol')
    lo=.160/(rs*(1+resistor_tol));hi=.240/(rs*(1-resistor_tol))
    return dict(resistor_ohm=rs,trip_nominal_a=.2/rs,trip_min_a=lo,trip_max_a=hi,
        three_motor_trip_sum_a=3*hi,allocated_media_a=media_a,allocated_other_a=other_a,
        static_current_envelope_a=3*hi+media_a+other_a,
        caveat='25 C datasheet trip limits; not a bound on startup/blanking transients. Media cap unverified.')


PARTS=[
# name, qty, nominal unit g, allowed installed line g, mass evidence, source
('XIAO ESP32S3 Sense + antenna',1,5.,5.5,'installed allocation; camera revision unresolved','https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/'),
('XIAO nRF52840 Sense with IMU',1,3.,3.5,'installed allocation','https://wiki.seeedstudio.com/XIAO_BLE/'),
('Adafruit 2011 protected 2000mAh pack',1,34.,35.0,'manufacturer nominal; receiving limit allocated','https://www.adafruit.com/product/2011'),
('Bitcraze 7x16mm motors',3,2.7,8.4,'manufacturer nominal includes connector','https://www.bitcraze.io/documentation/hardware/motor_7mm/motor_7mm-datasheet.pdf'),
('Pololu 2130 DRV8833 carriers',2,1.,2.2,'manufacturer bare boards; no headers','https://www.pololu.com/product/2130/specs'),
('Adafruit 3006 MAX98357A amplifier',1,1.2,1.3,'manufacturer bare board','https://www.adafruit.com/product/3006'),
('Adafruit 3923 8ohm 1W speaker',1,3.,3.2,'manufacturer nominal; out of stock','https://www.adafruit.com/product/3923'),
('Pololu 3415 VL53L1X carrier',1,.5,.6,'manufacturer bare board; no headers','https://www.pololu.com/product/3415/specs'),
('47-17 props + mounts + full guards',1,5.5,6.0,'installed allocation, NOT a safety certification','https://store.bitcraze.io/collections/spare-parts/products/propeller-47-17-black'),
('Balsa/foam frame and speaker baffle',1,3.,3.5,'fabrication allowance','engineering allocation'),
('Wiring + contacts + power-off interlock',1,5.,5.5,'fabrication allowance; no airborne charger/boost','engineering allocation'),
('Current sense, switch, filtering, insulation',1,2.,2.5,'fabrication allowance; current monitoring on test bench','engineering allocation'),
('Unallocated integration reserve',1,4.,4.,'budget only, not physically installed mass','engineering reserve')]


def hardware_mass():return sum(x[1]*x[2] for x in PARTS)
def hardware_limit():return sum(x[3] for x in PARTS)


def run(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    e=Envelope()
    grid=[]
    for d in [.50,.55,.60,.62,.65]:
        env=Envelope(diameter_m=d)
        for ah,bg in [(.5,10.5),(1.2,23.),(2.,34.)]:
            hw=hardware_mass()-34+bg
            # shape factor .96 is a scenario assumption; not inferred from gore count
            vol=env.volume_l*.96;lift=gas_lift_g(vol)
            grid.append(dict(diameter_m=d,capacity_ah=ah,envelope_g=env.mass,
              hardware_g=hw,cold_volume_l=vol,gas_lift_g=lift,untrimmed_margin_g=lift-hw-env.mass,
              runtime_at_1p8w_h=runtime_h(ah,1.8)))
    write_csv(output/'diameter_battery_sweep.csv',grid)
    stack=[]
    for seal,adh in itertools.product([6.,8.,10.,12.,15.],[1.,2.,3.]):
        ee=Envelope(sealant_um=seal,adhesive_g_m2=adh)
        stack.append(dict(sealant_um=seal,adhesive_g_m2=adh,envelope_mass_g=ee.mass,
            passes_36g=ee.mass<=36))
    write_csv(output/'laminate_sweep.csv',stack)
    corners=[]
    # Deterministic boundary combinations, NOT a probability distribution.
    for vol,env,hw,tc,p,rh,pur in itertools.product([120.,124.79],[30.,36.],
        [hardware_mass(),hardware_limit()],[18.,27.],[100000.,102000.],[.3,.7],[.99,.999]):
        lift=gas_lift_g(vol,tc,p,rh,pur)
        corners.append(dict(volume_l=vol,envelope_g=env,hardware_g=hw,temperature_c=tc,
            pressure_pa=p,rh=rh,purity=pur,gas_lift_g=lift,untrimmed_margin_g=lift-env-hw))
    write_csv(output/'mass_corners.csv',corners)
    props=[dict(current_a=r[0],total_four_motor_thrust_g=r[1],voltage_v=r[2],pwm_percent=r[3],
       per_motor_thrust_g=r[1]/4,incremental_per_motor_power_w=(r[0]-.24)*r[2]/4) for r in RAW_THRUST]
    write_csv(output/'manufacturer_thrust_proxy.csv',props)
    missions=[mission(speed=.15,moving_fraction=.1,base_w=.75,extra_corrections_w=.1),
              mission(),mission(speed=.6,moving_fraction=.75,base_w=1.2,extra_corrections_w=.4)]
    speeds=[dict(speed_m_s=v,drag_g=drag_n(v)/G*1000,drag_power_w=drag_n(v)*v) for v in [.15,.3,.5,.6,1.]]
    write_csv(output/'drag_sweep.csv',speeds)
    stops=[braking(v) for v in [.15,.3,.5,.6,1.]]
    write_csv(output/'braking_sweep.csv',stops)
    summary=dict(status='Numerical models and specification audit only; no physical tests',
        envelope=e.breakdown(),hardware_nominal_g=hardware_mass(),hardware_acceptance_sum_g=hardware_limit(),
        dry_nominal_g=hardware_mass()+e.mass,filled_lift_120L_g=gas_lift_g(120.),
        margin_at_120L_g=gas_lift_g(120)-hardware_mass()-e.mass,
        corners_count=len(corners),corners_worst=min(corners,key=lambda x:x['untrimmed_margin_g']),
        corners_best=max(corners,key=lambda x:x['untrimmed_margin_g']),
        current=current_budget(),missions=missions,braking=stops,
        energy=dict(nominal_wh=7.4,usable_fraction=.75,usable_wh=5.55,
            runtime_by_load={str(p):runtime_h(2,p) for p in [1.2,1.5,1.8,2.,2.8,3.]}),
        fleet=dict(charge_current_a=.5,assumed_charge_turnaround_h=4.,
           active_runtime_at_1p8W_h=runtime_h(2,1.8),one_active_units=math.ceil(1+4/runtime_h(2,1.8))))
    (output/'results.json').write_text(json.dumps(summary,indent=2)+'\n')
    write_csv(output/'component_mass.csv',[dict(component=p[0],qty=p[1],unit_mass_g=p[2],
        line_mass_g=p[1]*p[2],acceptance_line_g=p[3],basis=p[4],source=p[5]) for p in PARTS])
    print(json.dumps(summary,indent=2))


def write_csv(path,rows):
    with open(path,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


if __name__=='__main__': run(Path(__file__).resolve().parents[1]/'reports')
