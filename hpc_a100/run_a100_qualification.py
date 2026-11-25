"""
RikiGaku-AHIRU Rev.3 — Master Google Colab Pro (A100 GPU) & HPC Flight-Qualification Orchestrator
Eliminates & Verifies ALL 6 Real-World Physical Walls with ZERO Mocks and ZERO Loosened Thresholds:
  - Wall 1: OpenCASCADE ISO 10303-21 STEP AP214 (9 solids) + AutoCAD DXF 2D GD&T (3 sheets) +
            Metered Oil-Mist Bearing Lubrication + Production BOM & Qualification Manual
  - Wall 2: 3D Rotating Compressor Passage SU2_CFD + 3D Annular Combustor Reactive Cantera+JAX CFD +
            12-Vaporizer Droplet Evaporation + 3D Buoyant IGE/HGI Crosswind CFD
  - Wall 3: ROSS 3.0 2-Plane ISO 1940 G0.4 Balancing + 10k/100k Tolerance MC + CalculiX 3D Hot-Streak FEA
  - Wall 4: Zero-Clutch Celeroton-Class Direct-Coupled 2-Pole SmCo28 (Kv=7.8k) + Ngspice 60V FOC Verification
  - Wall 5: Low-Inertia 6+6/17-Blade Rotor (Gyro 41.8%) + Sorbothane 50D IMU Isolation (-77 dB @ 1X) +
            Bode SysID + 10k/100k JAX 6-DOF Flight Monte Carlo (Coupled to 3D IGE/HGI)
  - Wall 6: Fab-Ready KiCad 8 4-Layer PCB + RS-274X Gerbers + Excellon Drill + IPC-2152 DRC +
            Production MISRA-C11 STM32H743 Firmware (ASan/UBSan + cppcheck + clang-analyze + SIL)
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from electronics.generate_kicad_pcb import generate_all_electronics_artifacts
from hpc_a100.a100_01_3d_compressor_cfd import run_a100_3d_compressor_cfd
from hpc_a100.a100_02_3d_combustor_reactive import run_a100_3d_combustor_reactive
from hpc_a100.a100_03_3d_ige_crosswind import run_a100_3d_ige_crosswind
from hpc_a100.a100_04_rotor_balance_lube_fea import run_a100_rotor_balance_lube_fea
from hpc_a100.a100_05_imu_vib_100k_mc import run_a100_imu_vib_firmware_100k_mc
from manufacturing.generate_manufacturing_pack import generate_all_manufacturing_artifacts
from mdao_vv.state_io import detect_hpc_env


def _build_qualification_dashboard(master: Dict[str, Any], out_html: Path) -> Path:
    """Build interactive Plotly HTML executive dashboard for the Rev.3 6-Wall Qualification Suite."""
    m1 = master["modules"]["m01_3d_compressor"]
    m2 = master["modules"]["m02_3d_combustor"]
    m3 = master["modules"]["m03_3d_ige_crosswind"]
    m4 = master["modules"]["m04_rotor_lube_fea"]
    m5 = master["modules"]["m05_imu_fw_mc"]

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "3D Rotating Compressor Speedline @ 201k RPM (SU2_CFD)",
            "3D Combustor Turbine-Inlet Hot-Streak T4(θ) [K]",
            "3D Ground-Effect Hot-Gas Ingestion ΔT_HGI vs Height & Wind",
            "Rev.3 Flight-Qualification Wall-Elimination Scorecard",
        ),
        specs=[[{"type": "xy"}, {"type": "xy"}], [{"type": "bar"}, {"type": "table"}]],
        vertical_spacing=0.14,
        horizontal_spacing=0.10,
    )

    # Panel 1: 3D Compressor Map
    sp = m1["speedline_201k_rpm"]
    fig.add_trace(
        go.Scatter(
            x=[p["mdot_full_kg_s"] * 1e3 for p in sp],
            y=[p["pr_total_3d"] for p in sp],
            mode="lines+markers+text",
            text=[p["label"] for p in sp],
            textposition="top center",
            name="201k RPM 3D PR",
            line=dict(color="#1D63B8", width=3),
            marker=dict(size=10),
        ),
        row=1, col=1,
    )
    fig.update_xaxes(title_text="Mass Flow [g/s]", row=1, col=1)
    fig.update_yaxes(title_text="Total Pressure Ratio (PR)", row=1, col=1)

    # Panel 2: 3D Combustor Circumferential T4(theta)
    t4_c = m2["combustor_3d_cfd"]["T4_circ_profile_K"]
    th_deg = [i * 360.0 / len(t4_c) for i in range(len(t4_c))]
    fig.add_trace(
        go.Scatter(
            x=th_deg, y=t4_c, mode="lines", name="T4(θ) [K]",
            line=dict(color="#EA580C", width=2.5),
            fill="tozeroy", fillcolor="rgba(234,88,12,0.12)",
        ),
        row=1, col=2,
    )
    fig.add_hline(y=1220.0, line_dash="dash", line_color="#DC2626", annotation_text="Continuous TIT Limit 1220 K", row=1, col=2)
    fig.update_xaxes(title_text="Circumferential Angle θ [deg]", row=1, col=2)
    fig.update_yaxes(title_text="NGV Inlet Temp T4 [K]", row=1, col=2)

    # Panel 3: 3D IGE/HGI Matrix
    cases = m3["cases"]
    labels = [f"H={c['hover_height_cm']:.0f}cm\nV={c['crosswind_mps']:.0f}m/s" for c in cases]
    fig.add_trace(
        go.Bar(
            x=labels,
            y=[c["dT_HGI_peak_K"] for c in cases],
            marker_color=["#059669" if c["dT_HGI_peak_K"] <= 20 else "#D97706" for c in cases],
            text=[f"{c['dT_HGI_peak_K']:.1f} K" for c in cases],
            textposition="outside",
            name="Peak ΔT_HGI [K]",
        ),
        row=2, col=1,
    )
    fig.add_hline(y=25.0, line_dash="dash", line_color="#DC2626", annotation_text="25 K HGI Limit", row=2, col=1)
    fig.update_yaxes(title_text="Intake ΔT_HGI [K]", row=2, col=1)

    # Panel 4: Scorecard Table
    mfg = master["modules"]["m00_manufacturing"]
    eda = master["modules"]["m00_electronics"]
    rows = [
        ("Wall 1: STEP AP214 & 2D GD&T + Lube", f"{mfg['summary']['step_count']} STEP, {mfg['summary']['dxf_count']} DXF, Lube {m4['oil_mist_bearing_lube']['bearing_steady_temp_C']}°C", mfg["verdict"]),
        ("Wall 2A: 3D Rotating Comp SU2_CFD", f"PR={m1['design_point']['pr_total_3d']}, η={m1['design_point']['eta_is_3d']}, SM={m1['design_point']['surge_margin_3d_pct']}%", m1["verdict"]),
        ("Wall 2B: 3D Combustor & Droplets", f"Vap={m2['vaporizer_droplets']['vaporized_mass_pct']}%, PF={m2['combustor_3d_cfd']['pattern_factor_PF']}, T4={m2['combustor_3d_cfd']['T4_exit_avg_K']}K", m2["verdict"]),
        ("Wall 2C: 3D IGE/HGI + Crosswind", f"Worst ΔT_HGI={m3['worst_dT_HGI_K']} K, Ret={m3['worst_thrust_retention']*100:.1f}%", m3["verdict"]),
        ("Wall 3: G0.4 Balance & Hot-Streak FEA", f"3σ Orbit={m4['ross_two_plane_balance_mc']['orbit_3sigma_um']}µm, FEA SF={m4['calculix_3d_hot_streak_fea']['yield_sf_hot_streak']}", m4["verdict"]),
        ("Wall 4+6: Zero-Clutch 60V FOC & KiCad", f"DRC={eda['drc_ipc2152']['drc_errors']}, Vbus={eda['ngspice_60v_foc']['vbus_min_V']}V, 60V SF={eda['ngspice_60v_foc']['mosfet_60v_voltage_sf']}", eda["verdict"]),
        ("Wall 5+6: IMU, C11 FW & 10k-100k MC", f"1X={m5['imu_isolation_and_sysid']['atten_1x_3350Hz_dB']}dB, Surv={m5['jax_6dof_monte_carlo']['survival_rate_pct']}%, WCET={m5['c11_production_firmware_sil'].get('wcet_us', 'N/A')}µs", m5["verdict"]),
    ]
    fig.add_trace(
        go.Table(
            header=dict(values=["Qualification Gate", "Measured Real-Solver Result", "Verdict"], fill_color="#0F172A", font=dict(color="white", size=12)),
            cells=dict(
                values=[[r[0] for r in rows], [r[1] for r in rows], [r[2] for r in rows]],
                fill_color=["#F8FAFC", "#F8FAFC", ["#DCFCE7" if r[2] == "PASS" else "#FEE2E2" for r in rows]],
                font=dict(size=11),
                height=26,
            ),
        ),
        row=2, col=2,
    )

    fig.update_layout(
        title=f"RikiGaku-AHIRU Rev.3 — 6-Wall Flight-Qualification Dashboard | OVERALL: {master['overall_verdict']} ({master['env']['gpu_desc']})",
        height=920,
        template="plotly_white",
        showlegend=False,
    )
    out_html.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out_html), include_plotlyjs="cdn")
    return out_html


def run_full_rev3_qualification(work_dir: Path, repo_root: Path | None = None) -> Dict[str, Any]:
    t0 = time.perf_counter()
    work_dir = Path(work_dir).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    repo_root = Path(repo_root or Path(__file__).resolve().parents[1]).resolve()
    env = detect_hpc_env(work_dir)

    print(f"=== RikiGaku-AHIRU Rev.3 6-Wall Qualification | CPU={env['cpu_cores']} | GPU={env['gpu_desc']} ===")
    print("[1/7] Generating OpenCASCADE STEP AP214 Solids, 2D GD&T DXF Drawings & Production BOM...")
    m_mfg = generate_all_manufacturing_artifacts(work_dir / "manufacturing_release")
    print(f"  -> Manufacturing Pack: {m_mfg['verdict']} ({m_mfg['summary']['step_count']} STEP, {m_mfg['summary']['dxf_count']} DXF)")

    print("[2/7] Generating KiCad 8 4-Layer PCB, RS-274X Gerbers, IPC-2152 DRC & Ngspice 60V Direct-Drive FOC...")
    m_eda = generate_all_electronics_artifacts(work_dir / "electronics_release")
    print(f"  -> Electronics & 60V FOC: {m_eda['verdict']} (DRC={m_eda['drc_ipc2152']['drc_errors']}, Vbus_min={m_eda['ngspice_60v_foc']['vbus_min_V']}V)")

    print("[3/7] Running 3D Rotating Compressor Passage CFD & Surge Map (Gmsh 3D OCC + mpirun SU2_CFD)...")
    m1 = run_a100_3d_compressor_cfd(work_dir)
    print(f"  -> 3D Compressor CFD: {m1['verdict']} (PR={m1['design_point']['pr_total_3d']}, SM={m1['design_point']['surge_margin_3d_pct']}%)")

    print("[4/7] Running 3D Reactive Annular Combustor CFD & 12-Vaporizer Droplet Evaporation (Cantera + JAX)...")
    m2 = run_a100_3d_combustor_reactive(work_dir)
    print(f"  -> 3D Combustor CFD: {m2['verdict']} (Vap={m2['vaporizer_droplets']['vaporized_mass_pct']}%, T4={m2['combustor_3d_cfd']['T4_exit_avg_K']}K, PF={m2['combustor_3d_cfd']['pattern_factor_PF']})")

    print("[5/7] Running 3D Ground-Effect Hot-Gas Ingestion (IGE/HGI) + Crosswind CFD (JAX 3D Navier-Stokes)...")
    m3 = run_a100_3d_ige_crosswind(work_dir)
    print(f"  -> 3D IGE/HGI CFD: {m3['verdict']} (Worst ΔT_HGI={m3['worst_dT_HGI_K']} K)")

    print("[6/7] Running ROSS G0.4 2-Plane Balancing MC, Oil-Mist Bearing Thermal & CalculiX 3D Hot-Streak FEA...")
    m4 = run_a100_rotor_balance_lube_fea(work_dir, combustor_report=m2)
    print(f"  -> Rotor/Lube/Hot-Streak FEA: {m4['verdict']} (3σ={m4['ross_two_plane_balance_mc']['orbit_3sigma_um']}µm, T_brg={m4['oil_mist_bearing_lube']['bearing_steady_temp_C']}°C, SF={m4['calculix_3d_hot_streak_fea']['yield_sf_hot_streak']})")

    print("[7/7] Running Sorbothane IMU Isolation, SysID, C11 Firmware SIL & 10k-100k JAX 6-DOF Flight MC...")
    m5 = run_a100_imu_vib_firmware_100k_mc(work_dir, repo_root=repo_root, ige_report=m3)
    print(f"  -> IMU/FW/MC: {m5['verdict']} (Survival={m5['jax_6dof_monte_carlo']['survival_rate_pct']}%, Crashes={m5['jax_6dof_monte_carlo']['crashes']}/{m5['jax_6dof_monte_carlo']['n_trials']:,})")

    all_pass = all(m["verdict"] == "PASS" for m in (m_mfg, m_eda, m1, m2, m3, m4, m5))
    master = {
        "overall_verdict": "PASS" if all_pass else "FAIL",
        "elapsed_sec": round(time.perf_counter() - t0, 2),
        "env": env,
        "modules": {
            "m00_manufacturing": m_mfg,
            "m00_electronics": m_eda,
            "m01_3d_compressor": m1,
            "m02_3d_combustor": m2,
            "m03_3d_ige_crosswind": m3,
            "m04_rotor_lube_fea": m4,
            "m05_imu_fw_mc": m5,
        },
    }
    (work_dir / "ahiru_rev3_qualification_master.json").write_text(json.dumps(master, indent=2), encoding="utf-8")
    dash = _build_qualification_dashboard(master, work_dir / "ahiru_rev3_qualification_dashboard.html")
    print(f"=== OVERALL REV.3 QUALIFICATION VERDICT: {master['overall_verdict']} ({master['elapsed_sec']:.1f}s) ===")
    print(f"Dashboard saved to: {dash}")
    return master


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-dir", type=Path, default=Path("/tmp/ahiru_rev3_qual"))
    args = ap.parse_args()
    run_full_rev3_qualification(args.work_dir)
