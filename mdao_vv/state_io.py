"""
Coupled JSON + HDF5 MDAO Checkpoint State Manager, YAML Spec Loader, and
Colab/Linux HPC Hardware & MPI Execution Helper.
"""
from __future__ import annotations

import json
import multiprocessing
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import h5py
import numpy as np
import yaml


DEFAULT_AHIRU_YAML = """
vehicle_spec:
  name: "RikiGaku-AHIRU (AHIRU-uTJ42V)"
  dimensions_mm: { length: 180.0, width: 100.0, height: 200.0 }
  mass_g: { dry_mass: 480.0, fuel_mass: 112.0, payload_mass: 0.0 }
  cad_step_or_stl_path: ""   # Empty -> auto-extracts exact 54-part CAD from index.html (or CadQuery parametric)
propulsion_spec:
  fuel_type: "Jet-A1 / Kerosene + 5% Oil (n-Dodecane C12H26 surrogate)"
  max_thrust_N: 11.43
  max_rpm: 225000
  idle_rpm: 68000
  compressor_diameter_mm: 38.0
  turbine_diameter_mm: 36.4
  pressure_ratio: 3.2
  thrust_vectoring_deg: 14.0
  rcs_type: "bleed_air"
avionics_and_power:
  battery: "3S 850mAh LiHV"
  battery_cells_s: 3
  battery_mah: 850.0
  imu_rate_hz: 1000
  servo_bandwidth_hz: 15.0
"""


def load_user_spec(yaml_str_or_path: Optional[str] = None) -> Dict[str, Any]:
    """Load user vehicle/propulsion/avionics YAML specification."""
    if not yaml_str_or_path:
        return yaml.safe_load(DEFAULT_AHIRU_YAML)
    p = Path(yaml_str_or_path)
    if p.exists() and p.is_file():
        return yaml.safe_load(p.read_text(encoding="utf-8"))
    return yaml.safe_load(yaml_str_or_path)


def detect_hpc_env(work_dir: Path) -> Dict[str, Any]:
    """Detect CPU cores, CUDA GPU, MPI flags, and verify Phase 0 binaries on PATH."""
    # APPEND SU2 micromamba env to PATH (never prepend, so Colab python3 is not shadowed!)
    extra_bins = [Path("/opt/su2_env/bin"), Path.home() / "su2_env" / "bin", Path.home() / ".local" / "bin"]
    path_parts = os.environ.get("PATH", "").split(os.pathsep)
    for eb in extra_bins:
        if eb.exists() and str(eb) not in path_parts:
            path_parts.append(str(eb))
    os.environ["PATH"] = os.pathsep.join(path_parts)

    cpu_cores = multiprocessing.cpu_count()
    gpu_proc = subprocess.run(
        "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader",
        shell=True, capture_output=True, text=True,
    )
    gpu_avail = gpu_proc.returncode == 0 and bool(gpu_proc.stdout.strip())
    gpu_desc = gpu_proc.stdout.strip() if gpu_avail else "CPU Only"

    jax_backend = "unavailable"
    try:
        import jax
        jax_backend = f"{jax.default_backend()} ({len(jax.devices())} dev)"
    except Exception:
        pass

    env = {
        "cpu_cores": cpu_cores,
        "gpu_available": gpu_avail,
        "gpu_desc": gpu_desc,
        "jax_backend": jax_backend,
        "is_root": (os.geteuid() == 0) if hasattr(os, "geteuid") else False,
        "work_dir": str(work_dir.resolve()),
        "binaries": {
            "SU2_CFD": shutil.which("SU2_CFD"),
            "ccx": shutil.which("ccx"),
            "ngspice": shutil.which("ngspice"),
            "mpirun": shutil.which("mpirun"),
            "gmsh": shutil.which("gmsh"),
            "node": shutil.which("node"),
        },
    }
    return env


def require_binary(name: str) -> str:
    """Strictly require an installed native solver binary (no mocks allowed)."""
    path = shutil.which(name)
    if not path:
        raise RuntimeError(
            f"Required native solver '{name}' not found on PATH! "
            f"Run Phase 0 setup cell first to install all aerospace solvers."
        )
    return path


def build_mpi_cmd(exe: str, args: List[str], nprocs: int) -> List[str]:
    """Build an OpenMPI command pairing exe with its sibling mpirun (safe for Colab root container)."""
    exe_p = Path(exe).resolve()
    sibling_mpi = exe_p.parent / "mpirun"
    mpirun = str(sibling_mpi) if sibling_mpi.exists() else shutil.which("mpirun")
    if not mpirun or nprocs <= 1:
        return [exe] + args
    cmd = [mpirun]
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        cmd.append("--allow-run-as-root")
    cmd += ["--oversubscribe", "-np", str(nprocs), exe] + args
    return cmd


def mpi_env() -> Dict[str, str]:
    """Return environment dictionary safe for OpenMPI inside Docker/Colab."""
    env = os.environ.copy()
    env["OMPI_ALLOW_RUN_AS_ROOT"] = "1"
    env["OMPI_ALLOW_RUN_AS_ROOT_CONFIRM"] = "1"
    env["OMP_NUM_THREADS"] = "1"
    return env


class MDAOStateStore:
    """Coupled JSON + HDF5 checkpoint storage for Phase 0..9 MDAO data transfer."""

    def __init__(self, work_dir: Path):
        self.work_dir = Path(work_dir).resolve()
        self.ckpt_dir = self.work_dir / "checkpoints"
        self.mesh_dir = self.work_dir / "meshes"
        self.report_dir = self.work_dir / "reports"
        for d in (self.work_dir, self.ckpt_dir, self.mesh_dir, self.report_dir):
            d.mkdir(parents=True, exist_ok=True)
        self.h5_path = self.ckpt_dir / "mdao_state.h5"

    def save_phase(
        self,
        phase_key: str,
        summary_dict: Dict[str, Any],
        arrays: Optional[Dict[str, np.ndarray]] = None,
    ) -> Path:
        """Persist scalar/structured JSON and numpy field arrays into HDF5."""
        json_path = self.ckpt_dir / f"{phase_key}.json"
        json_path.write_text(json.dumps(summary_dict, indent=2, ensure_ascii=False, default=_json_default), encoding="utf-8")

        if arrays:
            with h5py.File(self.h5_path, "a") as hf:
                if phase_key in hf:
                    del hf[phase_key]
                grp = hf.create_group(phase_key)
                for k, arr in arrays.items():
                    grp.create_dataset(k, data=np.asarray(arr), compression="gzip")
        return json_path

    def load_phase(self, phase_key: str) -> Dict[str, Any]:
        json_path = self.ckpt_dir / f"{phase_key}.json"
        if not json_path.exists():
            raise FileNotFoundError(f"Checkpoint '{phase_key}' not found at {json_path}. Execute previous phases first.")
        return json.loads(json_path.read_text(encoding="utf-8"))

    def has_phase(self, phase_key: str) -> bool:
        return (self.ckpt_dir / f"{phase_key}.json").exists()

    def load_arrays(self, phase_key: str) -> Dict[str, np.ndarray]:
        out: Dict[str, np.ndarray] = {}
        if not self.h5_path.exists():
            return out
        with h5py.File(self.h5_path, "r") as hf:
            if phase_key in hf:
                grp = hf[phase_key]
                for k in grp.keys():
                    out[k] = np.asarray(grp[k])
        return out


def _json_default(obj: Any) -> Any:
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, Path):
        return str(obj)
    return str(obj)
