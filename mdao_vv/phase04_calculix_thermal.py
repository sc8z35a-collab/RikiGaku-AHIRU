"""
Phase 4: Coupled Transient Heat Transfer (Conduction + Convection + Stefan-Boltzmann
Radiation + Contact Resistance) & 300-Second Post-Shutdown Heat Soakback via CalculiX (ccx).

Real Solvers Invoked:
  - CalculiX (ccx) native 3D DC3D8 finite-element transient *HEAT TRANSFER solver
    with *PHYSICAL CONSTANTS (ABSOLUTE ZERO, STEFAN BOLTZMANN), *FILM, *RADIATE,
    multi-material thermal contact resistance, Step 1 (0..312 s full-power flight)
    and Step 2 (312..612 s 300-second post-shutdown heat soakback)!
"""
from __future__ import annotations

import math
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from .state_io import MDAOStateStore, require_binary


def _parse_ccx_nt_history(dat_path: Path, probe_nodes: Dict[str, int]) -> Dict[str, Any]:
    """Parse CalculiX *NODE PRINT NT time-series output from .dat file."""
    times: List[float] = []
    series: Dict[str, List[float]] = {k: [] for k in probe_nodes}
    inv_map = {nid: name for name, nid in probe_nodes.items()}

    cur_t = None
    prev_raw_t = 0.0
    step_offset = 0.0
    cur_vals: Dict[str, float] = {}
    for line in dat_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if "temperatures" in s.lower() and "for set" in s.lower() and "time" in s.lower():
            if cur_t is not None and len(cur_vals) == len(probe_nodes):
                times.append(cur_t)
                for k in probe_nodes:
                    series[k].append(cur_vals[k])
            toks = s.split()
            try:
                raw_t = float(toks[-1])
                if times and raw_t <= prev_raw_t + 1e-9:
                    step_offset = times[-1]
                prev_raw_t = raw_t
                cur_t = step_offset + raw_t
            except ValueError:
                cur_t = None
            cur_vals = {}
        elif cur_t is not None:
            toks = s.split()
            if len(toks) == 2:
                try:
                    nid = int(toks[0])
                    temp_K = float(toks[1])
                    if nid in inv_map:
                        cur_vals[inv_map[nid]] = temp_K
                except ValueError:
                    pass
    if cur_t is not None and len(cur_vals) == len(probe_nodes):
        times.append(cur_t)
        for k in probe_nodes:
            series[k].append(cur_vals[k])

    return {"times_s": np.array(times, dtype=np.float64), "temps_K": {k: np.array(v, dtype=np.float64) for k, v in series.items()}}


def run_phase04(spec: Dict[str, Any], store: MDAOStateStore) -> Dict[str, Any]:
    """Execute Phase 4: Real CalculiX (ccx) transient thermal + radiation + 300s heat soakback."""
    t0 = time.perf_counter()
    print("=== [Phase 4] CalculiX (ccx) Transient CHT, Radiation & 300s Heat Soakback ===")

    ccx_bin = require_binary("ccx")
    p1 = store.load_phase("phase01_geometry")
    p2 = store.load_phase("phase02_propulsion")
    p3 = store.load_phase("phase03_cfd_su2")

    geom = p1["geometry"]
    ft = p2["full_throttle"]
    dT_hgi = float(p3["ige_hgi"]["dT_hgi_K"][0])

    # Coupled boundary temperatures from Phase 2 & 3!
    T_amb_K = 288.15 + 0.15 * dT_hgi  # Slight ambient elevation near ground
    T_comb_gas_K = float(ft["T_t4_K"])
    T_comp_air_K = float(ft["T_t3_K"])
    T_liner_film_K = 0.78 * T_comb_gas_K + 0.22 * T_comp_air_K

    th_dir = store.work_dir / "calculix_thermal"
    th_dir.mkdir(parents=True, exist_ok=True)
    inp_path = th_dir / "ahiru_thermal_soak.inp"

    # Build a real 3D multi-sector cylindrical DC3D8 finite-element mesh (4 radial stacks in parallel sectors):
    #   Sector 0 (Front +X): Combustor -> Jacket/Gold -> Aerogel -> Direct Contact Interface -> 3S LiHV Battery -> Outer PEEK Shell
    #   Sector 1 (Rear -X):  Combustor -> Jacket/Gold -> Aerogel -> 3.1mm Air/Rad Gap -> Saddle Fuel Tank Wall -> Bulk Jet-A1 -> Outer Shell
    #   Sector 2 (Side +Z):  Combustor -> Bolt Contact Bridge -> Al 7075-T6 Frame -> Air Gap -> Outer PEEK Shell
    #   Sector 3 (Upper +Y): Combustor -> Neck Truss Conduction (80 mm) -> Head FADEC PCB (3.5W dissipation) -> Head Shell
    # Each sector is a 3D 1x1 cross-section (10mm x 10mm) chain of DC3D8 hexahedra with exact physical layer thicknesses!

    nodes: List[str] = []
    elems_by_mat: Dict[str, List[str]] = {}
    hot_eids: List[int] = []
    ext_eids: List[int] = []
    probe_nodes: Dict[str, int] = {}

    nid = 1
    eid = 1

    def add_3d_chain(
        y_offset: float,
        layers: List[tuple[str, float, int, str]],
        hot_end: bool = True,
    ) -> Dict[str, int]:
        """Build a 3D brick chain along X (length = sum of thicknesses) with 10mm x 10mm YZ cross-section."""
        nonlocal nid, eid
        sec_probes: Dict[str, int] = {}
        x_coords = [0.0]
        elem_mats: List[str] = []
        elem_tags: List[str] = []
        for mat_name, thick_m, n_sub, tag in layers:
            for k in range(n_sub):
                x_coords.append(x_coords[-1] + thick_m / n_sub)
                elem_mats.append(mat_name)
                elem_tags.append(tag)

        # Create (nx+1) planes of 4 nodes each: (x, y_off, 0), (x, y_off+w, 0), (x, y_off+w, w), (x, y_off, w)
        w = 0.010  # 10 mm unit cross-section
        planes = []
        for x in x_coords:
            p_ids = []
            for dy, dz in ((0.0, 0.0), (w, 0.0), (w, w), (0.0, w)):
                nodes.append(f"{nid}, {x:.6e}, {y_offset + dy:.6e}, {dz:.6e}")
                p_ids.append(nid)
                nid += 1
            planes.append(p_ids)

        for i, (mname, tag) in enumerate(zip(elem_mats, elem_tags)):
            n1, n2, n3, n4 = planes[i]
            n5, n6, n7, n8 = planes[i + 1]
            elems_by_mat.setdefault(mname, []).append(f"{eid}, {n1}, {n2}, {n3}, {n4}, {n5}, {n6}, {n7}, {n8}")
            if i == 0 and hot_end:
                hot_eids.append(eid)
            if i == len(elem_mats) - 1:
                ext_eids.append(eid)
            # Record probe node at the center/end of each tagged component
            sec_probes[tag] = n5
            eid += 1
        return sec_probes

    # Sector 0 (Front +X Battery Stack): note actual CAD battery touches shroud directly!
    # Contact gap thickness = 0.0005 m (direct contact resistance R_c ~ 0.002 m^2K/W)
    p_s0 = add_3d_chain(0.00, [
        ("INCONEL718", 0.0022, 3, "combustor_liner"),
        ("GOLD_GAP_RAD", 0.0018, 2, "cooling_jacket"),
        ("AEROGEL", 0.0034, 4, "aerogel_shroud"),
        ("CONTACT_BAT", 0.0008, 2, "bat_contact"),
        ("LIHV_PACK", 0.0170, 4, "battery_3s"),
        ("PEEK_SHELL", 0.0023, 2, "shell_front"),
    ])

    # Sector 1 (Rear -X Conformal Saddle Fuel Tank Stack): 3.1 mm air+rad gap + PA12 wall + Jet-A1 fuel
    p_s1 = add_3d_chain(0.03, [
        ("INCONEL718", 0.0022, 3, "comb_rear"),
        ("GOLD_GAP_RAD", 0.0018, 2, "jack_rear"),
        ("AEROGEL", 0.0034, 4, "shroud_rear"),
        ("AIR_GAP_FUEL", 0.0031, 2, "fuel_gap"),
        ("PA12_TANK", 0.0018, 2, "fuel_tank_wall"),
        ("JET_A1", 0.0190, 4, "fuel_bulk"),
        ("PEEK_SHELL", 0.0023, 2, "shell_rear"),
    ])

    # Sector 2 (Side +Z Al 7075-T6 Structural Frame Stack): direct bolted conduction path!
    p_s2 = add_3d_chain(0.06, [
        ("INCONEL718", 0.0022, 2, "comb_side"),
        ("BOLT_CONTACT", 0.0030, 2, "bolt_bridge"),
        ("AL7075", 0.0140, 4, "al7075_frame"),
        ("AIR_GAP_FUEL", 0.0060, 2, "frame_air"),
        ("PEEK_SHELL", 0.0023, 2, "shell_side"),
    ])

    # Sector 3 (Upper +Y Neck Truss to Head FADEC PCB): 80 mm truss + FR4 PCB (internal dissipation)
    p_s3 = add_3d_chain(0.09, [
        ("INCONEL718", 0.0022, 2, "comb_top"),
        ("BOLT_CONTACT", 0.0040, 2, "top_mount"),
        ("NECK_TRUSS", 0.0780, 5, "neck_truss"),
        ("FR4_PCB", 0.0035, 3, "fadec_pcb"),
        ("PEEK_SHELL", 0.0023, 2, "shell_head"),
    ])

    probe_nodes = {
        "combustor_liner": p_s0["combustor_liner"],
        "aerogel_shroud": p_s0["aerogel_shroud"],
        "battery_3s": p_s0["battery_3s"],
        "fuel_tank_wall": p_s1["fuel_tank_wall"],
        "fuel_bulk": p_s1["fuel_bulk"],
        "al7075_frame": p_s2["al7075_frame"],
        "outer_shell": p_s0["shell_front"],
        "fadec_pcb": p_s3["fadec_pcb"],
    }

    # Build CalculiX *HEAT TRANSFER input deck with REAL Stefan-Boltzmann radiation!
    inp_lines = [
        "*HEADING",
        "AHIRU-uTJ42V Transient CHT + Radiation + 300s Post-Shutdown Heat Soakback (SI)",
        "*PHYSICAL CONSTANTS, ABSOLUTE ZERO=0.0, STEFAN BOLTZMANN=5.670374e-8",
        "*NODE, NSET=NALL",
        *nodes,
    ]
    for mname, elist in elems_by_mat.items():
        inp_lines.append(f"*ELEMENT, TYPE=DC3D8, ELSET=E_{mname}")
        inp_lines.extend(elist)

    # Probe node set for compact clean .dat time-history output
    inp_lines.append("*NSET, NSET=NPROBES")
    inp_lines.append(", ".join(str(v) for v in probe_nodes.values()))

    # Aerospace material thermal properties: Conductivity [W/mK], Specific Heat [J/kgK], Density [kg/m^3]
    # Note: GOLD_GAP_RAD encodes pressurized jacket air + gold foil low-emissivity radiation barrier;
    # CONTACT_BAT encodes direct ceramic-to-battery touching contact resistance!
    mat_db = {
        "INCONEL718":   (18.0,   450.0, 8190.0),
        "GOLD_GAP_RAD": (0.048,  1005.0, 2.5),
        "AEROGEL":      (0.042,  950.0, 200.0),
        "CONTACT_BAT":  (0.32,   900.0, 800.0),   # Direct touching CAD overlap (gap=-1.85 mm!)
        "LIHV_PACK":    (1.80,   1050.0, 2250.0),
        "AIR_GAP_FUEL": (0.045,  1005.0, 1.2),    # 3.1 mm ventilated gap + radiation
        "PA12_TANK":    (0.24,   1700.0, 1050.0),
        "JET_A1":       (0.14,   2010.0, 800.0),
        "BOLT_CONTACT": (2.20,   600.0, 3200.0),  # Direct metal-to-metal bolted bridge (no thermal break!)
        "AL7075":       (130.0,  960.0, 2810.0),
        "NECK_TRUSS":   (12.0,   960.0, 950.0),   # Effective cross-section ratio of slim truss tubes
        "FR4_PCB":      (0.45,   1100.0, 2150.0),
        "PEEK_SHELL":   (0.92,   1150.0, 1420.0),
    }
    for mname, (k, cp, rho) in mat_db.items():
        inp_lines.extend([
            f"*MATERIAL, NAME={mname}",
            "*CONDUCTIVITY", f"{k}",
            "*SPECIFIC HEAT", f"{cp}",
            "*DENSITY", f"{rho}",
            f"*SOLID SECTION, ELSET=E_{mname}, MATERIAL={mname}",
        ])

    film_step1 = [f"{e}, F1, {T_liner_film_K:.2f}, 420.0" for e in hot_eids] + [
        f"{e}, F2, {T_amb_K:.2f}, 38.0" for e in ext_eids
    ]
    rad_step1 = [f"{e}, R2, {T_amb_K:.2f}, 0.85" for e in ext_eids]

    film_step2 = [f"{e}, F1, {T_amb_K + 40.0:.2f}, 6.0" for e in hot_eids] + [
        f"{e}, F2, {T_amb_K:.2f}, 9.5" for e in ext_eids
    ]
    rad_step2 = [f"{e}, R2, {T_amb_K:.2f}, 0.85" for e in ext_eids]

    inp_lines.extend([
        "*INITIAL CONDITIONS, TYPE=TEMPERATURE",
        f"NALL, {T_amb_K:.2f}",
        # STEP 1: Full-Power Continuous Flight Burn (0 -> 312 s)
        "*STEP, INC=200",
        "*HEAT TRANSFER",
        "12.0, 312.0, 0.5, 24.0",
        "*FILM",
        *film_step1,
        "*RADIATE",
        *rad_step1,
        "*DFLUX",
        "E_LIHV_PACK, BF, 2.2e5",   # 3.5 W battery I^2R ohmic heating
        "E_FR4_PCB, BF, 3.8e5",     # 3.5 W FADEC PCB internal heat dissipation
        "*NODE PRINT, NSET=NPROBES",
        "NT",
        "*END STEP",
        # STEP 2: 300-Second Post-Shutdown Heat Soakback (312 -> 612 s)
        "*STEP, INC=200",
        "*HEAT TRANSFER",
        "12.0, 300.0, 0.5, 24.0",
        "*FILM, OP=NEW",
        *film_step2,
        "*RADIATE, OP=NEW",
        *rad_step2,
        "*DFLUX, OP=NEW",
        "E_LIHV_PACK, BF, 1.5e4",
        "E_FR4_PCB, BF, 2.0e5",
        "*NODE PRINT, NSET=NPROBES",
        "NT",
        "*END STEP",
    ])
    inp_path.write_text("\n".join(inp_lines), encoding="utf-8")

    # Execute REAL CalculiX (ccx) solver!
    proc = subprocess.run(
        [ccx_bin, "-i", "ahiru_thermal_soak"],
        cwd=str(th_dir),
        capture_output=True,
        text=True,
        timeout=90,
    )
    dat_path = th_dir / "ahiru_thermal_soak.dat"
    if proc.returncode != 0 or not dat_path.exists():
        raise RuntimeError(f"CalculiX ccx thermal solve failed (rc={proc.returncode}): {proc.stdout[-600:]} {proc.stderr[-600:]}")

    hist = _parse_ccx_nt_history(dat_path, probe_nodes)
    times_s = hist["times_s"]
    if len(times_s) < 5:
        raise RuntimeError(f"CalculiX thermal .dat yielded insufficient time steps ({len(times_s)}).")

    temps_C = {k: v - 273.15 for k, v in hist["temps_K"].items()}
    peaks_C = {k: round(float(np.max(v)), 2) for k, v in temps_C.items()}
    # Separate flight peak (t <= 312 s) vs soakback peak (t > 312 s) for battery!
    m_flight = times_s <= 312.5
    bat_flight_C = float(np.max(temps_C["battery_3s"][m_flight])) if np.any(m_flight) else peaks_C["battery_3s"]
    bat_soak_C = peaks_C["battery_3s"]

    # Strict Aerospace Verdicts
    checks = {
        "battery_thermal_runaway_soakback": {
            "pass": (bat_soak_C <= 60.0),
            "measured": f"Flight={bat_flight_C:.1f} °C, 300s Soak Peak={bat_soak_C:.1f} °C",
            "target": "≤ 60.0 °C safe LiHV limit (Runaway onset 130 °C)",
        },
        "fuel_tank_and_vapor_lock": {
            "pass": (peaks_C["fuel_tank_wall"] <= 85.0 and peaks_C["fuel_bulk"] <= 65.0),
            "measured": f"Tank Wall={peaks_C['fuel_tank_wall']:.1f} °C, Bulk Jet-A1={peaks_C['fuel_bulk']:.1f} °C",
            "target": "Tank Wall ≤ 85 °C, Bulk Fuel ≤ 65 °C (Boil=150 °C)",
        },
        "al7075_frame_and_outer_shell": {
            "pass": (peaks_C["al7075_frame"] <= 145.0 and peaks_C["outer_shell"] <= 120.0),
            "measured": f"Al 7075 Frame={peaks_C['al7075_frame']:.1f} °C, Outer Shell={peaks_C['outer_shell']:.1f} °C",
            "target": "Al 7075 ≤ 145 °C (over-aging), PEEK Shell ≤ 120 °C",
        },
        "fadec_pcb_electronics": {
            "pass": (peaks_C["fadec_pcb"] <= 95.0),
            "measured": f"FADEC PCB={peaks_C['fadec_pcb']:.1f} °C (T_j ≈ {peaks_C['fadec_pcb']+18.0:.1f} °C)",
            "target": "PCB ≤ 95 °C (MCU T_j ≤ 115 °C)",
        },
        "inconel_liner_limit": {
            "pass": (peaks_C["combustor_liner"] <= 950.0),
            "measured": f"Inconel 718 Liner={peaks_C['combustor_liner']:.1f} °C",
            "target": "≤ 950 °C (Inconel 718 max 980 °C)",
        },
    }

    summary = {
        "phase": 4,
        "title": "Transient CHT, Stefan-Boltzmann Radiation & 300s Heat Soakback (CalculiX)",
        "solver": f"CalculiX ccx 3D DC3D8 *HEAT TRANSFER + *RADIATE ({len(times_s)} transient steps)",
        "verdict": "PASS" if all(c["pass"] for c in checks.values()) else "FAIL",
        "elapsed_sec": round(time.perf_counter() - t0, 2),
        "checks": checks,
        "peak_temps_C": peaks_C,
        "battery_flight_max_C": round(bat_flight_C, 2),
        "battery_soak_max_C": round(bat_soak_C, 2),
        "inp_path": str(inp_path),
    }

    arrs = {"times_s": times_s}
    for k, v in temps_C.items():
        arrs[f"T_{k}_C"] = v
    store.save_phase("phase04_thermal", summary, arrays=arrs)
    print(
        f"  -> Phase 4 Verdict: {summary['verdict']} ({summary['elapsed_sec']:.2f}s) | "
        f"Liner={peaks_C['combustor_liner']:.0f}°C, Bat(soak)={bat_soak_C:.1f}°C, Frame={peaks_C['al7075_frame']:.1f}°C, Fuel={peaks_C['fuel_bulk']:.1f}°C"
    )
    return summary
