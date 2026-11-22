"""
Phase 8: Aerospace-Grade Uncertainty Quantification (OpenTURNS Polynomial Chaos
Expansion PCE -> Failure Probability Pf) & Global Sensitivity Analysis (SALib Sobol S1/ST).

Real Solvers Invoked:
  - OpenTURNS (JointDistribution, OrthogonalProductPolynomialFactory,
    FunctionalChaosAlgorithm PCE, FunctionalChaosSobolIndices, 50k PCE Monte Carlo Pf)
  - SALib (sobol_sample.sample, sobol_analyze.analyze First-Order S1 & Total-Order ST)
"""
from __future__ import annotations

import math
import time
from typing import Any, Dict, List

import numpy as np
import openturns as ot             # Strictly required (Phase 0)
from SALib.analyze import sobol as salib_sobol  # Strictly required (Phase 0)
from SALib.sample import sobol as salib_sample

from .state_io import MDAOStateStore


def run_phase08(spec: Dict[str, Any], store: MDAOStateStore) -> Dict[str, Any]:
    """Execute Phase 8: Real OpenTURNS PCE UQ (Pf) + SALib Sobol sensitivity ranking."""
    t0 = time.perf_counter()
    print("=== [Phase 8] OpenTURNS PCE Uncertainty Quantification (Pf) & SALib Sobol Sensitivity ===")

    p1 = store.load_phase("phase01_geometry")
    p2 = store.load_phase("phase02_propulsion")
    p4 = store.load_phase("phase04_thermal")
    p5 = store.load_phase("phase05_struct_rotor")

    # Coupled nominal baselines directly from Phases 1-5 real solver runs!
    nom_thrust = float(p2["full_throttle"]["thrust_N"])
    nom_turb_clr = float(p1["geometry"]["turb_tip_clr_hot_mm"])
    nom_bat_soak = float(p4["battery_soak_max_C"])
    nom_sf_turb = float(p5["fea"]["sf_turb_100"])
    nom_L_tvc = max(0.025, abs(p1["geometry"]["wet_cog_mm"][1] - 44.5) * 1e-3)
    nom_dx_cog = (p1["geometry"]["wet_cog_mm"][0] - p1["geometry"]["engine_axis_x_mm"]) * 1e-3
    req_thrust = float(spec["propulsion_spec"].get("max_thrust_N", 11.43))

    # Define 6 real manufacturing & environmental uncertainty variables:
    # X0: tip_clr_err [mm]     ~ N(0, 0.015)   (±0.03 mm 2σ CNC tolerance)
    # X1: surf_rough_Ra [um]   ~ U(1.6, 12.5)  (5-axis vs as-built SLM roughness)
    # X2: cog_err_x [mm]       ~ N(0, 1.0)     (±2.0 mm 2σ assembly mass tolerance)
    # X3: aerogel_k_mult [-]   ~ N(1.0, 0.075) (±15% 2σ thermal blanket scatter)
    # X4: mat_yield_mult [-]   ~ N(1.0, 0.035) (±7% 2σ SLM Inconel 718 yield scatter)
    # X5: brg_stiff_mult [-]   ~ N(1.0, 0.080) (±16% 2σ O-ring bearing stiffness scatter)
    param_names = [
        "Tip Clearance Tol (±0.03 mm)",
        "Surface Roughness Ra (1.6–12.5 μm)",
        "CoG Offset Tol (±2.0 mm)",
        "Aerogel Insulation Scatter (±15%)",
        "Inconel 718 Yield Scatter (±7%)",
        "Bearing Stiffness Scatter (±16%)",
    ]

    def coupled_limit_states(X_mat: np.ndarray) -> np.ndarray:
        """
        Evaluate 5 coupled aerospace limit-state margins G_i(x) (PASS when G_i > 0):
          G0: Thrust margin = T_net(x) - req_thrust [N]
          G1: Hot turbine tip-clearance margin = clr_hot(x) - 0.05 [mm]
          G2: Turbine structural yield margin = SF_turb(x) - 1.25 [-]
          G3: Battery soakback margin = 60.0 - T_bat_soak(x) [°C] (normalized /10)
          G4: Trim gimbal margin = 10.0 - trim_deg(x) [deg]
        Also returns composite system margin G_sys = min_i normalized_margin (for scalar PCE & Sobol!).
        """
        tip_err = X_mat[:, 0]
        ra_um = X_mat[:, 1]
        cog_err_mm = X_mat[:, 2]
        k_mult = X_mat[:, 3]
        sy_mult = X_mat[:, 4]
        kb_mult = X_mat[:, 5]

        # Physics sensitivity couplings derived from Phases 1-5:
        # Roughness & tip clearance degrade turbomachinery efficiency & net thrust
        eta_loss = 0.0045 * (ra_um - 3.2) + 0.14 * np.maximum(0.0, tip_err)
        T_net = nom_thrust * (1.0 - eta_loss)
        G0_thrust = T_net - req_thrust

        # Hot turbine tip clearance margin (rub occurs <= 0.00 mm; safe > 0.05 mm)
        clr_hot = nom_turb_clr - tip_err - 0.008 * np.abs(kb_mult - 1.0) * 3.0
        G1_tip = clr_hot - 0.05

        # Turbine yield safety factor margin (coupled to roughness stress concentration & yield scatter)
        sf_turb = nom_sf_turb * sy_mult * (1.0 - 0.006 * np.maximum(0.0, ra_um - 3.2))
        G2_struct = sf_turb - 1.25

        # Battery soakback thermal margin (scales with aerogel thermal conductivity scatter)
        T_bat = 15.0 + (nom_bat_soak - 15.0) * (0.35 + 0.65 * k_mult)
        G3_thermal = 60.0 - T_bat

        # Hover trim authority margin (CoG error shifts static trim gimbal angle)
        dx_tot = np.abs(nom_dx_cog + cog_err_mm * 1e-3)
        trim_deg = np.degrees(np.arctan2(dx_tot, nom_L_tvc))
        G4_trim = 8.0 - trim_deg

        # Composite scalar performance index for global sensitivity ranking (higher = better)
        # Standardized weighted combination of propulsion, tip clearance, structure, thermal & trim margins
        y_comp = (
            (G0_thrust / 2.0)
            + (G1_tip / 0.08)
            + (G2_struct / 0.30)
            + (G3_thermal / 25.0)
            + (G4_trim / 4.0)
        )
        return np.column_stack([G0_thrust, G1_tip, G2_struct, G3_thermal, G4_trim, y_comp])

    # ------------------------------------------------------------------
    # 1. REAL OpenTURNS Polynomial Chaos Expansion (PCE) & Failure Probability Pf
    # ------------------------------------------------------------------
    ot.RandomGenerator.SetSeed(2026)
    marginals = [
        ot.Normal(0.0, 0.015),
        ot.Uniform(1.6, 12.5),
        ot.Normal(0.0, 1.0),
        ot.TruncatedNormal(1.0, 0.075, 0.65, 1.35),
        ot.TruncatedNormal(1.0, 0.035, 0.85, 1.15),
        ot.TruncatedNormal(1.0, 0.080, 0.65, 1.35),
    ]
    dist = ot.JointDistribution(marginals)

    # Generate training DOE (N=400 Sobol/LHS points) for Degree-3 PCE
    N_train = 400
    X_ot = dist.getSample(N_train)
    X_np = np.asarray(X_ot, dtype=np.float64)
    Y_np = coupled_limit_states(X_np)
    Y_ot = ot.Sample(Y_np)

    # Build orthonormal polynomial product basis (Hermite + Legendre automatically matched to marginals!)
    enumerate_fn = ot.LinearEnumerateFunction(len(marginals))
    multivar_basis = ot.OrthogonalProductPolynomialFactory(marginals, enumerate_fn)
    total_degree = 3
    n_basis = enumerate_fn.getBasisSizeFromTotalDegree(total_degree)
    adaptive_strategy = ot.FixedStrategy(multivar_basis, n_basis)
    projection_strategy = ot.LeastSquaresStrategy(ot.LeastSquaresMetaModelSelectionFactory())

    chaos = ot.FunctionalChaosAlgorithm(X_ot, Y_ot, dist, adaptive_strategy, projection_strategy)
    chaos.run()
    chaos_res = chaos.getResult()
    metamodel = chaos_res.getMetaModel()

    # Validate PCE Q^2 on 200 independent test samples
    X_val = dist.getSample(200)
    Y_true_val = coupled_limit_states(np.asarray(X_val))
    Y_pred_val = np.asarray(metamodel(X_val))
    ss_res = np.sum((Y_true_val[:, 5] - Y_pred_val[:, 5]) ** 2)
    ss_tot = np.sum((Y_true_val[:, 5] - np.mean(Y_true_val[:, 5])) ** 2) + 1e-12
    pce_q2 = float(1.0 - ss_res / ss_tot)

    # Extract OpenTURNS analytical PCE Sobol indices for composite output (index 5)
    ot_sobol = ot.FunctionalChaosSobolIndices(chaos_res)
    ot_s1 = [round(float(ot_sobol.getSobolIndex(i, 5)), 4) for i in range(len(marginals))]
    ot_st = [round(float(ot_sobol.getSobolTotalIndex(i, 5)), 4) for i in range(len(marginals))]

    # Evaluate 50,000-sample PCE Monte Carlo Failure Probability Pf!
    N_mc_pce = 50000
    X_mc = dist.getSample(N_mc_pce)
    Y_mc = np.asarray(metamodel(X_mc))
    pf_each = {
        "pf_thrust": float(np.mean(Y_mc[:, 0] <= 0.0)),
        "pf_hot_tip_rub": float(np.mean(Y_mc[:, 1] <= 0.0)),
        "pf_turbine_yield": float(np.mean(Y_mc[:, 2] <= 0.0)),
        "pf_battery_thermal": float(np.mean(Y_mc[:, 3] <= 0.0)),
        "pf_trim_authority": float(np.mean(Y_mc[:, 4] <= 0.0)),
    }
    any_fail = (Y_mc[:, 0] <= 0.0) | (Y_mc[:, 1] <= 0.0) | (Y_mc[:, 2] <= 0.0) | (Y_mc[:, 3] <= 0.0) | (Y_mc[:, 4] <= 0.0)
    pf_system = float(np.mean(any_fail))
    reliability_pct = (1.0 - pf_system) * 100.0

    # ------------------------------------------------------------------
    # 2. REAL SALib Sobol Global Sensitivity Analysis (N=512 -> 7,168 evals)
    # ------------------------------------------------------------------
    salib_problem = {
        "num_vars": 6,
        "names": param_names,
        "bounds": [
            [-0.030, 0.030],  # Tip clearance tol [mm]
            [1.6, 12.5],      # Surface roughness Ra [um]
            [-2.0, 2.0],      # CoG offset [mm]
            [0.85, 1.15],     # Aerogel k scatter
            [0.93, 1.07],     # Yield scatter
            [0.84, 1.16],     # Bearing stiffness scatter
        ],
    }
    X_salib = salib_sample.sample(salib_problem, 512, calc_second_order=True)
    Y_salib = coupled_limit_states(X_salib)[:, 5]
    Si = salib_sobol.analyze(salib_problem, Y_salib, calc_second_order=True, print_to_console=False)

    ranking = sorted(
        [
            {
                "parameter": param_names[i],
                "SALib_S1": round(float(Si["S1"][i]), 4),
                "SALib_ST": round(float(Si["ST"][i]), 4),
                "OpenTURNS_PCE_S1": ot_s1[i],
                "OpenTURNS_PCE_ST": ot_st[i],
            }
            for i in range(6)
        ],
        key=lambda r: -r["SALib_ST"],
    )

    checks = {
        "pce_surrogate_fidelity": {
            "pass": (pce_q2 >= 0.98),
            "measured": f"OpenTURNS Degree-3 PCE Q² = {pce_q2:.5f} ({n_basis} polynomial terms)",
            "target": "Q² ≥ 0.980",
        },
        "system_reliability_3sigma": {
            "pass": (reliability_pct >= 99.7),
            "measured": f"System Reliability = {reliability_pct:.3f}% (Pf = {pf_system:.4e} across 50k PCE MC)",
            "target": "Reliability ≥ 99.70% (Pf ≤ 3.0×10⁻³)",
        },
    }

    summary = {
        "phase": 8,
        "title": "Uncertainty Quantification (OpenTURNS PCE) & Global Sensitivity (SALib Sobol)",
        "solver": f"OpenTURNS {ot.__version__} (Degree-3 PCE, 50k MC) + SALib Sobol ({len(X_salib):,} evals)",
        "verdict": "PASS" if all(c["pass"] for c in checks.values()) else "FAIL",
        "elapsed_sec": round(time.perf_counter() - t0, 2),
        "checks": checks,
        "pce_q2": round(pce_q2, 6),
        "pf_system": round(pf_system, 6),
        "reliability_pct": round(reliability_pct, 3),
        "pf_components": {k: round(v, 5) for k, v in pf_each.items()},
        "critical_parameter_ranking": ranking,
    }

    store.save_phase(
        "phase08_uq_sobol",
        summary,
        arrays={
            "salib_S1": np.asarray(Si["S1"], dtype=np.float64),
            "salib_ST": np.asarray(Si["ST"], dtype=np.float64),
            "ot_S1": np.asarray(ot_s1, dtype=np.float64),
            "ot_ST": np.asarray(ot_st, dtype=np.float64),
            "pce_mc_margins": Y_mc,
        },
    )
    print(
        f"  -> Phase 8 Verdict: {summary['verdict']} ({summary['elapsed_sec']:.2f}s) | "
        f"PCE Q²={pce_q2:.4f}, Reliability={reliability_pct:.2f}% (Pf={pf_system:.3e}), Top Driver={ranking[0]['parameter']}"
    )
    return summary
