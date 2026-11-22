"""
Master Coupled MDAO / V&V Pipeline Runner (Phases 1 through 9 with Checkpoint Resume).

Usage:
    python3 -m mdao_vv.run_pipeline --work-dir /tmp/ahiru_mdao_run
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

from .phase01_geometry_fcl import run_phase01
from .phase02_cantera_openmdao import run_phase02
from .phase03_gmsh_su2_cfd import run_phase03
from .phase04_calculix_thermal import run_phase04
from .phase05_calculix_ross import run_phase05
from .phase06_pyspice_ngspice import run_phase06
from .phase07_casadi_mujoco_jax import run_phase07
from .phase08_openturns_salib_uq import run_phase08
from .phase09_dashboard_optimizer import run_phase09
from .state_io import MDAOStateStore, detect_hpc_env, load_user_spec


def run_mdao_vv_pipeline(
    work_dir: str | Path,
    repo_root: str | Path = ".",
    spec_yaml: Optional[str] = None,
    resume: bool = True,
) -> Dict[str, Any]:
    """Execute Phases 1..9 sequentially with automatic JSON+HDF5 checkpoint persistence."""
    t0 = time.perf_counter()
    work_p = Path(work_dir).resolve()
    repo_p = Path(repo_root).resolve()
    store = MDAOStateStore(work_p)
    env_info = detect_hpc_env(work_p)
    spec = load_user_spec(spec_yaml)

    store.save_phase("env_config", env_info)
    store.save_phase("user_spec", spec)

    print("=" * 86)
    print("  RikiGaku-AHIRU (AHIRU-μTJ42V) — AEROSPACE MDAO / V&V PIPELINE (PHASES 1–9)")
    print(f"  HW: {env_info['cpu_cores']} CPU Cores | GPU: {env_info['gpu_desc']} | JAX: {env_info['jax_backend']}")
    print(f"  Checkpoints & Reports: {work_p}")
    print("=" * 86)

    steps = [
        ("phase01_geometry", lambda: run_phase01(spec, store, repo_p)),
        ("phase02_propulsion", lambda: run_phase02(spec, store)),
        ("phase03_cfd_su2", lambda: run_phase03(spec, store, env_info)),
        ("phase04_thermal", lambda: run_phase04(spec, store)),
        ("phase05_struct_rotor", lambda: run_phase05(spec, store)),
        ("phase06_power_spice", lambda: run_phase06(spec, store)),
        ("phase07_gnc_mc", lambda: run_phase07(spec, store, env_info)),
        ("phase08_uq_sobol", lambda: run_phase08(spec, store)),
        ("phase09_optimization", lambda: run_phase09(spec, store)),
    ]

    results: Dict[str, Any] = {}
    for key, fn in steps:
        if resume and store.has_phase(key) and key != "phase09_optimization":
            print(f"[RESUME] Skipping {key} (loaded from {store.ckpt_dir / (key + '.json')})")
            results[key] = store.load_phase(key)
        else:
            results[key] = fn()

    total_s = time.perf_counter() - t0
    print("\n" + "=" * 86)
    print(f"  MDAO / V&V COMPLETE IN {total_s:.1f}s")
    print(f"  Baseline Verdict  : {results['phase09_optimization']['baseline_verdict']}")
    print(f"  Optimized Verdict : {results['phase09_optimization']['optimized_verdict']}")
    print(f"  Plotly Dashboard  : {results['phase09_optimization']['dashboard_html']}")
    print("=" * 86)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="RikiGaku-AHIRU Coupled MDAO / V&V Pipeline")
    parser.add_argument("--work-dir", default="/tmp/ahiru_mdao_vv", help="Checkpoint & report directory")
    parser.add_argument("--repo-root", default=".", help="Path to RikiGaku-AHIRU repo")
    parser.add_argument("--spec", default=None, help="Optional YAML path")
    parser.add_argument("--no-resume", action="store_true", help="Force re-run all phases")
    args = parser.parse_args()
    run_mdao_vv_pipeline(args.work_dir, args.repo_root, args.spec, resume=not args.no_resume)
    return 0


if __name__ == "__main__":
    sys.exit(main())
