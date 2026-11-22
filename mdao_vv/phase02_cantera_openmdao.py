"""
Phase 2: Detailed Combustion Chemical Kinetics (Cantera Jet-A1 Surrogate) &
Off-Design Micro-Turbojet Cycle Analysis (NASA OpenMDAO).

Real Solvers Invoked:
  - Cantera (nDodecane_Reitz.yaml Jet-A1 surrogate / gri30.yaml):
      * Real temperature-dependent cp(T), gamma(T), mu(T), k(T), enthalpy/entropy
      * Equilibrium adiabatic flame temp + dissociation (CO, OH, NO)
      * 1D Laminar Flame Speed S_L via ct.FreeFlame
      * Autoignition delay tau_ign via ct.IdealGasConstPressureReactor
      * Lean Blowout (LBO) limit via ct.IdealGasReactor PSR sweep
  - OpenMDAO (openmdao.api.Problem, Group, ExplicitComponent):
      * Coupled Intake -> Compressor (Low-Re + Tip-Clearance loss) ->
        Cantera Combustor (RCS bleed + pressure loss) -> Turbine + De Laval Nozzle
      * 8-point Idle-to-Max off-design operating map (Thrust, TSFC, EGT, Surge Margin)
"""
from __future__ import annotations

import math
import time
from typing import Any, Dict, List, Tuple

import cantera as ct        # Strictly required (Phase 0)
import numpy as np
import openmdao.api as om   # Strictly required (Phase 0)

from .state_io import MDAOStateStore


def _select_cantera_mechanism() -> Tuple[str, str]:
    """Select built-in Cantera Jet-A1 surrogate (n-Dodecane C12H26) or hydrocarbon mechanism."""
    candidates = [
        ("nDodecane_Reitz.yaml", "c12h26"),
        ("nDodecane_Reitz.yaml", "nc12h26"),
        ("gri30.yaml", "C3H8"),
    ]
    for mech, fuel_sp in candidates:
        try:
            g = ct.Solution(mech)
            if fuel_sp in g.species_names:
                return mech, fuel_sp
        except Exception:
            continue
    return "gri30.yaml", "CH4"


def _compute_cantera_kinetics(
    mech: str,
    fuel_sp: str,
    T_in: float,
    P_in: float,
    comb_vol_m3: float,
    mdot_air_primary: float,
) -> Dict[str, Any]:
    """Run real Cantera equilibrium, 1D FreeFlame S_L, autoignition delay, and PSR LBO."""
    gas = ct.Solution(mech)
    ox = "o2:1.0, n2:3.76" if "o2" in gas.species_names else "O2:1.0, N2:3.76"
    co_sp = "co" if "co" in gas.species_names else "CO"
    oh_sp = "oh" if "oh" in gas.species_names else "OH"

    # 1. Adiabatic Flame Temperature & Dissociation at stoichiometric (phi=1.0)
    gas.TP = T_in, P_in
    gas.set_equivalence_ratio(1.0, fuel=fuel_sp, oxidizer=ox)
    gas.equilibrate("HP")
    T_ad_stoich_K = float(gas.T)
    co_eq_ppm = float(gas[co_sp].X[0] * 1e6) if co_sp in gas.species_names else 0.0
    oh_eq_ppm = float(gas[oh_sp].X[0] * 1e6) if oh_sp in gas.species_names else 0.0
    cp_flame = float(gas.cp_mass)
    gamma_flame = float(gas.cp_mass / gas.cv_mass)

    # 2. 1D Laminar Flame Speed S_L via Cantera FreeFlame
    S_L_m_s = None
    flame_mech = "gri30.yaml (C3H8 FreeFlame)"
    try:
        g_fl = ct.Solution("gri30.yaml")
        g_fl.TP = T_in, P_in
        g_fl.set_equivalence_ratio(1.0, fuel="C3H8:1.0", oxidizer="O2:1.0, N2:3.76")
        flame = ct.FreeFlame(g_fl, width=0.010)
        flame.set_refine_criteria(ratio=5.0, slope=0.45, curve=0.45)
        flame.transport_model = "mixture-averaged"
        flame.solve(loglevel=0, auto=True)
        S_L_m_s = float(flame.velocity[0])
    except Exception:
        g_fl = ct.Solution("gri30.yaml")
        g_fl.TP = T_in, P_in
        g_fl.set_equivalence_ratio(1.0, fuel="CH4:1.0", oxidizer="O2:1.0, N2:3.76")
        flame = ct.FreeFlame(g_fl, width=0.012)
        flame.set_refine_criteria(ratio=5.0, slope=0.5, curve=0.5)
        flame.solve(loglevel=0, auto=True)
        S_L_m_s = float(flame.velocity[0])
        flame_mech = "gri30.yaml (CH4 FreeFlame)"

    # 3. Autoignition Delay Time tau_ign via real-gas ConstPressureReactor (at T_ign_test = 1050 K, P_in)
    g_ign = ct.Solution(mech)
    g_ign.TP = 1050.0, P_in
    g_ign.set_equivalence_ratio(1.0, fuel=fuel_sp, oxidizer=ox)
    reac = ct.ConstPressureReactor(g_ign)
    sim = ct.ReactorNet([reac])
    t_cur = 0.0
    t_prev = 0.0
    T_prev = 1050.0
    max_dTdt = 0.0
    tau_ign_s = 0.02
    while t_cur < 0.02:
        t_cur = sim.step()
        T_cur = float(reac.T)
        dt = max(t_cur - t_prev, 1e-12)
        dTdt = (T_cur - T_prev) / dt
        if dTdt > max_dTdt:
            max_dTdt = dTdt
            tau_ign_s = t_cur
        T_prev, t_prev = T_cur, t_cur
        if T_cur > 1900.0:
            break

    # 4. Lean Blowout (LBO) Sweep via Cantera Perfectly Stirred Reactor (PSR)
    phi_lbo = 0.55
    psr_temps: List[Tuple[float, float]] = []
    V_primary = max(3.0e-6, comb_vol_m3 * 0.42)
    for phi_try in np.linspace(0.85, 0.29, 8):
        g_in = ct.Solution(mech)
        g_in.TP = T_in, P_in
        g_in.set_equivalence_ratio(float(phi_try), fuel=fuel_sp, oxidizer=ox)
        inlet = ct.Reservoir(g_in)

        g_hot = ct.Solution(mech)
        g_hot.TP = T_in, P_in
        g_hot.set_equivalence_ratio(float(phi_try), fuel=fuel_sp, oxidizer=ox)
        g_hot.equilibrate("HP")
        psr = ct.Reactor(g_hot)
        psr.volume = V_primary
        exhaust = ct.Reservoir(g_hot)
        ct.MassFlowController(inlet, psr, mdot=max(0.002, mdot_air_primary))
        ct.Valve(psr, exhaust, K=1e-3)
        net = ct.ReactorNet([psr])
        try:
            net.advance(0.008)
            T_psr = float(psr.T)
        except Exception:
            T_psr = T_in
        psr_temps.append((float(phi_try), T_psr))
        if T_psr > T_in + 450.0:
            phi_lbo = float(phi_try)
        else:
            break

    return {
        "mechanism": mech,
        "fuel_species": fuel_sp,
        "flame_mech": flame_mech,
        "T_ad_stoich_K": round(T_ad_stoich_K, 1),
        "cp_flame_J_kgK": round(cp_flame, 1),
        "gamma_flame": round(gamma_flame, 4),
        "co_eq_ppm": round(co_eq_ppm, 1),
        "oh_eq_ppm": round(oh_eq_ppm, 1),
        "laminar_flame_speed_m_s": round(S_L_m_s, 4),
        "ignition_delay_ms": round(tau_ign_s * 1e3, 4),
        "phi_lbo": round(phi_lbo, 3),
        "psr_curve": psr_temps,
    }


# ==============================================================================
# REAL NASA OpenMDAO COMPONENTS (COUPLED WITH CANTERA REAL-GAS PROPERTIES)
# ==============================================================================
class IntakeSductComp(om.ExplicitComponent):
    """Compressible S-duct intake with real Cantera air properties & Dean loss."""

    def initialize(self):
        self.options.declare("gas", types=ct.Solution)

    def setup(self):
        self.add_input("mdot_air", val=0.032, units="kg/s")
        self.add_input("A_intake", val=1.145e-4, units="m**2")
        self.add_input("T_amb", val=288.15, units="K")
        self.add_input("P_amb", val=101325.0, units="Pa")
        self.add_output("M_intake", val=0.2)
        self.add_output("eta_intake", val=0.95)
        self.add_output("P_t2", val=100000.0, units="Pa")
        self.add_output("T_t2", val=288.15, units="K")

    def compute(self, inputs, outputs):
        gas = self.options["gas"]
        mdot = float(inputs["mdot_air"][0])
        A_in = max(1e-6, float(inputs["A_intake"][0]))
        T0 = float(inputs["T_amb"][0])
        P0 = float(inputs["P_amb"][0])

        ox = "o2:1.0, n2:3.76" if "o2" in gas.species_names else "O2:1.0, N2:3.76"
        gas.TPX = T0, P0, ox
        rho0 = float(gas.density)
        a0 = float(gas.sound_speed)
        V_in = mdot / (rho0 * A_in)
        M_in = min(0.98, V_in / a0)
        # S-duct bend + NACA recessed lip total pressure loss K_sduct = 0.65
        dP = 0.65 * 0.5 * rho0 * (V_in ** 2)
        eta_d = max(0.68, 1.0 - dP / P0)

        outputs["M_intake"] = M_in
        outputs["eta_intake"] = eta_d
        outputs["P_t2"] = P0 * eta_d
        outputs["T_t2"] = T0


_TRANS_GAS_CACHE = None


def _cantera_viscosity(gas: ct.Solution, T: float, P: float) -> float:
    """Query real Cantera mixture-averaged viscosity (falls back to gri30.yaml transport if mech has transport='none')."""
    global _TRANS_GAS_CACHE
    try:
        return float(gas.viscosity)
    except Exception:
        if _TRANS_GAS_CACHE is None:
            _TRANS_GAS_CACHE = ct.Solution("gri30.yaml")
        _TRANS_GAS_CACHE.TPX = T, P, "O2:1.0, N2:3.76"
        return float(_TRANS_GAS_CACHE.viscosity)


def _cantera_P_from_SH(gas: ct.Solution, s_target: float, h_target: float, p_lo: float, p_hi: float) -> float:
    """Solve exact pressure P [Pa] at constant entropy s_target matching enthalpy h_target via real Cantera gas.SP."""
    lo, hi = math.log(max(p_lo, 5000.0)), math.log(max(p_hi, p_lo * 1.1))
    for _ in range(22):
        mid = 0.5 * (lo + hi)
        gas.SP = s_target, math.exp(mid)
        if float(gas.enthalpy_mass) < h_target:
            lo = mid
        else:
            hi = mid
    p_sol = math.exp(0.5 * (lo + hi))
    gas.SP = s_target, p_sol
    return p_sol


class CentrifugalCompressorComp(om.ExplicitComponent):
    """38mm micro-centrifugal compressor with Cantera real gas, Low-Re & tip-clearance loss."""

    def initialize(self):
        self.options.declare("gas", types=ct.Solution)

    def setup(self):
        self.add_input("rpm", val=225000.0)
        self.add_input("D_comp", val=0.038, units="m")
        self.add_input("tip_clr_comp", val=0.31e-3, units="m")
        self.add_input("mdot_air", val=0.032, units="kg/s")
        self.add_input("P_t2", val=95000.0, units="Pa")
        self.add_input("T_t2", val=288.15, units="K")
        self.add_output("PR_comp", val=3.2)
        self.add_output("eta_comp", val=0.72)
        self.add_output("P_t3", val=300000.0, units="Pa")
        self.add_output("T_t3", val=450.0, units="K")
        self.add_output("W_comp", val=5000.0, units="W")
        self.add_output("surge_margin_pct", val=15.0)

    def compute(self, inputs, outputs):
        gas = self.options["gas"]
        rpm = float(inputs["rpm"][0])
        D2 = float(inputs["D_comp"][0])
        clr = max(0.0, float(inputs["tip_clr_comp"][0]))
        mdot = float(inputs["mdot_air"][0])
        P2 = float(inputs["P_t2"][0])
        T2 = float(inputs["T_t2"][0])

        ox = "o2:1.0, n2:3.76" if "o2" in gas.species_names else "O2:1.0, N2:3.76"
        gas.TPX = T2, P2, ox
        h2 = float(gas.enthalpy_mass)
        s2 = float(gas.entropy_mass)
        mu2 = _cantera_viscosity(gas, T2, P2)
        rho2 = float(gas.density)

        omega = rpm * 2.0 * math.pi / 60.0
        U2 = omega * (D2 * 0.5)
        b2 = 0.0038  # Exducer blade height 3.8 mm
        Z_eff = 20.0
        slip = 1.0 - math.sqrt(math.cos(math.radians(22.0))) / (Z_eff ** 0.7)

        Re_u2 = rho2 * U2 * b2 / max(mu2, 1e-8)
        d_eta_re = 0.045 * max(0.0, (2.5e5 / max(Re_u2, 2e4)) ** 0.25 - 1.0)
        d_eta_clr = 0.35 * (clr / b2)
        eta_c = max(0.55, min(0.81, 0.78 - d_eta_re - d_eta_clr))

        dh_actual = slip * (U2 ** 2) * 0.945
        h3 = h2 + dh_actual
        h3s = h2 + eta_c * dh_actual

        # Exact Cantera real-gas isentropic state at (s2, h3s) -> exact P_t3!
        P3 = _cantera_P_from_SH(gas, s2, h3s, P2, P2 * 12.0)
        gas.HP = h3, P3
        T3 = float(gas.T)
        pr = P3 / P2

        mdot_surge = 0.0115 * (rpm / 225000.0) * (P2 / 101325.0)
        sm_pct = ((mdot / max(mdot_surge, 1e-5)) - 1.0) * 100.0 * 0.35

        outputs["PR_comp"] = pr
        outputs["eta_comp"] = eta_c
        outputs["P_t3"] = P3
        outputs["T_t3"] = T3
        outputs["W_comp"] = mdot * dh_actual
        outputs["surge_margin_pct"] = sm_pct


class CanteraCombustorComp(om.ExplicitComponent):
    """Real Cantera equilibrium combustor with RCS bleed-air deduction & liner pressure drop."""

    def initialize(self):
        self.options.declare("gas", types=ct.Solution)
        self.options.declare("fuel_sp", types=str)

    def setup(self):
        self.add_input("mdot_air", val=0.032, units="kg/s")
        self.add_input("bleed_frac", val=0.025)
        self.add_input("P_t3", val=300000.0, units="Pa")
        self.add_input("T_t3", val=450.0, units="K")
        self.add_input("TIT_target", val=1160.0, units="K")
        self.add_output("mdot_fuel", val=0.0006, units="kg/s")
        self.add_output("mdot_gas", val=0.0318, units="kg/s")
        self.add_output("P_t4", val=283000.0, units="Pa")
        self.add_output("T_t4", val=1160.0, units="K")
        self.add_output("phi_overall", val=0.28)
        self.add_output("h_t4", val=0.0, units="J/kg")
        self.add_output("s_t4", val=0.0, units="J/(kg*K)")
        self.add_output("cp_t4", val=1150.0, units="J/(kg*K)")
        self.add_output("gamma_t4", val=1.33)
        self.add_output("mu_t4", val=4.5e-5, units="Pa*s")

    def compute(self, inputs, outputs):
        gas = self.options["gas"]
        fuel_sp = self.options["fuel_sp"]
        ox = "o2:1.0, n2:3.76" if "o2" in gas.species_names else "O2:1.0, N2:3.76"

        mdot_core = float(inputs["mdot_air"][0]) * (1.0 - float(inputs["bleed_frac"][0]))
        P3 = float(inputs["P_t3"][0])
        T3 = float(inputs["T_t3"][0])
        TIT_req = float(inputs["TIT_target"][0])
        P4 = P3 * 0.945

        lo, hi = 0.04, 0.72
        for _ in range(18):
            mid = 0.5 * (lo + hi)
            gas.TP = T3, P4
            gas.set_equivalence_ratio(mid, fuel=fuel_sp, oxidizer=ox)
            gas.equilibrate("HP")
            if float(gas.T) < TIT_req:
                lo = mid
            else:
                hi = mid
        phi = 0.5 * (lo + hi)
        gas.TP = T3, P4
        gas.set_equivalence_ratio(phi, fuel=fuel_sp, oxidizer=ox)
        Y_fuel = float(gas[fuel_sp].Y[0])
        far = Y_fuel / max(1.0 - Y_fuel, 1e-6)
        mdot_f = mdot_core * far / 0.95
        gas.equilibrate("HP")

        T4_eq = float(gas.T)
        outputs["mdot_fuel"] = mdot_f
        outputs["mdot_gas"] = mdot_core + mdot_f
        outputs["P_t4"] = P4
        outputs["T_t4"] = T4_eq
        outputs["phi_overall"] = phi
        outputs["h_t4"] = float(gas.enthalpy_mass)
        outputs["s_t4"] = float(gas.entropy_mass)
        outputs["cp_t4"] = float(gas.cp_mass)
        outputs["gamma_t4"] = float(gas.cp_mass / gas.cv_mass)
        outputs["mu_t4"] = _cantera_viscosity(gas, T4_eq, P4)


class TurbineNozzleComp(om.ExplicitComponent):
    """Real Cantera hot-gas turbine work match + De Laval nozzle thrust expansion."""

    def initialize(self):
        self.options.declare("gas", types=ct.Solution)
        self.options.declare("fuel_sp", types=str)

    def setup(self):
        self.add_input("mdot_gas", val=0.0318, units="kg/s")
        self.add_input("mdot_fuel", val=0.0006, units="kg/s")
        self.add_input("W_comp", val=5000.0, units="W")
        self.add_input("P_t4", val=283000.0, units="Pa")
        self.add_input("T_t4", val=1160.0, units="K")
        self.add_input("phi_overall", val=0.28)
        self.add_input("tip_clr_turb", val=0.10e-3, units="m")
        self.add_input("P_amb", val=101325.0, units="Pa")
        self.add_output("P_t5", val=150000.0, units="Pa")
        self.add_output("T_t5", val=990.0, units="K")
        self.add_output("NPR", val=1.5)
        self.add_output("V_exit", val=380.0, units="m/s")
        self.add_output("T_exit", val=920.0, units="K")
        self.add_output("thrust_N", val=11.5, units="N")
        self.add_output("tsfc_g_kNs", val=50.0)
        self.add_output("eta_turb", val=0.79)

    def compute(self, inputs, outputs):
        gas = self.options["gas"]
        fuel_sp = self.options["fuel_sp"]
        ox = "o2:1.0, n2:3.76" if "o2" in gas.species_names else "O2:1.0, N2:3.76"

        mdot_g = float(inputs["mdot_gas"][0])
        mdot_f = float(inputs["mdot_fuel"][0])
        W_c = float(inputs["W_comp"][0])
        P4 = float(inputs["P_t4"][0])
        T4 = float(inputs["T_t4"][0])
        phi = float(inputs["phi_overall"][0])
        clr_t = max(0.0, float(inputs["tip_clr_turb"][0]))
        P0 = float(inputs["P_amb"][0])

        gas.TP = 450.0, P4
        gas.set_equivalence_ratio(max(0.04, phi), fuel=fuel_sp, oxidizer=ox)
        gas.equilibrate("HP")
        gas.TP = T4, P4
        h4 = float(gas.enthalpy_mass)
        s4 = float(gas.entropy_mass)

        eta_t = max(0.65, min(0.84, 0.82 - 1.4 * (clr_t / 0.0073)))
        eta_m = 0.96
        dh_t = W_c / (eta_m * max(mdot_g, 1e-6))
        h5 = h4 - dh_t
        h5s = h4 - dh_t / eta_t

        P5 = max(P0 * 1.03, _cantera_P_from_SH(gas, s4, h5s, P0 * 0.5, P4))
        gas.HP = h5, P5
        T5 = float(gas.T)
        s5 = float(gas.entropy_mass)

        gas.SP = s5, P0
        h8s = float(gas.enthalpy_mass)
        dh_noz = max(100.0, 0.95 * (h5 - h8s))
        V_e = math.sqrt(2.0 * dh_noz)
        h8 = h5 - dh_noz
        gas.HP = h8, P0
        T_e = float(gas.T)

        thrust = mdot_g * V_e
        tsfc = (mdot_f * 1e6) / max(thrust, 1e-6)

        outputs["P_t5"] = P5
        outputs["T_t5"] = T5
        outputs["NPR"] = P5 / P0
        outputs["V_exit"] = V_e
        outputs["T_exit"] = T_e
        outputs["thrust_N"] = thrust
        outputs["tsfc_g_kNs"] = tsfc
        outputs["eta_turb"] = eta_t


def run_phase02(spec: Dict[str, Any], store: MDAOStateStore) -> Dict[str, Any]:
    """Execute Phase 2: Cantera detailed combustion kinetics + OpenMDAO off-design cycle."""
    t0 = time.perf_counter()
    print("=== [Phase 2] Cantera Detailed Kinetics & OpenMDAO Off-Design Cycle ===")

    p1 = store.load_phase("phase01_geometry")
    geom = p1["geometry"]
    pspec = spec["propulsion_spec"]

    mech, fuel_sp = _select_cantera_mechanism()
    gas_shared = ct.Solution(mech)

    # Assemble real NASA OpenMDAO coupled cycle problem
    prob = om.Problem(reports=None)
    model = prob.model
    model.add_subsystem("intake", IntakeSductComp(gas=gas_shared), promotes=["*"])
    model.add_subsystem("compressor", CentrifugalCompressorComp(gas=gas_shared), promotes=["*"])
    model.add_subsystem("combustor", CanteraCombustorComp(gas=gas_shared, fuel_sp=fuel_sp), promotes=["*"])
    model.add_subsystem("turbine_nozzle", TurbineNozzleComp(gas=gas_shared, fuel_sp=fuel_sp), promotes=["*"])
    prob.setup()

    # Exact geometric coupling from Phase 1!
    A_intake_m2 = geom["intake_total_area_mm2"] * 1e-6
    D_comp_m = float(pspec.get("compressor_diameter_mm", 38.0)) * 1e-3
    clr_comp_m = max(0.05e-3, geom["comp_tip_clr_hot_mm"] * 1e-3)
    clr_turb_m = max(0.05e-3, geom["turb_tip_clr_hot_mm"] * 1e-3)
    rpm_max = float(pspec.get("max_rpm", 225000.0))
    rpm_idle = float(pspec.get("idle_rpm", 68000.0))
    bleed_frac = 0.025 if "bleed" in str(pspec.get("rcs_type", "bleed")).lower() or "ブリード" in str(pspec.get("rcs_type", "")) else 0.0

    # 8-point Off-Design Throttle Sweep (Idle 30% -> Full 100%)
    throttles = np.linspace(0.0, 1.0, 8)
    od_map: Dict[str, List[float]] = {
        "throttle": [], "rpm": [], "mdot_air_g_s": [], "PR": [], "thrust_N": [],
        "tsfc_g_kNs": [], "EGT_K": [], "TIT_K": [], "surge_margin_pct": [], "M_intake": [],
    }
    full_point: Dict[str, float] = {}

    for thr in throttles:
        rpm_i = rpm_idle + (rpm_max - rpm_idle) * (thr ** 0.85)
        mdot_i = 0.0085 + 0.0235 * (rpm_i / rpm_max) ** 1.45
        tit_i = 840.0 + 325.0 * (thr ** 0.90)

        prob.set_val("rpm", rpm_i)
        prob.set_val("mdot_air", mdot_i)
        prob.set_val("A_intake", A_intake_m2)
        prob.set_val("D_comp", D_comp_m)
        prob.set_val("tip_clr_comp", clr_comp_m)
        prob.set_val("tip_clr_turb", clr_turb_m)
        prob.set_val("bleed_frac", bleed_frac)
        prob.set_val("TIT_target", tit_i)
        prob.run_model()

        od_map["throttle"].append(round(float(thr), 3))
        od_map["rpm"].append(round(rpm_i, 0))
        od_map["mdot_air_g_s"].append(round(mdot_i * 1e3, 2))
        od_map["PR"].append(round(float(prob.get_val("PR_comp")[0]), 3))
        od_map["thrust_N"].append(round(float(prob.get_val("thrust_N")[0]), 3))
        od_map["tsfc_g_kNs"].append(round(float(prob.get_val("tsfc_g_kNs")[0]), 2))
        od_map["EGT_K"].append(round(float(prob.get_val("T_t5")[0]), 1))
        od_map["TIT_K"].append(round(float(prob.get_val("T_t4")[0]), 1))
        od_map["surge_margin_pct"].append(round(float(prob.get_val("surge_margin_pct")[0]), 2))
        od_map["M_intake"].append(round(float(prob.get_val("M_intake")[0]), 3))

        if thr == 1.0:
            full_point = {
                "rpm_max": rpm_i,
                "mdot_air_kg_s": mdot_i,
                "mdot_fuel_kg_s": float(prob.get_val("mdot_fuel")[0]),
                "mdot_gas_kg_s": float(prob.get_val("mdot_gas")[0]),
                "M_intake": float(prob.get_val("M_intake")[0]),
                "eta_intake": float(prob.get_val("eta_intake")[0]),
                "P_t2_Pa": float(prob.get_val("P_t2")[0]),
                "T_t2_K": float(prob.get_val("T_t2")[0]),
                "PR_comp": float(prob.get_val("PR_comp")[0]),
                "eta_comp": float(prob.get_val("eta_comp")[0]),
                "P_t3_Pa": float(prob.get_val("P_t3")[0]),
                "T_t3_K": float(prob.get_val("T_t3")[0]),
                "W_comp_W": float(prob.get_val("W_comp")[0]),
                "surge_margin_pct": float(prob.get_val("surge_margin_pct")[0]),
                "P_t4_Pa": float(prob.get_val("P_t4")[0]),
                "T_t4_K": float(prob.get_val("T_t4")[0]),
                "phi_overall": float(prob.get_val("phi_overall")[0]),
                "cp_t4_J_kgK": float(prob.get_val("cp_t4")[0]),
                "gamma_t4": float(prob.get_val("gamma_t4")[0]),
                "mu_t4_Pa_s": float(prob.get_val("mu_t4")[0]),
                "P_t5_Pa": float(prob.get_val("P_t5")[0]),
                "T_t5_K": float(prob.get_val("T_t5")[0]),
                "NPR": float(prob.get_val("NPR")[0]),
                "V_exit_m_s": float(prob.get_val("V_exit")[0]),
                "T_exit_K": float(prob.get_val("T_exit")[0]),
                "thrust_N": float(prob.get_val("thrust_N")[0]),
                "tsfc_g_kNs": float(prob.get_val("tsfc_g_kNs")[0]),
                "eta_turb": float(prob.get_val("eta_turb")[0]),
            }

    # Run Detailed Cantera Kinetics at Full-Throttle Combustor Conditions (T_t3, P_t3)
    kinetics = _compute_cantera_kinetics(
        mech=mech,
        fuel_sp=fuel_sp,
        T_in=full_point["T_t3_K"],
        P_in=full_point["P_t3_Pa"],
        comb_vol_m3=geom["combustor_vol_cm3"] * 1e-6,
        mdot_air_primary=full_point["mdot_air_kg_s"] * 0.28,
    )

    # Hover endurance with actual CAD fuel mass
    wet_weight_N = geom["wet_mass_g"] * 1e-3 * 9.80665
    twr = full_point["thrust_N"] / max(wet_weight_N, 1e-6)
    hover_thr = float(np.interp(wet_weight_N, od_map["thrust_N"], throttles))
    mdot_f_hover = full_point["mdot_fuel_kg_s"] * (0.28 + 0.72 * (hover_thr ** 1.1))
    endurance_cad_min = (geom["fuel_mass_g"] * 1e-3 / max(mdot_f_hover, 1e-9)) / 60.0

    # Strict Aerospace Verdicts
    t_req = float(pspec.get("max_thrust_N", 11.43))
    checks = {
        "intake_non_choked": {
            "pass": (full_point["M_intake"] <= 0.35 and full_point["eta_intake"] >= 0.94),
            "measured": f"M_in={full_point['M_intake']:.3f}, η_d={full_point['eta_intake']:.3f}",
            "target": "M_in ≤ 0.35, η_d ≥ 0.94",
        },
        "thrust_and_twr": {
            "pass": (full_point["thrust_N"] >= t_req and twr >= 1.80),
            "measured": f"T_net={full_point['thrust_N']:.2f} N, TWR={twr:.2f}, TSFC={full_point['tsfc_g_kNs']:.1f} g/(kN·s)",
            "target": f"T_net ≥ {t_req:.2f} N, TWR ≥ 1.80",
        },
        "combustion_lbo_and_tit": {
            "pass": (full_point["T_t4_K"] <= 1220.0 and (full_point["phi_overall"] / 0.28) > kinetics["phi_lbo"] * 1.25),
            "measured": f"TIT={full_point['T_t4_K']:.1f} K, S_L={kinetics['laminar_flame_speed_m_s']:.2f} m/s, τ_ign={kinetics['ignition_delay_ms']:.2f} ms, φ_LBO={kinetics['phi_lbo']:.3f}",
            "target": "TIT ≤ 1220 K, φ_primary ≥ 1.25×φ_LBO",
        },
        "surge_margin": {
            "pass": (min(od_map["surge_margin_pct"]) >= 12.0),
            "measured": f"Min Surge Margin={min(od_map['surge_margin_pct']):.1f}%, Full={full_point['surge_margin_pct']:.1f}%",
            "target": "Surge Margin ≥ 12.0% across Idle–Max",
        },
        "hover_endurance": {
            "pass": (endurance_cad_min >= 5.0),
            "measured": f"{endurance_cad_min:.2f} min (CAD fuel={geom['fuel_mass_g']:.1f} g)",
            "target": "≥ 5.0 min continuous hover",
        },
    }

    import openmdao as _openmdao_pkg
    summary = {
        "phase": 2,
        "title": "Detailed Combustion Kinetics (Cantera) & Off-Design Cycle (OpenMDAO)",
        "solver": f"Cantera {ct.__version__} ({mech}) + OpenMDAO {_openmdao_pkg.__version__}",
        "verdict": "PASS" if all(c["pass"] for c in checks.values()) else "FAIL",
        "elapsed_sec": round(time.perf_counter() - t0, 2),
        "checks": checks,
        "full_throttle": {k: round(v, 5) if isinstance(v, float) else v for k, v in full_point.items()},
        "twr": round(twr, 3),
        "hover_endurance_min": round(endurance_cad_min, 2),
        "kinetics": {k: v for k, v in kinetics.items() if k != "psr_curve"},
        "off_design_map": od_map,
    }

    store.save_phase(
        "phase02_propulsion",
        summary,
        arrays={
            "throttle": np.array(od_map["throttle"]),
            "rpm": np.array(od_map["rpm"]),
            "thrust_N": np.array(od_map["thrust_N"]),
            "tsfc_g_kNs": np.array(od_map["tsfc_g_kNs"]),
            "EGT_K": np.array(od_map["EGT_K"]),
            "surge_margin_pct": np.array(od_map["surge_margin_pct"]),
        },
    )
    print(
        f"  -> Phase 2 Verdict: {summary['verdict']} ({summary['elapsed_sec']:.2f}s) | "
        f"T_net={full_point['thrust_N']:.2f} N, T_ad={kinetics['T_ad_stoich_K']:.0f} K, "
        f"S_L={kinetics['laminar_flame_speed_m_s']:.2f} m/s, φ_LBO={kinetics['phi_lbo']:.3f}"
    )
    return summary
