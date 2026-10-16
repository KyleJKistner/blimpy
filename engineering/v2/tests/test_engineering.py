import csv, math, unittest
from pathlib import Path
from engineering.model import *
from engineering.contracts import *

class EnvelopeTests(unittest.TestCase):
    def test_reference_volume(self):self.assertAlmostEqual(Envelope().volume_l,124.7882489908,places=8)
    def test_mass_layer_sum(self):
        b=Envelope().breakdown()
        self.assertAlmostEqual(b['envelope_g'],sum(b[k] for k in ['base_film_g','sealant_g','adhesive_g','valve_g','reinforcement_g']))
    def test_two_seam_margins(self):
        e=Envelope();self.assertAlmostEqual(e.seam_area,2*e.flange_m*e.gores*math.pi*e.diameter_m/2)
    def test_diameter_cubic_lift_quadratic_skin(self):
        a=Envelope(diameter_m=.3,flange_m=0,valve_g=0,reinforcement_g=0)
        b=Envelope(diameter_m=.6,flange_m=0,valve_g=0,reinforcement_g=0)
        self.assertAlmostEqual(b.volume_l/a.volume_l,8);self.assertAlmostEqual(b.mass/a.mass,4)
    def test_unsealed_base_is_not_complete_envelope(self):
        self.assertGreater(Envelope().mass,Envelope().cut_area*13.94+10)
    def test_thicker_sealant_fails_limit(self):self.assertGreater(Envelope(sealant_um=15).mass,36)
    def test_more_gores_cost_mass(self):self.assertGreater(Envelope(gores=16).mass,Envelope(gores=8).mass)
    def test_reject_bad_geometry(self):
        for args in [{'diameter_m':-1},{'gores':0},{'sealant_um':float('nan')}]:
            with self.assertRaises(ValueError):Envelope(**args)

class LiftTests(unittest.TestCase):
    def test_no_helium_no_lift(self):self.assertEqual(gas_lift_g(120,purity=0),0)
    def test_purity_linear(self):self.assertAlmostEqual(gas_lift_g(120,purity=.8),.8*gas_lift_g(120,purity=1))
    def test_gas_mass_is_not_double_counted(self):
        self.assertAlmostEqual(gas_mass_g(120)+gas_lift_g(120),120*air_density())
    def test_moist_air_reduces_fill_capacity(self):
        self.assertLess(gas_lift_g(120,rh=1),gas_lift_g(120,rh=0))
    def test_nominal_mass_closes(self):self.assertGreater(gas_lift_g(120)-Envelope().mass-hardware_mass(),10)
    def test_hot_low_pressure_receiving_limits_need_aggregate_cap(self):
        available=gas_lift_g(120,27,100000,.7,.99)-36
        self.assertGreater(available-78,3)
        self.assertLess(available-hardware_limit(),1)
    def test_party_mix_fails_large_battery_build(self):
        self.assertLess(gas_lift_g(120,purity=.8),hardware_mass()+Envelope().mass)
    def test_slight_dimension_change_can_fail(self):
        small=Envelope(diameter_m=.55)
        self.assertLess(gas_lift_g(small.volume_l*.96),hardware_mass()+small.mass)

class PerformanceTests(unittest.TestCase):
    def test_four_motor_data_conversion(self):
        # Published row: 4.8g total, .56A @3.95V, baseline .24A.
        self.assertAlmostEqual(motor_power_proxy(1.2,1),(.56-.24)*3.95/4)
    def test_no_unbounded_extrapolation(self):
        with self.assertRaises(ValueError):motor_power_proxy(20)
    def test_zero_propulsion(self):self.assertEqual(motor_power_proxy(0),0)
    def test_guard_derating_costs_power(self):
        self.assertGreater(motor_power_proxy(1,.6),motor_power_proxy(1,1))
    def test_drag_quadratic(self):self.assertAlmostEqual(drag_n(.6)/drag_n(.3),4)
    def test_drag_power_cubic(self):self.assertAlmostEqual(drag_n(.6)*.6/(drag_n(.3)*.3),8)
    def test_battery_energy_once(self):self.assertAlmostEqual(runtime_h(2,1.8),3.0833333333333335)
    def test_reserve_not_usable_twice(self):self.assertAlmostEqual(runtime_h(2,1.8,.75)/runtime_h(2,1.8,1),.75)
    def test_added_mass_includes_displaced_air(self):
        self.assertGreater(effective_mass_kg(),.2)
    def test_braking_matches_closed_form(self):
        for speed in [.15,.3,.5,.6,1.]:
            r=braking(speed);self.assertLess(abs(r['stop_distance_m']-r['analytic_distance_m']),.0005)
    def test_faster_motion_brakes_farther(self):self.assertGreater(braking(1)['stop_distance_m'],5*braking(.3)['stop_distance_m'])
    def test_current_tolerance_not_just_typical(self):
        r=current_budget();self.assertGreater(r['trip_max_a'],r['trip_nominal_a']*1.2)
    def test_larger_pack_arithmetic_margin(self):
        r=current_budget();self.assertLess(r['static_current_envelope_a'],1.8);self.assertGreater(r['static_current_envelope_a'],1.2)
    def test_dangerous_small_sense_resistor_rejected_by_budget(self):
        self.assertGreater(current_budget(rs=.2)['static_current_envelope_a'],2)

class InterfaceTests(unittest.TestCase):
    def test_declared_gpio_nonoverlap(self):self.assertTrue(unique_pins(MEDIA_PINS));self.assertTrue(unique_pins(SAFETY_PINS))
    def test_declared_rail_compatibility(self):self.assertEqual(review(),[])
    def test_sd_card_conflict_detected(self):self.assertTrue(review(sd_enabled=True))
    def test_factory_driver_configuration_flagged(self):self.assertTrue(review(current_limit_enabled=False))
    def test_double_charger_flagged(self):self.assertTrue(review(separate_chargers_connected=True))
    def test_bad_rail_detected(self):self.assertFalse(rail_compatible((3.5,6.0),DEVICES['MAX98357A']))

if __name__=='__main__':unittest.main()
