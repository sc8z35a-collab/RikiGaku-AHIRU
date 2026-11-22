"""
Phase 5: Coupled Centrifugal + Thermal Stress 3D FEA (CalculiX ccx at 100% & 125%
Burst Overspeed) + Ultra-High-Speed Rotordynamics (ROSS 3.0 Campbell, Critical Speeds,
ISO 1940 G0.4/G1.0 Unbalance Response & Maneuver Gyroscopic Bearing Loads).

Real Solvers Invoked:
  - CalculiX (ccx) 3D C3D8 thermo-mechanical FEA (*DLOAD CENTRIF + *TEMPERATURE + *CLOAD)
  - ROSS (ross.Rotor, run_campbell, run_critical_speed, run_unbalance_response)
"""
from __future__ import annotations

import math
import subprocess
import time
import warnings
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import ross as rs  # Strictly required (Phase 0)

from .state_io import MDAOStateStore, require_binary


def _run_ccx_thermo_centrif_disk(
    work_dir: Path,
    job_name: str,
    r_in: float,
    r_out: float,
    h_bore: float,
    h_rim: float,
    omega: float,
    E_Pa: float,
    nu: float,
    rho: float,
    cte: float,
    T_ref_K: float,
    T_bore_K: float,
    T_rim_K: float,
    total_rim_pull_N: float,
) -> Dict[str, float]:
    """
    Build a profiled 3D C3D8 tapered-hub annular disk mesh and execute CalculiX (ccx)
    with coupled *DLOAD CENTRIF + radial *TEMPERATURE thermal stress + rim blade *CLOAD.
    """
    ccx_bin = require_binary("ccx")
    nr, nt, nz = 8, 36, 2
    r_vals = np.linspace(r_in, r_out, nr + 1)
    t_vals = np.linspace(0.0, 2.0 * math.pi, nt, endpoint=False)

    lines = [
        "*HEADING",
        f"AHIRU-uTJ42V 3D Thermo-Mechanical Disk FEA: {job_name} (SI)",
        "*NODE, NSET=NALL",
    ]
    nid_map = {}
    node_temps: List[str] = []
    rim_loads: List[str] = []
    nid = 1

    # Number of rim nodes = nt * (nz + 1)
    n_rim_nodes = nt * (nz + 1)
    f_per_rim_node = total_rim_pull_N / max(n_rim_nodes, 1)

    for iz in range(nz + 1):
        z_frac = -0.5 + iz / nz  # -0.5, 0.0, +0.5
        for ir, r in enumerate(r_vals):
            xi = (r - r_in) / max(r_out - r_in, 1e-9)
            h_local = h_bore + (h_rim - h_bore) * xi
            z = z_frac * h_local
            T_node = T_bore_K + (T_rim_K - T_bore_K) * (xi ** 1.5)
            for it, th in enumerate(t_vals):
                nid_map[(ir, it, iz)] = nid
                lines.append(f"{nid}, {r * math.cos(th):.6e}, {r * math.sin(th):.6e}, {z:.6e}")
                node_temps.append(f"{nid}, {T_node:.2f}")
                if ir == nr and f_per_rim_node > 0.0:
                    rim_loads.append(f"{nid}, 1, {f_per_rim_node * math.cos(th):.6e}")
                    rim_loads.append(f"{nid}, 2, {f_per_rim_node * math.sin(th):.6e}")
                nid += 1

    lines.append("*ELEMENT, TYPE=C3D8, ELSET=EDISK")
    eid = 1
    for iz in range(nz):
        for ir in range(nr):
            for it in range(nt):
                it2 = (it + 1) % nt
                n1 = nid_map[(ir, it, iz)]
                n2 = nid_map[(ir + 1, it, iz)]
                n3 = nid_map[(ir + 1, it2, iz)]
                n4 = nid_map[(ir, it2, iz)]
                n5 = nid_map[(ir, it, iz + 1)]
                n6 = nid_map[(ir + 1, it, iz + 1)]
                n7 = nid_map[(ir + 1, it2, iz + 1)]
                n8 = nid_map[(ir, it2, iz + 1)]
                lines.append(f"{eid}, {n1}, {n2}, {n3}, {n4}, {n5}, {n6}, {n7}, {n8}")
                eid += 1

    # Minimal 6-DOF rigid-body suppression (zero thermal over-constraint!)
    n_f1 = nid_map[(0, 0, 1)]
    n_f2 = nid_map[(0, nt // 2, 1)]
    n_f3 = nid_map[(0, nt // 4, 1)]

    lines.extend([
        "*MATERIAL, NAME=ROTOR_ALLOY",
        "*ELASTIC", f"{E_Pa:.6e}, {nu}",
        "*DENSITY", f"{rho:.2f}",
        f"*EXPANSION, ZERO={T_ref_K:.2f}", f"{cte:.6e}",
        "*SOLID SECTION, ELSET=EDISK, MATERIAL=ROTOR_ALLOY",
        "*INITIAL CONDITIONS, TYPE=TEMPERATURE",
        f"NALL, {T_ref_K:.2f}",
        "*BOUNDARY",
        f"{n_f1}, 2, 3, 0.0",
        f"{n_f2}, 2, 3, 0.0",
        f"{n_f3}, 1, 1, 0.0",
        f"{n_f3}, 3, 3, 0.0",
        "*STEP",
        "*STATIC",
        "*DLOAD",
        f"EDISK, CENTRIF, {omega**2:.6e}, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0",
        "*TEMPERATURE",
        *node_temps,
    ])
    if rim_loads:
        lines.append("*CLOAD")
        lines.extend(rim_loads)
    lines.extend([
        "*EL PRINT, ELSET=EDISK",
        "S",
        "*NODE PRINT, NSET=NALL",
        "U",
        "*END STEP",
    ])

    inp_path = work_dir / f"{job_name}.inp"
    inp_path.write_text("\n".join(lines), encoding="utf-8")

    proc = subprocess.run([ccx_bin, "-i", job_name], cwd=str(work_dir), capture_output=True, text=True, timeout=60)
    dat_path = work_dir / f"{job_name}.dat"
    if proc.returncode != 0 or not dat_path.exists():
        raise RuntimeError(f"CalculiX ccx failed on {job_name}: {proc.stdout[-500:]} {proc.stderr[-500:]}")

    max_vm_Pa = 0.0
    vm_list: List[float] = []
    max_ur_m = 0.0
    in_stress = False
    in_disp = False
    for line in dat_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        lo = line.lower()
        if "stresses" in lo and "for set" in lo:
            in_stress, in_disp = True, False
            continue
        if "displacements" in lo and "for set" in lo:
            in_stress, in_disp = False, True
            continue
        toks = line.split()
        if in_stress and len(toks) == 8:
            try:
                sxx, syy, szz, sxy, sxz, syz = [float(t) for t in toks[2:8]]
                vm = math.sqrt(0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2 + 6.0 * (sxy ** 2 + sxz ** 2 + syz ** 2)))
                vm_list.append(vm)
                if vm > max_vm_Pa:
                    max_vm_Pa = vm
            except ValueError:
                pass
        elif in_disp and len(toks) == 4:
            try:
                ux, uy = float(toks[1]), float(toks[2])
                ur = math.hypot(ux, uy)
                if ur > max_ur_m:
                    max_ur_m = ur
            except ValueError:
                pass

    if not vm_list:
        raise RuntimeError(f"CalculiX .dat for {job_name} contained zero parsed stress integration points.")

    return {
        "elements": eid - 1,
        "max_vm_MPa": round(max_vm_Pa * 1e-6, 2),
        "p95_vm_MPa": round(float(np.percentile(vm_list, 95)) * 1e-6, 2),
        "mean_vm_MPa": round(float(np.mean(vm_list)) * 1e-6, 2),
        "max_radial_growth_mm": round(max_ur_m * 1e3, 4),
    }


def _run_ross_rotordynamics(rpm_max: float, rpm_idle: float) -> Dict[str, Any]:
    """Execute real ROSS 3.0 finite-element rotordynamics (Campbell, Criticals, ISO 1940 G0.4/G1.0)."""
    warnings.filterwarnings("ignore")
    ti_mat = rs.Material(name="Ti6Al4V", rho=4430.0, E=113.8e9, G_s=42.4e9)

    # Exact CAD stations along shaft Y: [53.5, 62.5, 74.0, 85.0, 90.0] mm
    L_segs = [0.0090, 0.0115, 0.0110, 0.0050]
    od_segs = [0.0062, 0.0084, 0.0084, 0.0062]
    shaft_elems = [
        rs.ShaftElement(L=L, idl=0.0, odl=od, material=ti_mat, shear_effects=True, rotary_inertia=True, gyroscopic=True)
        for L, od in zip(L_segs, od_segs)
    ]

    # Exact CAD disk inertia: Node 0 = Inconel 718 Turbine (14 g), Node 4 = Ti-6Al-4V Compressor (9 g)
    m_turb, m_comp = 0.014, 0.009
    Ip_turb, Id_turb = 0.5 * m_turb * (0.0145 ** 2), 0.25 * m_turb * (0.0145 ** 2)
    Ip_comp, Id_comp = 0.5 * m_comp * (0.0135 ** 2), 0.25 * m_comp * (0.0135 ** 2)
    disks = [
        rs.DiskElement(n=0, m=m_turb, Id=Id_turb, Ip=Ip_turb, tag="Inconel718_Turbine"),
        rs.DiskElement(n=4, m=m_comp, Id=Id_comp, Ip=Ip_comp, tag="Ti6Al4V_Compressor"),
    ]

    # Dual hybrid Si3N4 angular-contact bearings (O-ring damped cartridge stiffness k=3.5e6 N/m, c=190 N*s/m)
    bearings = [
        rs.BearingElement(n=1, kxx=3.5e6, kyy=3.5e6, cxx=190.0, cyy=190.0, tag="Lower_Si3N4_Brg"),
        rs.BearingElement(n=3, kxx=3.5e6, kyy=3.5e6, cxx=190.0, cyy=190.0, tag="Upper_Si3N4_Brg"),
    ]

    rotor = rs.Rotor(shaft_elems, disks, bearings)
    speed_rpm = np.linspace(5000.0, 290000.0, 48)
    speed_rad = speed_rpm * 2.0 * math.pi / 60.0

    camp = rotor.run_campbell(speed_rad, frequencies=6)
    wd_rpm = np.asarray(camp.wd, dtype=np.float64) * 60.0 / (2.0 * math.pi)  # shape (n_speeds, n_modes)

    # Extract 1X synchronous critical speeds via ROSS Campbell 1X crossings (plus run_critical_speed on first 4 modes)
    crit_speeds_rpm: List[float] = []
    for m in range(wd_rpm.shape[1]):
        diff = wd_rpm[:, m] - speed_rpm
        for j in range(len(speed_rpm) - 1):
            if np.isfinite(diff[j]) and np.isfinite(diff[j + 1]) and (diff[j] * diff[j + 1] <= 0.0):
                if abs(diff[j + 1] - diff[j]) > 1e-9:
                    frac = -diff[j] / (diff[j + 1] - diff[j])
                    c_rpm = float(speed_rpm[j] + frac * (speed_rpm[j + 1] - speed_rpm[j]))
                    if 5000.0 <= c_rpm <= 285000.0:
                        crit_speeds_rpm.append(c_rpm)
    try:
        crit_res = rotor.run_critical_speed(speed_range=(speed_rad[0], speed_rad[-1]), num_modes=4)
        wn_crit = np.asarray(crit_res.wn(), dtype=np.float64) if callable(getattr(crit_res, "wn", None)) else np.asarray(getattr(crit_res, "wn", []), dtype=np.float64)
        for w in wn_crit:
            c_rpm = float(w * 60.0 / (2.0 * math.pi))
            if 5000.0 <= c_rpm <= 285000.0 and all(abs(c_rpm - x) > 1500.0 for x in crit_speeds_rpm):
                crit_speeds_rpm.append(c_rpm)
    except RuntimeError:
        pass
    # Deduplicate close forward/backward whirl roots within 500 RPM
    crit_speeds_rpm.sort()
    dedup_crits: List[float] = []
    for c in crit_speeds_rpm:
        if not dedup_crits or abs(c - dedup_crits[-1]) > 500.0:
            dedup_crits.append(c)
    crit_speeds_rpm = dedup_crits

    # ISO 1940-1 G0.4 and G1.0 unbalance response via ROSS!
    # Unbalance magnitude U = m * e = m * (G_m_s / omega_max) [kg*m]
    omega_max = rpm_max * 2.0 * math.pi / 60.0
    U_g04_turb = m_turb * (0.0004 / omega_max)
    U_g04_comp = m_comp * (0.0004 / omega_max)
    U_g10_turb = m_turb * (0.0010 / omega_max)
    U_g10_comp = m_comp * (0.0010 / omega_max)

    resp_g04 = rotor.run_unbalance_response([0, 4], [U_g04_turb, U_g04_comp], [0.0, 0.0], speed_rad)
    resp_g10 = rotor.run_unbalance_response([0, 4], [U_g10_turb, U_g10_comp], [0.0, 0.0], speed_rad)

    # Forced response displacement magnitude at turbine (DOF 0) & compressor (DOF 16)
    mag_g04 = np.abs(np.asarray(resp_g04.forced_resp))
    mag_g10 = np.abs(np.asarray(resp_g10.forced_resp))
    # Extract lateral X/Y translation DOFs (nodes 0 and 4 -> DOFs 0,1 and 16,17)
    amp_g04_um = np.max(mag_g04[[0, 1, 16, 17], :], axis=0) * 1e6
    amp_g10_um = np.max(mag_g10[[0, 1, 16, 17], :], axis=0) * 1e6

    # Gyroscopic moment & bearing radial load during 90 deg/s pitch slew maneuver!
    Ip_total = Ip_turb + Ip_comp + 0.5 * 0.006 * (0.0038 ** 2)
    H_rotor_Nms = Ip_total * omega_max
    tau_gyro_90dps_Nm = H_rotor_Nms * math.radians(90.0)
    bearing_span_m = 0.0850 - 0.0625  # 22.5 mm
    F_brg_gyro_N = tau_gyro_90dps_Nm / bearing_span_m

    # Hybrid ceramic bearing DN value (exact CAD d_m = 12.5 mm)
    dn_million = 12.5 * rpm_max / 1e6

    return {
        "ross_version": rs.__version__,
        "speed_rpm": speed_rpm,
        "campbell_wd_rpm": wd_rpm,
        "crit_speeds_rpm": [round(c, 0) for c in crit_speeds_rpm],
        "amp_g04_um": amp_g04_um,
        "amp_g10_um": amp_g10_um,
        "peak_g04_op_um": round(float(np.interp(rpm_max, speed_rpm, amp_g04_um)), 3),
        "peak_g10_op_um": round(float(np.interp(rpm_max, speed_rpm, amp_g10_um)), 3),
        "peak_g10_crit_um": round(float(np.max(amp_g10_um)), 3),
        "H_rotor_Nms": round(H_rotor_Nms, 6),
        "tau_gyro_90dps_mNm": round(tau_gyro_90dps_Nm * 1e3, 2),
        "F_brg_gyro_N": round(F_brg_gyro_N, 2),
        "bearing_dn_million": round(dn_million, 3),
    }


def run_phase05(spec: Dict[str, Any], store: MDAOStateStore) -> Dict[str, Any]:
    """Execute Phase 5: Real CalculiX 3D Thermo-Mechanical FEA (100% & 125%) + ROSS 3.0 Rotordynamics."""
    t0 = time.perf_counter()
    print("=== [Phase 5] CalculiX (ccx) 100%/125% Thermo-Mechanical FEA + ROSS 3.0 ===")

    p1 = store.load_phase("phase01_geometry")
    p2 = store.load_phase("phase02_propulsion")
    p4 = store.load_phase("phase04_thermal")

    pspec = spec["propulsion_spec"]
    rpm_max = float(pspec.get("max_rpm", 225000.0))
    rpm_idle = float(pspec.get("idle_rpm", 68000.0))
    omega_100 = rpm_max * 2.0 * math.pi / 60.0
    omega_125 = omega_100 * 1.25  # 125% burst overspeed!

    fea_dir = store.work_dir / "calculix_fea"
    fea_dir.mkdir(parents=True, exist_ok=True)

    # Coupled thermal boundary temps from Phase 2 & Phase 4!
    T_comp_rim_K = float(p2["full_throttle"]["T_t3_K"])
    T_turb_rim_K = min(1090.0, float(p4["peak_temps_C"]["combustor_liner"]) + 273.15 + 45.0)

    # Exact total rim centrifugal blade pull [N] from 19 Inconel 718 blades (m_b = 0.246 g, r_cg = 14.55 mm)
    m_blade = 8190.0 * (4.9e-3 * 0.84e-3) * 7.3e-3
    F_blades_100 = 19.0 * m_blade * (omega_100 ** 2) * 14.55e-3
    F_blades_125 = F_blades_100 * (1.25 ** 2)
    sigma_blade_root_100_MPa = (F_blades_100 / 19.0) / (4.9e-3 * 0.84e-3) * 1e-6

    # 1. CalculiX 3D FEA: Ti-6Al-4V Compressor Impeller (100% & 125% Burst)
    r_c_out = float(pspec.get("compressor_diameter_mm", 38.0)) * 0.5e-3
    comp_100 = _run_ccx_thermo_centrif_disk(
        fea_dir, "comp_100pct", r_in=4.2e-3, r_out=r_c_out, h_bore=9.6e-3, h_rim=2.0e-3,
        omega=omega_100, E_Pa=106e9, nu=0.342, rho=4430.0, cte=8.6e-6,
        T_ref_K=293.15, T_bore_K=340.0, T_rim_K=T_comp_rim_K, total_rim_pull_N=120.0,
    )
    comp_125 = _run_ccx_thermo_centrif_disk(
        fea_dir, "comp_125pct_burst", r_in=4.2e-3, r_out=r_c_out, h_bore=9.6e-3, h_rim=2.0e-3,
        omega=omega_125, E_Pa=106e9, nu=0.342, rho=4430.0, cte=8.6e-6,
        T_ref_K=293.15, T_bore_K=345.0, T_rim_K=T_comp_rim_K + 15.0, total_rim_pull_N=120.0 * 1.5625,
    )

    # 2. CalculiX 3D FEA: Inconel 718 Turbine Disk (100% & 125% Burst) + Thermal Gradient
    turb_100 = _run_ccx_thermo_centrif_disk(
        fea_dir, "turb_100pct", r_in=3.5e-3, r_out=11.4e-3, h_bore=5.6e-3, h_rim=4.4e-3,
        omega=omega_100, E_Pa=168e9, nu=0.29, rho=8190.0, cte=14.2e-6,
        T_ref_K=293.15, T_bore_K=T_turb_rim_K - 210.0, T_rim_K=T_turb_rim_K, total_rim_pull_N=F_blades_100,
    )
    turb_125 = _run_ccx_thermo_centrif_disk(
        fea_dir, "turb_125pct_burst", r_in=3.5e-3, r_out=11.4e-3, h_bore=5.6e-3, h_rim=4.4e-3,
        omega=omega_125, E_Pa=168e9, nu=0.29, rho=8190.0, cte=14.2e-6,
        T_ref_K=293.15, T_bore_K=T_turb_rim_K - 210.0, T_rim_K=T_turb_rim_K, total_rim_pull_N=F_blades_125,
    )

    sf_comp_100 = 760.0 / max(comp_100["max_vm_MPa"], 1e-3)
    sf_comp_burst = 950.0 / max(comp_125["mean_vm_MPa"], 1e-3)
    sf_turb_100 = 815.0 / max(turb_100["max_vm_MPa"], sigma_blade_root_100_MPa)
    sf_turb_burst = 1020.0 / max(turb_125["mean_vm_MPa"], 1e-3)

    # AMS 5662 Inconel 718 Larson-Miller Creep Rupture Life at turbine root
    T_root_K = min(1025.0, T_turb_rim_K - 60.0)
    lmp_allow = 39.8 - 6.2 * math.log10(max(sigma_blade_root_100_MPa, 50.0))
    creep_life_hr = 10.0 ** min(6.0, max(-2.0, (lmp_allow * 1000.0 / T_root_K) - 20.0))

    # 3. ROSS 3.0 Rotordynamics
    rd = _run_ross_rotordynamics(rpm_max=rpm_max, rpm_idle=rpm_idle)
    if rd["crit_speeds_rpm"]:
        sep_max_pct = min(abs(c - rpm_max) / rpm_max * 100.0 for c in rd["crit_speeds_rpm"])
        sep_idle_pct = min(abs(c - rpm_idle) / rpm_idle * 100.0 for c in rd["crit_speeds_rpm"])
    else:
        sep_max_pct, sep_idle_pct = 50.0, 50.0
    min_sep_pct = min(sep_max_pct, sep_idle_pct)

    checks = {
        "compressor_fea_100_and_125_burst": {
            "pass": (sf_comp_100 >= 1.50 and sf_comp_burst >= 1.15),
            "measured": f"100% σ_vm={comp_100['max_vm_MPa']:.1f} MPa (SF={sf_comp_100:.2f}), 125% Burst SF={sf_comp_burst:.2f}",
            "target": "Yield SF ≥ 1.50 @ 100%, Burst SF ≥ 1.15 @ 125% RPM",
        },
        "turbine_fea_thermo_and_creep": {
            "pass": (sf_turb_100 >= 1.50 and sf_turb_burst >= 1.15 and creep_life_hr >= 50.0),
            "measured": f"100% Disk σ_vm={turb_100['max_vm_MPa']:.1f} MPa, Blade={sigma_blade_root_100_MPa:.1f} MPa (SF={sf_turb_100:.2f}), Creep={creep_life_hr:.0f} hr",
            "target": "Yield SF ≥ 1.50 @ 100%, Burst SF ≥ 1.15 @ 125%, Creep ≥ 50 hr",
        },
        "ross_critical_speed_margin": {
            "pass": (min_sep_pct >= 15.0),
            "measured": f"ROSS Crits={rd['crit_speeds_rpm']} RPM (Sep_max={sep_max_pct:.1f}%, Sep_idle={sep_idle_pct:.1f}%)",
            "target": "Critical speed separation ≥ 15% from Idle & Max RPM",
        },
        "ross_iso1940_unbalance_and_bearing_dn": {
            "pass": (rd["peak_g10_op_um"] <= 15.0 and rd["bearing_dn_million"] <= 2.20),
            "measured": f"G0.4={rd['peak_g04_op_um']:.2f} μm, G1.0={rd['peak_g10_op_um']:.2f} μm, dm·N={rd['bearing_dn_million']:.2f}M, F_gyro={rd['F_brg_gyro_N']:.2f} N",
            "target": "G1.0 orbit ≤ 15 μm, Ceramic Bearing dm·N ≤ 2.20M",
        },
    }

    summary = {
        "phase": 5,
        "title": "3D Thermo-Mechanical FEA (CalculiX 100%/125%) & Rotordynamics (ROSS 3.0)",
        "solver": f"CalculiX ccx 3D C3D8 + ROSS {rd['ross_version']}",
        "verdict": "PASS" if all(c["pass"] for c in checks.values()) else "FAIL",
        "elapsed_sec": round(time.perf_counter() - t0, 2),
        "checks": checks,
        "fea": {
            "comp_100": comp_100,
            "comp_125": comp_125,
            "turb_100": turb_100,
            "turb_125": turb_125,
            "sf_comp_100": round(sf_comp_100, 3),
            "sf_comp_burst_125": round(sf_comp_burst, 3),
            "sf_turb_100": round(sf_turb_100, 3),
            "sf_turb_burst_125": round(sf_turb_burst, 3),
            "blade_root_100_MPa": round(sigma_blade_root_100_MPa, 1),
            "creep_life_hr": round(creep_life_hr, 1),
        },
        "rotordynamics": {
            k: v for k, v in rd.items() if not isinstance(v, np.ndarray)
        },
    }

    store.save_phase(
        "phase05_struct_rotor",
        summary,
        arrays={
            "ross_speed_rpm": rd["speed_rpm"],
            "ross_campbell_wd_rpm": rd["campbell_wd_rpm"],
            "ross_unbal_g04_um": rd["amp_g04_um"],
            "ross_unbal_g10_um": rd["amp_g10_um"],
        },
    )
    print(
        f"  -> Phase 5 Verdict: {summary['verdict']} ({summary['elapsed_sec']:.2f}s) | "
        f"CCX Comp={comp_100['max_vm_MPa']:.0f} MPa (SF={sf_comp_100:.2f}), Turb={turb_100['max_vm_MPa']:.0f} MPa (SF={sf_turb_100:.2f}), "
        f"ROSS Crits={rd['crit_speeds_rpm']}, DN={rd['bearing_dn_million']:.2f}M"
    )
    return summary
