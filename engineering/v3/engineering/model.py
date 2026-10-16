"""Helium companion v3: auditable reduced-order design exploration.

No physical measurements were performed. Empirical motor data are supplier data,
not measurements of the proposed assembly. Scenario sweeps are not probabilities.
SI internally except explicitly named gram, litre, and hour interfaces.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import csv
import importlib.util
import json
import math
import sys
from typing import Sequence
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
from scipy.special import ellipe

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('v2_reference', ROOT/'reference/v2_model.py')
v2 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = v2
spec.loader.exec_module(v2)
G = 9.80665


def require_positive(name: str, x: float) -> None:
    if not math.isfinite(x) or x <= 0:
        raise ValueError(f'{name} must be positive and finite')


@dataclass(frozen=True)
class SeamEnvelope:
    diameter_m: float = .62
    gores: int = 12
    flange_m: float = .005
    barrier_g_m2: float = 13.94
    seam_adhesive_um: float = 60.
    adhesive_density_g_cm3: float = 1.0  # ASSUMED; vendor does not give this
    neck_and_patches_g: float = 2.5

    def __post_init__(self):
        for k, x in asdict(self).items():
            require_positive(k, x)
        if not isinstance(self.gores, int) or self.gores < 4:
            raise ValueError('at least four integer gores required')

    def breakdown(self) -> dict:
        sphere_area = math.pi*self.diameter_m**2
        seam_length = self.gores*math.pi*self.diameter_m/2
        # Two flanges are present in the film; ONE adhesive layer at their interface.
        cut_area = sphere_area + 2*self.flange_m*seam_length
        interface_area = self.flange_m*seam_length
        barrier_mass = cut_area*self.barrier_g_m2
        adhesive_mass = interface_area*self.seam_adhesive_um*self.adhesive_density_g_cm3
        return dict(diameter_m=self.diameter_m, sphere_volume_l=math.pi*self.diameter_m**3/6*1000,
            sphere_area_m2=sphere_area, seam_length_m=seam_length,
            cut_area_m2=cut_area, interface_area_m2=interface_area,
            barrier_g=barrier_mass, adhesive_g=adhesive_mass,
            closures_g=self.neck_and_patches_g,
            total_g=barrier_mass+adhesive_mass+self.neck_and_patches_g)



def factory_film_envelopes():
    """Published film yields; closure masses and geometry remain engineering allocations.
    Helium permeability/finished shape NOT established by these specifications.
    CEL-MET numeric yield is provisional pending visual/vendor confirmation of table.
    """
    cut=SeamEnvelope().breakdown()['cut_area_m2']
    films=[('Torayfan PMX2 15um',1000/73.3,'manufacturer metric yield; helium untested'),
           ('CEL-MET HS PET 0.48mil',453.59237/(41900*.0254**2),
            'parsed manufacturer yield; PDF image blocked, confirm full-film basis weight')]
    return [dict(material=n,complete_film_g_m2=basis,cut_area_m2=cut,closures_g=2.5,
                 envelope_g=cut*basis+2.5,helium_qualified=False,evidence=e) for n,basis,e in films]

def membrane_stress(pressure_pa: float, diameter_m=.62, film_um=12.) -> dict:
    """Pristine spherical membrane equation. NOT a seam/creep/burst qualification."""
    if not math.isfinite(pressure_pa) or pressure_pa < 0:
        raise ValueError('invalid pressure')
    require_positive('diameter', diameter_m); require_positive('thickness', film_um)
    line_load = pressure_pa*diameter_m/4
    return dict(pressure_pa=pressure_pa, line_load_n_m=line_load,
                ideal_film_stress_mpa=line_load/(film_um*1e-6)/1e6)


def ideal_static_power(thrust_g: float, diameter_m: float, rho: float | None = None) -> float:
    """Actuator-disk lower bound, excluding profile, motor, gear and guard losses."""
    if not math.isfinite(thrust_g) or thrust_g < 0: raise ValueError('negative thrust')
    require_positive('rotor diameter', diameter_m)
    rho = v2.air_density() if rho is None else rho
    require_positive('air density', rho)
    f = thrust_g*G/1000
    return f**1.5/math.sqrt(2*rho*math.pi*diameter_m**2/4)


def manufacturer_comparison(thrust_g=13.6, voltage_v=3.8, current_a=.420) -> dict:
    """Different manufacturers/fixtures/voltages; a screening comparison only."""
    geared = voltage_v*current_a
    historical = v2.motor_power_proxy(thrust_g, thrust_eff=1.0)
    return dict(thrust_g=thrust_g, geared_supplier_electrical_w=geared,
                historical_incremental_proxy_w=historical,
                ratio_historical_to_geared=historical/geared,
                geared_supplier_g_per_w=thrust_g/geared,
                historic_g_per_w=thrust_g/historical,
                evidence='Cross-fixture screening; NOT an A/B efficiency measurement')


def thermal_state(gas_c: float, ambient_c=20., ambient_pa=101325., rh=.5,
                  fill_l=120., fill_c=20., fill_pa=101325., fill_rh=.5,
                  purity=.995, max_volume_l=None) -> dict:
    """Conserved gas: negligible overpressure while slack, hard volume cap when taut.
    Ignores envelope compliance, leak, stratification and mechanical hysteresis.
    A hard-cap overpressure is a RED FLAG calculation, not permissible operation.
    """
    max_volume_l = math.pi*.62**3/6*1000 if max_volume_l is None else max_volume_l
    for k, x in [('fill',fill_l),('max volume',max_volume_l),('gas K',gas_c+273.15),
                 ('fill K',fill_c+273.15),('ambient P',ambient_pa),('fill P',fill_pa)]:
        require_positive(k,x)
    if fill_l > max_volume_l: raise ValueError('initial fill exceeds volume cap')
    mass_g = v2.gas_mass_g(fill_l, fill_c, fill_pa, fill_rh, purity)
    target_l = fill_l*(gas_c+273.15)/(fill_c+273.15)*fill_pa/ambient_pa
    actual_l = min(target_l, max_volume_l)
    inside_pa = fill_pa*fill_l*(gas_c+273.15)/(fill_c+273.15)/actual_l
    lift_g = v2.air_density(ambient_c,ambient_pa,rh)*actual_l - mass_g
    return dict(gas_c=gas_c, ambient_c=ambient_c, target_volume_l=target_l,
                actual_volume_l=actual_l, internal_pressure_pa=inside_pa,
                gauge_pressure_pa=max(0,inside_pa-ambient_pa), gas_mass_g=mass_g,
                lift_g=lift_g, taut=target_l>=max_volume_l)


def ballonet_lower_bound(added_air_g: float, outer_volume_l=120., ambient_c=20.,
                        ambient_pa=101325., rh=.5) -> dict:
    """Pressure ballast in FIXED outer volume. Starts with pure gas at ambient P.
    Air density and intake-volume relation include assumed ambient humidity.
    Pump work: reversible isothermal compression of incoming air, above ambient.
    No thermal effects, compliance, valves, driver losses, or pump maps.
    """
    if not math.isfinite(added_air_g) or added_air_g < 0: raise ValueError('air mass')
    require_positive('volume',outer_volume_l)
    rho=v2.air_density(ambient_c,ambient_pa,rh)
    intake_m3=added_air_g/1000/rho
    outer_m3=outer_volume_l/1000
    z=intake_m3/outer_m3
    ratio=1+z
    w=ambient_pa*outer_m3*((1+z)*math.log1p(z)-z)
    return dict(added_air_g=added_air_g, intake_l=intake_m3*1000,
                internal_air_volume_l=intake_m3/ratio*1000,
                gauge_pressure_pa=ambient_pa*z,
                reversible_pump_work_j=w,
                evidence='Theoretical lower bound; full subsystem mass/power unverified')


def allocation_matrix(layout='four', arm_m=.12) -> np.ndarray:
    """Rows: forward, lateral, vertical force, yaw torque. Roll/pitch NOT actuated.
    Twin forward motors at +/- lateral arm; lateral motor thrust line through CG;
    vertical motor line through CG. Force-sign convention is an ideal geometry.
    """
    require_positive('arm',arm_m)
    if layout=='three':
        return np.array([[1,1,0],[0,0,0],[0,0,1],[arm_m,-arm_m,0]],float)
    if layout=='four':
        return np.array([[1,1,0,0],[0,0,1,0],[0,0,0,1],
                         [arm_m,-arm_m,0,0]],float)
    raise ValueError('unknown layout')


def control_current(channels=4, sense_ohm=1., tol=.01, media_a=.7, other_a=.12):
    require_positive('sense resistor',sense_ohm)
    if not isinstance(channels,int) or channels < 1 or not 0<=tol<1:
        raise ValueError('channels or tolerance')
    trip=.240/(sense_ohm*(1-tol))
    return dict(channels=channels,sense_ohm=sense_ohm,max_trip_a=trip,
                static_allocated_a=channels*trip+media_a+other_a,
                evidence='25C threshold allocation, not startup-transient proof')


def crosswind(layout='four', wind_m_s=.3, final_s=60., dt=.02):
    """Reduced 1D lateral slice, yaw held fixed; perfect state sensing.
    Quadratic drag, constant added mass, instantaneous actuator command with hard limit.
    No walls, wake, camera navigation, actuator deadband or gust spectrum.
    Both branches integrate with RK4. Uncontrolled travel ends at wall in reality.
    """
    if layout not in ('three','four'): raise ValueError('layout')
    require_positive('dt',dt); require_positive('time',final_s)
    mass=v2.effective_mass_kg(120.,.3)
    force_limit=4*G/1000  # target to measure, not supplier-certified reverse thrust
    kp,kd,ki=.060,.160,.012
    def rhs(t,s):
        y,v,integral=s
        w=wind_m_s if t>=5 else 0.
        desired=-kp*y-kd*v-ki*integral if layout=='four' else 0.
        u=float(np.clip(desired,-force_limit,force_limit))
        # Conditional integration: do not wind up farther into saturation.
        iz=y if layout=='four' else 0.
        if abs(desired)>force_limit and desired*(-ki*iz)>0: iz=0.
        drag=-v2.drag_n(v-w)
        return np.array([v,(drag+u)/mass,iz])
    count=round(final_s/dt)
    ts=np.linspace(0,final_s,count+1)
    s=np.zeros(3); out=[]
    for n,t in enumerate(ts):
        desired=-kp*s[0]-kd*s[1]-ki*s[2] if layout=='four' else 0.
        out.append(dict(time_s=float(t),y_m=float(s[0]),vy_m_s=float(s[1]),
                        commanded_force_n=float(np.clip(desired,-force_limit,force_limit))))
        if n==count:break
        h=ts[n+1]-t
        k1=rhs(t,s);k2=rhs(t+h/2,s+h*k1/2)
        k3=rhs(t+h/2,s+h*k2/2);k4=rhs(t+h,s+h*k3)
        s+=h*(k1+2*k2+2*k3+k4)/6
    peak=max(abs(x['y_m']) for x in out)
    collision=next((x['time_s'] for x in out if abs(x['y_m'])>=1.),None)
    return dict(layout=layout,wind_m_s=wind_m_s,max_lateral_error_m=peak,
                final_lateral_error_m=float(s[0]),first_1m_travel_s=collision,
                force_limit_assumed_g=4.,perfect_state_sensing=True),out



def prolate_shape(aspect=1.5, equivalent_diameter_m=.62, gores=12, flange_m=.005):
    """Equal-volume prolate geometry. No claim of aerodynamic coefficient improvement.
    Meridian length uses the complete elliptic integral. Panels are not flattened CAD.
    """
    require_positive('equivalent diameter', equivalent_diameter_m)
    if not math.isfinite(aspect) or aspect<1: raise ValueError('prolate aspect >=1')
    width=equivalent_diameter_m/aspect**(1/3)
    length=aspect*width
    a,b=length/2,width/2
    e=math.sqrt(max(0,1-(b/a)**2))
    area=(4*math.pi*b*b if e<1e-8 else 2*math.pi*b*b*(1+a/(b*e)*math.asin(e)))
    meridian=2*a*float(ellipe(e*e))
    seams=gores*meridian
    cut=area+2*flange_m*seams
    mass=cut*13.94+flange_m*seams*60+2.5
    return dict(aspect=aspect, width_m=width, length_m=length,
         volume_l=4*math.pi*a*b*b/3*1000, surface_area_m2=area,
         seam_length_m=seams, seam_candidate_mass_g=mass,
         forward_projected_area_m2=math.pi*b*b,
         side_projected_area_m2=math.pi*a*b,
         area_ratio_to_sphere=area/(math.pi*equivalent_diameter_m**2),
         forward_area_ratio=(width/equivalent_diameter_m)**2,
         status='Geometry only; inflated axes, turn clearance and axis-dependent drag need measurement')

def minimum_diameter(hardware_g=80., reserve_g=3., variant='seam', adverse=True):
    """Separate fills; 96% spherical volume assumption, NOT measured panel geometry."""
    if variant not in ('full', 'seam', 'pmx2'):
        raise ValueError('unknown envelope construction')
    def surplus(d):
        volume_l=.96*math.pi*d**3/6*1000
        construction=SeamEnvelope(diameter_m=d).breakdown()
        if variant == 'seam':
            env=construction['total_g']
        elif variant == 'pmx2':
            env=construction['cut_area_m2']*(1000/73.3)+2.5
        else:
            env=v2.Envelope(diameter_m=d).mass
        lift=(v2.gas_lift_g(volume_l,27,100000,.7,.99) if adverse
              else v2.gas_lift_g(volume_l))
        return lift-hardware_g-env-reserve_g
    return brentq(surplus,.3,1.)


def write_csv(path, rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:raise ValueError('no rows')
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def ensure_measurement_template(path: Path):
    """Create only if absent: rerunning simulations must never erase measurements."""
    path=Path(path)
    if not path.exists():
        path.write_text('timestamp_utc,assembly_id,revision,test_id,value,unit,uncertainty,fixture_id,operator\n')


def run(output: Path):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    seam=SeamEnvelope().breakdown()
    films=factory_film_envelopes()
    write_csv(output/'factory_film_candidates.csv',films)
    shapes=[prolate_shape(a) for a in [1.,1.2,1.3,1.5,2.]]
    write_csv(output/'shape_sweep.csv',shapes)
    trim=[v2.mission(trim_g=t) for t in [0.,.1,.2,.3,.5,1.,1.5,2.,3.]]
    write_csv(output/'trim_sensitivity.csv',trim)
    lam=[]
    for g in [8,12,16]:
      for width in [.003,.005,.008]:
       for t in [50.,60.,70.]:
        for rho in [.9,1.,1.2]:
         e=SeamEnvelope(gores=g,flange_m=width,seam_adhesive_um=t,adhesive_density_g_cm3=rho)
         row=asdict(e);row.update(e.breakdown());lam.append(row)
    write_csv(output/'seam_sweep.csv',lam)
    thr=[]
    for t in [.1,.3,.5,1.,1.5,2.,4.,8.,13.6]:
        thr.append(dict(thrust_g=t,ideal_47mm_w=ideal_static_power(t,.047),
               ideal_101p6mm_w=ideal_static_power(t,.1016),
               old_guarded_electrical_proxy_w=(v2.motor_power_proxy(t) if t<=10.8 else None)))
    write_csv(output/'rotor_lower_bounds.csv',thr)
    states=[thermal_state(tc) for tc in np.arange(15,41,1.)]
    write_csv(output/'sealed_gas_thermal.csv',states)
    # These are input heat-loss BRACKETS, not an inferred heat-transfer coefficient.
    cool=[]
    gas_g=v2.gas_mass_g(120.,purity=1.)
    capacitance=gas_g/1000*5193+33.36/1000*1600
    area=math.pi*.62**2
    for u in [1.,2.,5.]:
      tau=capacitance/(u*area)
      for s in [0,30,60,120,300]:
       cool.append(dict(assumed_u_w_m2k=u,seconds=s,tau_s=tau,
                         gas_delta_k=5*math.exp(-s/tau)))
    write_csv(output/'thermal_cooling_brackets.csv',cool)
    ballonet=[ballonet_lower_bound(g) for g in [.1,.3,.5,1.,2.,3.]]
    write_csv(output/'ballonet_bounds.csv',ballonet)
    control=[]
    for layout in ['three','four']:
     for wind in [.1,.3,.6]:
      row,series=crosswind(layout,wind)
      control.append(row)
      write_csv(output/f'crosswind_{layout}_{wind:.1f}.csv',series)
    write_csv(output/'control_sweep.csv',control)
    convergence=[dict(dt_s=dt,**crosswind('four',.3,dt=dt)[0]) for dt in [.04,.02,.01]]
    write_csv(output/'control_convergence.csv',convergence)
    # Actual inventory: supplier data; not self-generated physical observations.
    write_csv(output/'supplier_geared_test_points.csv',[
      dict(source='MicronWings Gearbox 6mm Ball Raced',prop='GWS4025',volts=3.8,amps=.420,thrust_g=13.6),
      dict(source='MicronWings Gearbox 6mm Ball Raced',prop='GWS4025',volts=4.1,amps=.460,thrust_g=14.4),
      dict(source='MicronWings Gearbox 6mm Ball Raced',prop='GWS4040',volts=3.5,amps=.400,thrust_g=8.4),
      dict(source='MicronWings Gearbox 6mm Ball Raced',prop='GWS4040',volts=4.3,amps=.500,thrust_g=10.5)])
    nominal=thermal_state(20.)
    warm=thermal_state(40.)
    result=dict(status='Reduced-order analysis; ZERO new physical tests; no flight qualification',
       reference_envelope_g=v2.Envelope().mass, seam_candidate=seam,shape_sweep=shapes,factory_films=films,
       envelope_savings_g=v2.Envelope().mass-seam['total_g'],
       minimum_adverse_diameter_full_laminate_m=minimum_diameter(variant='full'),
       minimum_adverse_diameter_seam_m=minimum_diameter(),
       minimum_adverse_diameter_pmx2_m=minimum_diameter(variant='pmx2'),
       minimum_diameter_assumptions=dict(hardware_g=80., reserve_g=3., shape_fraction=.96),
       rotor_induced_power_ratio=ideal_static_power(2,.1016)/ideal_static_power(2,.047),
       supplier_comparison=manufacturer_comparison(),trim_sensitivity=trim,
       thermal_taut_threshold_c=(math.pi*.62**3/6*1000)/120*293.15-273.15,
       thermal_40C=warm, two_K_differential_lift_g=thermal_state(22.)['lift_g']-nominal['lift_g'],
       membrane=[membrane_stress(p) for p in [50.,150.,700.,warm['gauge_pressure_pa']]],
       ballonet_bounds=ballonet, current_baseline_four=control_current(sense_ohm=.82),
       current_revised_four=control_current(), control_ranks={x:int(np.linalg.matrix_rank(allocation_matrix(x))) for x in ['three','four']},
       control_cases=control,seam_scenario_count=len(lam),
       weight_concept_g=dict(hardware=80.,seam_envelope=seam['total_g'],dry=80+seam['total_g'],
             margin_120L_reference=v2.gas_lift_g(120)-80-seam['total_g'],
             margin_120L_adverse=v2.gas_lift_g(120,27,100000,.7,.99)-80-seam['total_g']))
    (output/'results.json').write_text(json.dumps(result,indent=2))
    ensure_measurement_template(output/'physical_measurements.csv')
    return result

if __name__=='__main__':
    result=run(ROOT/'reports')
    print(json.dumps({k:v for k,v in result.items() if k not in ['trim_sensitivity','control_cases','ballonet_bounds']},indent=2))
