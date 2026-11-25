"""
Master 22-Domain Verification Runner for RikiGaku-AHIRU & AHIRU-uTJ42V.
Supports --mode quick (CPU sanity) and --mode colab_a100_heavy (Full NVIDIA A100 GPU workload).
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import time
from typing import Any, Dict, List

from verify_ahiru.cad_spec import run_d01_cad_dmu_tolerance
from verify_ahiru.aero_cfd_thermal import (
    run_d02_cfd_propulsion,
    run_d03_cht_thermal,
    run_d13_ignition_blowout,
    run_d15_ige_hot_gas,
    run_d16_aeroelastic_flutter,
)
from verify_ahiru.structures_rotor_mbd import (
    run_d04_fea_structural,
    run_d05_rotordynamics,
    run_d06_mbd_sph_sloshing,
    run_d14_gyro_precession,
    run_d17_ceramic_bearings,
    run_d18_fuel_cavitation,
)
from verify_ahiru.ee_emc_gnc_sw import (
    run_d07_electronics_spice,
    run_d08_em_emi_emc,
    run_d09_gnc_6dof_montecarlo,
    run_d10_firmware_formal,
    run_d19_battery_electrothermal,
    run_d20_gust_fod_resilience,
    run_d21_sensor_fusion_vibration,
)
from verify_ahiru.systems_dfm_life import (
    run_d11_mbse_fta_fmea,
    run_d12_dfm_slm_cnc,
    run_d22_life_mission_digital_twin,
)


def detect_hardware() -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "platform": platform.platform(),
        "cpu_count": os.cpu_count() or 1,
        "gpu": "None (CPU mode)",
    }
    try:
        import torch
        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            info["gpu"] = f"{props.name} ({props.total_memory / (1024**3):.1f} GB VRAM)"
            info["cuda_version"] = torch.version.cuda
            torch.backends.cuda.matmul.allow_tf32 = True
    except ImportError:
        pass
    return info


def generate_plots(results: List[Dict[str, Any]], out_dir: str) -> str | None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return None

    fig, axes = plt.subplots(2, 2, figsize=(13, 8.5), dpi=150)
    fig.patch.set_facecolor("#ffffff")

    # 1. Verification Runtime & Pass Status across all 22 Domains
    ax = axes[0, 0]
    labels = [r["domain"] for r in results]
    times = [r["elapsed_s"] for r in results]
    colors = ["#059669" if r["passed"] else "#dc2626" for r in results]
    ax.bar(labels, times, color=colors, edgecolor="#0f172a", linewidth=0.5)
    ax.set_title("22-Domain Verification Execution Time & Pass Gate", fontsize=11, fontweight="bold")
    ax.set_ylabel("Seconds")
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    ax.grid(axis="y", alpha=0.25)

    # 2. Campbell Diagram (D05)
    ax = axes[0, 1]
    d05 = next(r for r in results if r["domain"] == "D05")["metrics"]
    rpm = np.linspace(0, 320, 100)
    ax.plot(rpm, (rpm * 1000.0) / 60.0, "--", color="#dc2626", lw=1.6, label="1X Synchronous Excitation (Hz)")
    ax.axhline(d05["crit_1_bounce_rpm"] / 60.0, color="#2563eb", lw=2.0, label="1st Rigid Bounce Mode")
    ax.axhline(d05["crit_2_bending_rpm"] / 60.0, color="#059669", lw=2.0, label="1st Elastic Bending Mode")
    ax.axvspan(120, 225, color="#fef3c7", alpha=0.65, label="Steady Operating Band (120k-225k)")
    ax.set_title("D05 Campbell Diagram (0 - 320k RPM)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Rotor Speed [kRPM]")
    ax.set_ylabel("Frequency [Hz]")
    ax.legend(fontsize=7.5, loc="upper left")
    ax.grid(alpha=0.25)

    # 3. Thermodynamic Temperature Cascade vs Material Limits (D02 / D03)
    ax = axes[1, 0]
    d03 = next(r for r in results if r["domain"] == "D03")["metrics"]
    stages = ["Combustor\n(Inconel 718)", "Aerogel Out\n(ZrO2+Au)", "FADEC IC\n(Head)", "Battery\n(3S LiHV)", "Outer Shell\n(Touch)"]
    temps = [d03["combustor_wall_c"], d03["aerogel_outer_c"], d03["fadec_junction_c"], d03["battery_peak_c"], d03["duck_shell_touch_c"]]
    limits = [980.0, 450.0, 105.0, 65.0, 60.0]
    x = np.arange(len(stages))
    ax.bar(x - 0.18, temps, 0.35, color="#ea580c", label="Simulated Peak [C]")
    ax.bar(x + 0.18, limits, 0.35, color="#94a3b8", label="Safe Material Limit [C]")
    ax.set_xticks(x)
    ax.set_xticklabels(stages, fontsize=8)
    ax.set_yscale("log")
    ax.set_title("D03 Conjugate Heat Transfer vs Thermal Limits", fontsize=11, fontweight="bold")
    ax.set_ylabel("Temperature [C] (log)")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.25)

    # 4. Structural Safety Factors & Control Margins (D01, D04, D14, D16, D20)
    ax = axes[1, 1]
    d01 = next(r for r in results if r["domain"] == "D01")["metrics"]
    d04 = next(r for r in results if r["domain"] == "D04")["metrics"]
    d14 = next(r for r in results if r["domain"] == "D14")["metrics"]
    d16 = next(r for r in results if r["domain"] == "D16")["metrics"]
    sf_names = ["Comp\n110% FEA", "Turbine\n110% FEA", "1.5m Drop\nStruts", "Blade\nContain", "Gimbal\nvs Gyro", "Flutter\nMargin", "Comp 6σ\nCpk"]
    sf_vals = [
        d04["compressor_sf"], d04["turbine_sf"], d04["strut_absorb_margin"],
        d04["containment_sf"], d14["gimbal_gyro_margin"], d16["flutter_safety_factor"], d01["comp_cpk"]
    ]
    ax.barh(sf_names, sf_vals, color="#0284c7", edgecolor="#0f172a", linewidth=0.5)
    ax.axvline(1.0, color="#dc2626", linestyle="--", lw=1.5, label="Failure Threshold (1.0x)")
    ax.set_title("Safety Factors & Statistical Capability Across Physics Domains", fontsize=11, fontweight="bold")
    ax.set_xlabel("Safety Factor / Cpk")
    ax.legend(fontsize=8)
    ax.grid(axis="x", alpha=0.25)

    plt.tight_layout()
    plot_path = os.path.join(out_dir, "ahiru_verification_dashboard.png")
    plt.savefig(plot_path, dpi=150)
    plt.close(fig)
    return plot_path


def write_html_report(results: List[Dict[str, Any]], hw: Dict[str, Any], out_dir: str) -> str:
    all_pass = all(r["passed"] for r in results)
    rows = []
    for r in results:
        badge = '<span style="color:#047857;font-weight:700;">PASS</span>' if r["passed"] else '<span style="color:#dc2626;font-weight:700;">FAIL</span>'
        m_str = ", ".join(f"<code>{k}={v}</code>" for k, v in list(r["metrics"].items())[:5])
        rows.append(f"<tr><td><b>{r['domain']}</b></td><td>{r['name']}</td><td>{badge}</td><td>{r['backend']}</td><td>{r['elapsed_s']:.3f}s</td><td>{m_str}</td></tr>")

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>RikiGaku-AHIRU 22-Domain Verification Report</title>
<style>
body {{ font-family: system-ui, -apple-system, sans-serif; margin: 28px; color: #0f172a; background: #fff; }}
table {{ border-collapse: collapse; width: 100%; font-size: 13px; margin-top: 16px; }}
th, td {{ border: 1px solid #e2e8f0; padding: 8px 10px; text-align: left; vertical-align: top; }}
th {{ background: #f8fafc; }}
code {{ background: #f1f5f9; padding: 1px 4px; border-radius: 3px; font-size: 11.5px; }}
</style></head><body>
<h1>RikiGaku-AHIRU (AHIRU-μTJ42V) — 22-Domain Physical Verification Certificate</h1>
<p><b>Overall Status:</b> {"ALL 22 DOMAINS PASSED (100%)" if all_pass else "FAILED"} | <b>Hardware:</b> {hw['gpu']} | <b>CPUs:</b> {hw['cpu_count']}</p>
<table><thead><tr><th>ID</th><th>Domain</th><th>Gate</th><th>Solver Backend</th><th>Time</th><th>Key Physical Metrics</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></body></html>"""

    path = os.path.join(out_dir, "certification_report.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


def run_all(mode: str = "quick", out_dir: str = "reports") -> Dict[str, Any]:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    out_abs = os.path.abspath(os.path.join(repo_root, out_dir))
    export_dir = os.path.join(out_abs, "exports")
    os.makedirs(export_dir, exist_ok=True)

    hw = detect_hardware()
    print("=" * 84)
    print(f"RikiGaku-AHIRU 22-Domain Physical Verification Suite | mode={mode}")
    print(f"Hardware: GPU={hw['gpu']} | CPUs={hw['cpu_count']}")
    print("=" * 84)

    t_start = time.perf_counter()
    results = [
        run_d01_cad_dmu_tolerance(mode, export_dir),
        run_d02_cfd_propulsion(mode, export_dir),
        run_d03_cht_thermal(mode, export_dir),
        run_d04_fea_structural(mode, export_dir),
        run_d05_rotordynamics(mode, export_dir),
        run_d06_mbd_sph_sloshing(mode, export_dir),
        run_d07_electronics_spice(mode, export_dir),
        run_d08_em_emi_emc(mode),
        run_d09_gnc_6dof_montecarlo(mode),
        run_d10_firmware_formal(repo_root),
        run_d11_mbse_fta_fmea(mode, export_dir),
        run_d12_dfm_slm_cnc(mode, export_dir),
        run_d13_ignition_blowout(mode),
        run_d14_gyro_precession(mode),
        run_d15_ige_hot_gas(mode),
        run_d16_aeroelastic_flutter(mode),
        run_d17_ceramic_bearings(mode),
        run_d18_fuel_cavitation(mode),
        run_d19_battery_electrothermal(mode),
        run_d20_gust_fod_resilience(mode),
        run_d21_sensor_fusion_vibration(mode),
        run_d22_life_mission_digital_twin(mode),
    ]

    for r in results:
        tag = "PASS" if r["passed"] else "FAIL"
        print(f"[{tag}] {r['domain']} | {r['name']} ({r['elapsed_s']:.3f}s) -> {r['backend']}")
        if not r["passed"]:
            print("   FAIL METRICS:", r["metrics"])

    total_s = round(time.perf_counter() - t_start, 3)
    passed_count = sum(1 for r in results if r["passed"])
    all_passed = passed_count == len(results)

    summary = {
        "all_passed": all_passed,
        "passed_count": passed_count,
        "total_domains": len(results),
        "total_elapsed_s": total_s,
        "mode": mode,
        "hardware": hw,
        "results": results,
    }
    with open(os.path.join(out_abs, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    html_path = write_html_report(results, hw, out_abs)
    plot_path = generate_plots(results, out_abs)

    print("=" * 84)
    print(f"RESULT: {passed_count}/{len(results)} DOMAINS PASSED in {total_s:.2f}s | Report: {html_path}")
    if plot_path:
        print(f"Dashboard Plot: {plot_path}")
    print("=" * 84)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run RikiGaku-AHIRU 22-domain physical verification.")
    parser.add_argument("--mode", choices=["quick", "colab_a100_heavy"], default="quick")
    parser.add_argument("--out", default="reports")
    args = parser.parse_args()
    res = run_all(mode=args.mode, out_dir=args.out)
    raise SystemExit(0 if res["all_passed"] else 1)
