"""First-order sizing, not validated flight performance. Python 3.10+, stdlib only."""
from dataclasses import dataclass, fields
from pathlib import Path
import argparse, json, math

@dataclass(frozen=True)
class Design:
    diameter_m: float = .60
    temperature_c: float = 20
    pressure_pa: float = 101325
    helium_purity: float = 1
    air_gas_constant: float = 287.05
    helium_gas_constant: float = 2077.1
    dry_mass_g: float = 105.3
    envelope_mass_g: float = 32
    battery_ah: float = 1.2
    battery_v: float = 3.7
    usable_fraction: float = .8
    charge_current_a: float = .5
    charge_turnaround_h: float = 2.75
    active_units: int = 1
    cold_negative_trim_g: float = 1.5
    preheat_delta_k: float = 20
    helium_cp_j_kg_k: float = 5193
    envelope_cp_j_kg_k: float = 1200
    overall_heat_transfer_w_m2_k: float = 2
    dock_gap_m: float = .1

    def __post_init__(self):
        numeric = [getattr(self, f.name) for f in fields(self)]
        if not all(math.isfinite(x) for x in numeric):
            raise ValueError("All model inputs must be finite.")
        if self.temperature_c <= -273.15:
            raise ValueError("Temperature must be above absolute zero.")
        for key in ("diameter_m","pressure_pa","air_gas_constant","helium_gas_constant",
                    "battery_ah","battery_v","charge_current_a","overall_heat_transfer_w_m2_k"):
            if getattr(self,key) <= 0:
                raise ValueError(f"{key} must be positive.")
        if not 0 <= self.helium_purity <= 1 or not 0 < self.usable_fraction <= 1:
            raise ValueError("Purity and usable fraction must be within physical bounds.")
        if self.active_units < 1 or int(self.active_units) != self.active_units:
            raise ValueError("active_units must be a positive integer.")
        if not 0 <= self.envelope_mass_g <= self.dry_mass_g:
            raise ValueError("Envelope mass must fit inside dry mass.")
        if min(self.charge_turnaround_h, self.cold_negative_trim_g, self.dock_gap_m,
               self.preheat_delta_k,self.helium_cp_j_kg_k,self.envelope_cp_j_kg_k) < 0:
            raise ValueError("Time, mass, spacing, heat capacity and preheat cannot be negative.")

    @property
    def kelvin(self): return self.temperature_c + 273.15
    @property
    def volume_m3(self): return math.pi * self.diameter_m**3 / 6
    @property
    def area_m2(self): return math.pi * self.diameter_m**2
    @property
    def rho_air(self): return self.pressure_pa / (self.air_gas_constant*self.kelvin)
    @property
    def rho_he(self): return self.pressure_pa / (self.helium_gas_constant*self.kelvin)
    @property
    def gas_mass_g(self):
        return self.volume_m3*1000*(self.helium_purity*self.rho_he +
                                  (1-self.helium_purity)*self.rho_air)
    @property
    def supported_dry_mass_g(self):
        return self.volume_m3*1000*self.helium_purity*(self.rho_air-self.rho_he)
    @property
    def usable_wh(self): return self.battery_ah*self.battery_v*self.usable_fraction

    def runtime_h(self, power_w):
        if not math.isfinite(power_w) or power_w <= 0:
            raise ValueError("Battery-side power must be positive and finite.")
        return self.usable_wh/power_w

    def fleet(self,power_w):
        t=self.runtime_h(power_w)
        # Parallel charging, staggered departures, deterministic duty, no failures.
        n=math.ceil(self.active_units*(1+self.charge_turnaround_h/t))
        bays=math.ceil(self.active_units*self.charge_turnaround_h/t)
        return {"runtime_h":t, "minimum_robots":n, "minimum_simultaneous_chargers":bays,
                "strip_width_m":n*self.diameter_m+(n-1)*self.dock_gap_m}

    def thermal(self,elapsed_s=0):
        if elapsed_s < 0: raise ValueError("elapsed_s must be nonnegative")
        if self.helium_purity != 1:
            raise ValueError("Thermal submodel is for pure helium only.")
        cgas=self.gas_mass_g/1000*self.helium_cp_j_kg_k
        cenv=self.envelope_mass_g/1000*self.envelope_cp_j_kg_k
        conductance=self.overall_heat_transfer_w_m2_k*self.area_m2
        tau=(cgas+cenv)/conductance
        rise=self.preheat_delta_k*math.exp(-elapsed_s/tau)
        # Requires freely expandable, near-constant-pressure envelope, no gas venting.
        dv=self.volume_m3*rise/self.kelvin
        return {"time_s":elapsed_s,"tau_s":tau,"delta_k":rise,
                "extra_lift_g":self.rho_air*dv*1000,
                "warm_volume_l":(self.volume_m3+dv)*1000,
                "stored_heat_wh":(cgas+cenv)*self.preheat_delta_k/3600,
                "initial_hold_power_w":conductance*self.preheat_delta_k}

    def summary(self,powers):
        return {"model_status":"Unvalidated engineering estimates; see assumptions and test gates",
                "volume_l":self.volume_m3*1000,"area_m2":self.area_m2,
                "gas_mass_g":self.gas_mass_g,
                "supported_dry_mass_g":self.supported_dry_mass_g,
                "dry_mass_g":self.dry_mass_g,
                "untrimmed_margin_g":self.supported_dry_mass_g-self.dry_mass_g,
                "ballast_to_cold_trim_g":max(0,self.supported_dry_mass_g-self.dry_mass_g+self.cold_negative_trim_g),
                "nominal_wh":self.battery_ah*self.battery_v,"usable_wh":self.usable_wh,
                "fleet":{name:self.fleet(p) for name,p in powers.items()},
                "thermal": [self.thermal(t) for t in (0,60,180,300)] if self.helium_purity==1 else None}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config",type=Path,default=Path(__file__).with_name("assumptions.json"))
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    raw=json.loads(args.config.read_text())
    powers=raw.pop("scenarios_w")
    result=Design(**raw).summary(powers)
    text=json.dumps(result,indent=2)
    if args.output: args.output.write_text(text+"\n")
    else: print(text)
if __name__=="__main__": main()
