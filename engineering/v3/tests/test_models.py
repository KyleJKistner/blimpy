import math
from pathlib import Path
import numpy as np
import pytest
from scipy.integrate import quad
from engineering import model as m
from engineering.measurements import MeasuredMap, read_points


def test_seam_single_adhesive_interface():
    x=m.SeamEnvelope().breakdown()
    assert x['cut_area_m2']-x['sphere_area_m2']==pytest.approx(2*x['interface_area_m2'])
    assert x['adhesive_g']==pytest.approx(x['interface_area_m2']*60)


def test_seam_mass_independent_sum():
    x=m.SeamEnvelope().breakdown()
    assert x['total_g']==pytest.approx(sum(x[k] for k in ['barrier_g','adhesive_g','closures_g']))


def test_seam_mass_reference():
    assert m.SeamEnvelope().breakdown()['total_g']==pytest.approx(24.469484,abs=1e-5)


def test_higher_seam_count_costs_mass():
    assert m.SeamEnvelope(gores=16).breakdown()['total_g']>m.SeamEnvelope(gores=8).breakdown()['total_g']


def test_invalid_geometry():
    with pytest.raises(ValueError):m.SeamEnvelope(diameter_m=-1)
    with pytest.raises(ValueError):m.SeamEnvelope(gores=4.5)


def test_membrane_linear_pressure():
    assert m.membrane_stress(100)['ideal_film_stress_mpa']==2*m.membrane_stress(50)['ideal_film_stress_mpa']


def test_membrane_zero_pressure():
    assert m.membrane_stress(0)['line_load_n_m']==0


def test_disk_diameter_inverse():
    assert m.ideal_static_power(1,.1)/m.ideal_static_power(1,.05)==pytest.approx(.5)


def test_disk_thrust_exponent():
    assert m.ideal_static_power(2,.1)/m.ideal_static_power(1,.1)==pytest.approx(2**1.5)


def test_disk_zero():
    assert m.ideal_static_power(0,.1)==0


def test_disk_negative_rejected():
    with pytest.raises(ValueError):m.ideal_static_power(-1,.1)


def test_empirical_powers_above_ideal():
    x=m.manufacturer_comparison()
    assert x['geared_supplier_electrical_w']>m.ideal_static_power(13.6,.1016)
    assert x['historical_incremental_proxy_w']>m.ideal_static_power(13.6,.047)


def test_manufacturer_power_arithmetic():
    assert m.manufacturer_comparison()['geared_supplier_electrical_w']==pytest.approx(1.596)


def test_thermal_gas_mass_conservation():
    assert m.thermal_state(20)['gas_mass_g']==m.thermal_state(40)['gas_mass_g']


def test_slack_negligible_pressure():
    assert m.thermal_state(22)['gauge_pressure_pa']==pytest.approx(0,abs=1e-8)


def test_taut_pressure_positive():
    assert m.thermal_state(40)['gauge_pressure_pa']>2000


def test_equal_air_and_gas_temperature_cancels_dry_lift():
    a=m.thermal_state(15,ambient_c=15,rh=0,fill_rh=0,max_volume_l=200)
    b=m.thermal_state(30,ambient_c=30,rh=0,fill_rh=0,max_volume_l=200)
    assert a['lift_g']==pytest.approx(b['lift_g'])


def test_uniform_ambient_pressure_cancels_slack_dry_lift():
    a=m.thermal_state(20,ambient_pa=95000,rh=0,fill_rh=0,max_volume_l=200)
    b=m.thermal_state(20,ambient_pa=103000,rh=0,fill_rh=0,max_volume_l=200)
    assert a['lift_g']==pytest.approx(b['lift_g'])


def test_fixed_volume_no_extra_thermal_lift():
    a=m.thermal_state(35);b=m.thermal_state(40)
    assert a['lift_g']==pytest.approx(b['lift_g'])
    assert b['gauge_pressure_pa']>a['gauge_pressure_pa']


def test_fill_above_cap_rejected():
    with pytest.raises(ValueError):m.thermal_state(20,fill_l=150,max_volume_l=100)


def test_ballonet_no_air_no_change():
    x=m.ballonet_lower_bound(0)
    assert x['gauge_pressure_pa']==0
    assert x['reversible_pump_work_j']==0


def test_ballonet_pressure_proportional_mass():
    assert m.ballonet_lower_bound(2)['gauge_pressure_pa']==pytest.approx(2*m.ballonet_lower_bound(1)['gauge_pressure_pa'])


def test_ballonet_work_independent_quadrature():
    x=m.ballonet_lower_bound(1)
    intake=x['intake_l']/1000;vol=.120;p=101325.
    numeric=quad(lambda v:p*math.log1p(v/vol),0,intake)[0]
    assert x['reversible_pump_work_j']==pytest.approx(numeric,rel=1e-10)


def test_ballonet_volume_relation():
    x=m.ballonet_lower_bound(1)
    assert x['internal_air_volume_l']<x['intake_l']


def test_control_ranks():
    assert np.linalg.matrix_rank(m.allocation_matrix('three'))==3
    assert np.linalg.matrix_rank(m.allocation_matrix('four'))==4


def test_four_dof_inverse_reconstructs():
    a=m.allocation_matrix();w=np.array([.01,.008,.003,.0004])
    assert np.allclose(a@np.linalg.solve(a,w),w)


def test_three_cannot_make_pure_lateral_force():
    a=m.allocation_matrix('three');w=np.array([0,.01,0,0])
    u=np.linalg.lstsq(a,w,rcond=None)[0]
    assert np.linalg.norm(a@u-w)==pytest.approx(.01)


def test_motor_current_four_old_resistor_exceeds_2a():
    assert m.control_current(sense_ohm=.82)['static_allocated_a']>2


def test_motor_current_four_revised_below_1p8a():
    assert m.control_current()['static_allocated_a']<1.8


def test_crosswind_zero_preserves_equilibrium():
    result,_=m.crosswind('four',0,final_s=10,dt=.02)
    assert result['max_lateral_error_m']==0


def test_crosswind_control_reduces_drift():
    a,_=m.crosswind('three',.3,final_s=30)
    b,_=m.crosswind('four',.3,final_s=30)
    assert b['max_lateral_error_m']<a['max_lateral_error_m']/10


def test_crosswind_step_convergence():
    a,_=m.crosswind('four',.3,dt=.04)
    b,_=m.crosswind('four',.3,dt=.02)
    c,_=m.crosswind('four',.3,dt=.01)
    assert abs(b['max_lateral_error_m']-c['max_lateral_error_m'])<.001
    assert abs(a['max_lateral_error_m']-c['max_lateral_error_m'])<.002


def test_seam_reduces_minimum_diameter():
    assert m.minimum_diameter(variant='seam')<m.minimum_diameter(variant='full')


def test_trim_reduction_not_battery_energy_creation():
    old=m.v2.mission(trim_g=1.5);new=m.v2.mission(trim_g=.3)
    for x in [old,new]:
        assert x['runtime_2000mah_h']*x['total_power_proxy_w']==pytest.approx(5.55)
    assert new['runtime_2000mah_h']>old['runtime_2000mah_h']


def test_empty_physical_data_rejected(tmp_path):
    p=tmp_path/'empty.csv';p.write_text('assembly_id,direction,guarded,voltage_v,thrust_g,current_a\n')
    with pytest.raises(ValueError,match='No physical measurements'):read_points(p)


def synthetic_rows():
    # Deliberately SYNTHETIC affine power surface for interpolation correctness.
    return [dict(assembly_id='SYNTHETIC',direction='forward',guarded='true',
      voltage_v=v,thrust_g=t,current_a=(v+2*t)/v) for v,t in [(3,0),(4,0),(3,2),(4,2)]]


def test_interpolation_of_synthetic_surface():
    f=MeasuredMap(synthetic_rows(),'SYNTHETIC','forward')
    assert f.watts(3.5,1)==pytest.approx(5.5)


def test_interpolation_refuses_extrapolation():
    f=MeasuredMap(synthetic_rows(),'SYNTHETIC','forward')
    with pytest.raises(ValueError,match='outside'):f.watts(4.2,1)


def test_interpolation_cannot_mix_directions():
    with pytest.raises(ValueError):MeasuredMap(synthetic_rows(),'SYNTHETIC','reverse')


def test_interpolation_rejects_collinear_coverage():
    rows=synthetic_rows()[:2]*2
    with pytest.raises(ValueError):MeasuredMap(rows,'SYNTHETIC','forward')


def test_prolate_preserves_volume():
    for a in [1.,1.3,1.5,2.]:
        assert m.prolate_shape(a)['volume_l']==pytest.approx(m.SeamEnvelope().breakdown()['sphere_volume_l'])


def test_prolate_spherical_limit():
    x=m.prolate_shape(1.)
    assert x['seam_candidate_mass_g']==pytest.approx(m.SeamEnvelope().breakdown()['total_g'])
    assert x['area_ratio_to_sphere']==pytest.approx(1.)


def test_prolate_tradeoff():
    x=m.prolate_shape(1.5)
    assert x['width_m']<.62<x['length_m']
    assert x['area_ratio_to_sphere']>1.
    assert x['forward_area_ratio']<1.


def test_prolate_area_independent_quadrature():
    a=m.prolate_shape(1.5)['length_m']/2
    b=m.prolate_shape(1.5)['width_m']/2
    numeric=quad(lambda t:2*math.pi*b*math.sin(t)*math.sqrt(a*a*math.sin(t)**2+b*b*math.cos(t)**2),0,math.pi)[0]
    assert m.prolate_shape(1.5)['surface_area_m2']==pytest.approx(numeric,rel=1e-10)


def test_factory_yield_reciprocal():
    x=m.factory_film_envelopes()[0]
    assert x['complete_film_g_m2']*73.3==pytest.approx(1000)
    assert x['helium_qualified'] is False


def test_full_factory_film_does_not_add_sealant_twice():
    x=m.factory_film_envelopes()[0]
    assert x['envelope_g']==pytest.approx(x['cut_area_m2']*x['complete_film_g_m2']+2.5)



def test_factory_film_minimum_diameter_lower_than_reference():
    assert m.minimum_diameter(variant='pmx2') < m.minimum_diameter(variant='seam')


def test_unknown_envelope_variant_rejected():
    with pytest.raises(ValueError):m.minimum_diameter(variant='invented')


def test_existing_measurement_log_never_overwritten(tmp_path):
    p=tmp_path/'physical_measurements.csv';p.write_text('EXISTING REAL OBSERVATIONS\n')
    m.ensure_measurement_template(p)
    assert p.read_text()=='EXISTING REAL OBSERVATIONS\n'
