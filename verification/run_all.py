"""
Master One-Click 12-Domain Verification Orchestrator for RikiGaku-AHIRU (AHIRU-μTJ42V).

Usage (CLI or Google Colab Pro A100):
    python3 -m verification.run_all --html index.html --out verification_out
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .cad_loader import CADAssembly, load_cad_assembly
from .config import detect_compute_environment
from .domain01_cad_dmu import run_domain01
from .domain02_cfd_propulsion import run_domain02
from .domain03_thermal_cht import run_domain03
from .domain04_structural_fea import run_domain04
from .domain05_rotordynamics_caa import run_domain05
from .domain06_mbd_sloshing import run_domain06
from .domain07_eda_spice import run_domain07
from .domain08_em_emc import run_domain08
from .domain09_gnc_6dof import run_domain09
from .domain10_software_formal import run_domain10
from .domain11_mbse_rams import run_domain11
from .domain12_dfm_cam import run_domain12
from .reporting import generate_reports
from .schema import DomainReport, Verdict


def run_full_verification(
    html_path: str | Path = "index.html",
    out_dir: str | Path = "verification_out",
    verbose: bool = True,
) -> Tuple[CADAssembly, List[DomainReport], Dict[str, Path]]:
    """Execute Step 0 CAD extraction + all 12 aerospace verification domains end-to-end."""
    t_start = time.perf_counter()
    html_p = Path(html_path).resolve()
    out_p = Path(out_dir).resolve()
    out_p.mkdir(parents=True, exist_ok=True)

    env_info = detect_compute_environment()
    if verbose:
        print("=" * 84)
        print("  RikiGaku-AHIRU (AHIRU-μTJ42V) — V12 FULL-SPECTRUM AEROSPACE VERIFICATION SUITE")
        print("=" * 84)
        gpu_str = f"{env_info['gpu_name']} ({env_info['gpu_vram_gb']} GB VRAM)" if env_info["cuda_available"] else "CPU FP64 Fallback"
        print(f"  Compute Device : {gpu_str} | CPUs: {env_info['cpu_count']}")
        active_bins = [k for k, v in env_info["native_tools"].items() if v]
        active_py = [k for k, v in env_info["python_solvers"].items() if v]
        print(f"  Native Engines : {', '.join(active_bins) if active_bins else 'None'}")
        print(f"  Python Solvers : {', '.join(active_py)}")
        print("=" * 84)
        print("[Step 00/12] Extracting bit-exact 54-part 3D CAD meshes from index.html...")

    cad = load_cad_assembly(html_p, out_p)
    if verbose:
        print(
            f"  -> Extracted {len(cad.parts)} parts | Envelope={cad.global_envelope_mm[0]:.1f}×{cad.global_envelope_mm[1]:.1f}×{cad.global_envelope_mm[2]:.1f} mm "
            f"| Dry={cad.dry_mass_g:.1f}g, Fuel={cad.fuel_volume_ml:.1f}mL ({cad.fuel_mass_g:.1f}g), Wet={cad.wet_mass_g:.1f}g"
        )

    reports: List[DomainReport] = []

    def _run_step(label: str, fn, *args) -> DomainReport:
        if verbose:
            print(f"\n[{label}] Running...", flush=True)
        rep = fn(*args)
        reports.append(rep)
        if verbose:
            print(
                f"  -> {rep.overall_verdict.value:8s} | {rep.pass_count} PASS / {rep.marginal_count} MARG / {rep.fail_count} FAIL "
                f"| {rep.elapsed_sec:.2f}s"
            )
            for c in rep.checks:
                icon = {"PASS": "✓", "MARGINAL": "△", "FAIL": "✗", "INFO": "i"}[c.verdict.value]
                print(f"     [{icon}] {c.check_id} {c.name}: {c.measured}")
        return rep

    r01 = _run_step("Domain 01/12 CAD / DMU / GPU 100k GD&T", run_domain01, cad, out_p, env_info)
    r02 = _run_step("Domain 02/12 CFD / Cantera / Aero", run_domain02, cad, out_p, env_info)
    r03 = _run_step("Domain 03/12 CHT / Radiation / Thermal", run_domain03, cad, out_p, env_info, r02.metrics)
    r04 = _run_step("Domain 04/12 Structural FEA / Containment", run_domain04, cad, out_p, env_info, r02.metrics, r03.metrics)
    r05 = _run_step("Domain 05/12 Rotordynamics / Bearings / CAA", run_domain05, cad, out_p, env_info, r02.metrics)
    r06 = _run_step("Domain 06/12 MuJoCo MBD / GPU 3D SPH Slosh", run_domain06, cad, out_p, env_info, r02.metrics)
    r07 = _run_step("Domain 07/12 ngspice SPICE / KiCad PCB / SI-PI", run_domain07, cad, out_p, env_info)
    r08 = _run_step("Domain 08/12 Starter FEM / GPU 3D FDTD EMI", run_domain08, cad, out_p, env_info, r02.metrics)
    r09 = _run_step("Domain 09/12 6-DOF GNC / LQR / SIL", run_domain09, cad, out_p, env_info, r02.metrics, r06.metrics)
    r10 = _run_step("Domain 10/12 C11 Firmware / MISRA / SPIN / Z3", run_domain10, out_p, env_info)
    r11 = _run_step("Domain 11/12 MBSE / SysML / SCRAM FTA / FMEA", run_domain11, cad, out_p, env_info, reports)
    r12 = _run_step("Domain 12/12 DFM / SLM 3D Print / 5-Axis CNC", run_domain12, cad, out_p, env_info)

    outputs = generate_reports(cad, reports, env_info, out_p)

    total_sec = time.perf_counter() - t_start
    all_checks = [c for r in reports for c in r.checks]
    n_pass = sum(1 for c in all_checks if c.verdict == Verdict.PASS)
    n_marg = sum(1 for c in all_checks if c.verdict == Verdict.MARGINAL)
    n_fail = sum(1 for c in all_checks if c.verdict == Verdict.FAIL)

    if verbose:
        print("\n" + "=" * 84)
        print(f"  COMPLETED ALL 12 DOMAINS IN {total_sec:.2f}s")
        print(f"  FINAL SCORE : {n_pass} PASS | {n_marg} MARGINAL | {n_fail} FAIL (Total {len(all_checks)} checks)")
        print(f"  Dashboard   : {outputs['html']}")
        print(f"  JSON Report : {outputs['json']}")
        print(f"  ZIP Bundle  : {outputs['zip']}")
        print("=" * 84)

    return cad, reports, outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="RikiGaku-AHIRU V12 Full-Spectrum Verification Suite")
    parser.add_argument("--html", default="index.html", help="Path to RikiGaku-AHIRU index.html")
    parser.add_argument("--out", default="verification_out", help="Output directory for reports, plots & CAE decks")
    args = parser.parse_args()
    _, reports, _ = run_full_verification(args.html, args.out, verbose=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
