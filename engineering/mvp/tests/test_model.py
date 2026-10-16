import unittest
from dataclasses import replace
from engineering.model import Design
class ModelTests(unittest.TestCase):
    def setUp(self):self.d=Design()
    def test_sphere_volume(self):self.assertAlmostEqual(self.d.volume_m3*1000,113.0973,places=3)
    def test_lift(self):self.assertAlmostEqual(self.d.supported_dry_mass_g,117.3625,places=3)
    def test_purity(self):self.assertAlmostEqual(replace(self.d,helium_purity=.8).supported_dry_mass_g,self.d.supported_dry_mass_g*.8)
    def test_air_filled(self):self.assertEqual(replace(self.d,helium_purity=0).supported_dry_mass_g,0)
    def test_half_diameter_eighth_lift(self):self.assertAlmostEqual(replace(self.d,diameter_m=.3).supported_dry_mass_g,self.d.supported_dry_mass_g/8)
    def test_energy(self):self.assertAlmostEqual(self.d.usable_wh,3.552)
    def test_runtime(self):self.assertAlmostEqual(self.d.runtime_h(1.5),2.368)
    def test_fleet(self):self.assertEqual(self.d.fleet(1.5)["minimum_robots"],3)
    def test_parallel_chargers(self):self.assertEqual(self.d.fleet(1.5)["minimum_simultaneous_chargers"],2)
    def test_two_active_fleet(self):self.assertEqual(replace(self.d,active_units=2).fleet(1.5)["minimum_robots"],5)
    def test_heat_decay(self):self.assertLess(self.d.thermal(180)["extra_lift_g"],.5)
    def test_heat_initial(self):self.assertAlmostEqual(self.d.thermal()["extra_lift_g"],9.291,places=3)
    def test_no_preheat(self):self.assertEqual(replace(self.d,preheat_delta_k=0).thermal()["extra_lift_g"],0)
    def test_bad_power(self):
        for x in [0,-1,float("inf"),float("nan")]:
            with self.assertRaises(ValueError):self.d.runtime_h(x)
    def test_bad_inputs(self):
        for kw in [{"helium_purity":1.1},{"diameter_m":0},{"temperature_c":-274},
                   {"usable_fraction":0},{"active_units":1.5},{"envelope_mass_g":200}]:
            with self.assertRaises(ValueError):Design(**kw)
    def test_thermal_mixture_guard(self):
        with self.assertRaises(ValueError):replace(self.d,helium_purity=.8).thermal()
