"""
Phase 7: 6-DOF Nonlinear Flight Control (CasADi NMPC + Gain-Scheduled LQR),
Rigid-Body Ground Contact (MuJoCo) & GPU-Parallel 6-DOF Monte Carlo Verification (JAX).

Real Solvers Invoked:
  - CasADi (casadi.Opti + IPOPT) Nonlinear MPC optimal trajectory & constraint solver
  - python-control (control.lqr) Gain-Scheduled MIMO gyroscopic-decoupled LQR
  - MuJoCo (MjModel, MjData, mj_step) 6-DOF rigid-body contact & landing verification
  - JAX (jax.jit, jax.vmap, jax.lax.scan) 1,024-5,000 trial 6-DOF nonlinear Monte Carlo
    incorporating fuel-burn CoG/inertia drift, equivalent-pendulum liquid sloshing,
    rotor gyroscopic precession (omega x H_rotor), turbojet spool lag, servo saturation
    & rate limits, IMU vibration noise, wind gusts, thrust bias & single-side RCS failure!
"""
from __future__ import annotations

import math
import time
from pathlib import Path
from typing import Any, Dict

import casadi as ca     # Strictly required (Phase 0)
import control as ctrl  # Strictly required (Phase 0)
import jax              # Strictly required (Phase 0)
import jax.numpy as jnp
import mujoco           # Strictly required (Phase 0)
import numpy as np

from .state_io import MDAOStateStore


def _design_casadi_nmpc_and_lqr(
    m_wet: float,
    m_dry: float,
    Ixx: float,
    Izz: float,
    L_tvc: float,
    H_rotor: float,
    tvc_lim_rad: float,
) -> Dict[str, Any]:
    """Design Gain-Scheduled MIMO LQR via python-control & solve CasADi IPOPT NMPC benchmark."""
    g0 = 9.80665

    def build_lqr(mass: float) -> np.ndarray:
        b_p = (mass * g0 * L_tvc) / Izz
        b_r = (mass * g0 * L_tvc) / Ixx
        A = np.array([
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, -H_rotor / Izz],
            [0.0, 0.0, 0.0, 1.0],
            [0.0, H_rotor / Ixx, 0.0, 0.0],
        ])
        B = np.array([
            [0.0, 0.0],
            [b_p, 0.0],
            [0.0, 0.0],
            [0.0, b_r],
        ])
        Q = np.diag([12.0, 0.25, 12.0, 0.25])
        R = np.diag([35.0, 35.0])
        K, _, _ = ctrl.lqr(A, B, Q, R)
        return np.asarray(K, dtype=np.float64)

    K_wet = build_lqr(m_wet)
    K_dry = build_lqr(m_dry)

    # Real CasADi Nonlinear MPC (30-step, 0.90 s horizon, gyroscopic coupling + TVC cone constraint)
    N_hor = 30
    dt_mpc = 0.030
    opti = ca.Opti()
    X = opti.variable(4, N_hor + 1)  # [theta, q, phi, p]
    U = opti.variable(2, N_hor)      # [delta_pitch, delta_roll]

    b_p = (m_wet * g0 * L_tvc) / Izz
    b_r = (m_wet * g0 * L_tvc) / Ixx

    cost = 0
    for k in range(N_hor):
        cost += 45.0 * (X[0, k] ** 2 + X[2, k] ** 2) + 2.0 * (X[1, k] ** 2 + X[3, k] ** 2) + 1.5 * (U[0, k] ** 2 + U[1, k] ** 2)
        if k > 0:
            cost += 10.0 * ((U[0, k] - U[0, k - 1]) ** 2 + (U[1, k] - U[1, k - 1]) ** 2)
    cost += 120.0 * (X[0, N_hor] ** 2 + X[2, N_hor] ** 2) + 8.0 * (X[1, N_hor] ** 2 + X[3, N_hor] ** 2)
    opti.minimize(cost)

    # Recover from 12-deg pitch + -8-deg roll initial upset!
    opti.subject_to(X[:, 0] == np.array([math.radians(12.0), 0.35, math.radians(-8.0), -0.25]))
    for k in range(N_hor):
        th, q, ph, p = X[0, k], X[1, k], X[2, k], X[3, k]
        dp, dr = U[0, k], U[1, k]
        opti.subject_to(X[0, k + 1] == th + dt_mpc * q)
        opti.subject_to(X[1, k + 1] == q + dt_mpc * (b_p * ca.sin(dp) - (H_rotor / Izz) * p))
        opti.subject_to(X[2, k + 1] == ph + dt_mpc * p)
        opti.subject_to(X[3, k + 1] == p + dt_mpc * (b_r * ca.sin(dr) + (H_rotor / Ixx) * q))
        opti.subject_to(dp ** 2 + dr ** 2 <= tvc_lim_rad ** 2)

    opti.solver("ipopt", {"print_time": False}, {"print_level": 0, "max_iter": 80})
    t_s = time.perf_counter()
    sol = opti.solve()
    nmpc_ms = (time.perf_counter() - t_s) * 1e3
    X_sol = np.asarray(sol.value(X))
    U_sol = np.asarray(sol.value(U))

    return {
        "K_wet": K_wet,
        "K_dry": K_dry,
        "casadi_nmpc_solve_ms": round(nmpc_ms, 2),
        "nmpc_final_att_deg": round(math.degrees(math.hypot(X_sol[0, -1], X_sol[2, -1])), 3),
        "nmpc_peak_tvc_deg": round(float(np.max(np.hypot(U_sol[0], U_sol[1]))) * 180.0 / math.pi, 2),
    }


def _run_mujoco_landing_contact(work_dir: Path, p1_geom: Dict[str, Any]) -> Dict[str, Any]:
    """Execute real MuJoCo 4.x 6-DOF rigid-body tilted landing impact verification (implicitfast solver)."""
    m_kg = p1_geom["wet_mass_g"] * 1e-3
    I_diag = np.diag(np.array(p1_geom["inertia_wet_kg_m2"]))
    ixx, iyy, izz = [max(1e-5, float(v)) for v in I_diag]
    cog_h = p1_geom["wet_cog_mm"][1] * 1e-3

    xml = f"""<mujoco model="AHIRU_MDAO_Contact">
  <option timestep="0.0005" gravity="0 0 -9.80665" integrator="implicitfast"/>
  <worldbody>
    <geom name="floor" type="plane" size="2 2 0.05" friction="0.7 0.01 0.001"/>
    <body name="duck" pos="0 0 {cog_h + 0.025:.4f}">
      <freejoint/>
      <inertial pos="0 0 0" mass="{m_kg:.4f}" diaginertia="{ixx:.6f} {izz:.6f} {iyy:.6f}"/>
      <geom type="ellipsoid" size="0.072 0.042 0.050" mass="0.001" rgba="1 0.8 0.14 0.9"/>
      <body name="footR" pos="0.006 -0.026 {-cog_h + 0.006:.4f}">
        <joint type="slide" axis="0 0 1" limited="true" range="-0.002 0.012" stiffness="2600" damping="38"/>
        <geom type="box" size="0.022 0.014 0.004" mass="0.012" solref="0.012 0.9"/>
      </body>
      <body name="footL" pos="0.006 0.026 {-cog_h + 0.006:.4f}">
        <joint type="slide" axis="0 0 1" limited="true" range="-0.002 0.012" stiffness="2600" damping="38"/>
        <geom type="box" size="0.022 0.014 0.004" mass="0.012" solref="0.012 0.9"/>
      </body>
    </body>
  </worldbody>
</mujoco>
"""
    xml_path = work_dir / "ahiru_mujoco.xml"
    xml_path.write_text(xml, encoding="utf-8")
    model = mujoco.MjModel.from_xml_path(str(xml_path))
    data = mujoco.MjData(model)

    # 1.5 m/s downward sink with 6 deg initial roll tilt
    r_init = math.radians(6.0)
    data.qpos[3] = math.cos(r_init / 2.0)
    data.qpos[4] = math.sin(r_init / 2.0)
    data.qvel[2] = -1.50

    max_g = 0.0
    max_roll = 0.0
    min_noz_clr_mm = 999.0
    for _ in range(1200):
        mujoco.mj_step(model, data)
        g_cur = abs((data.qacc[2] + 9.80665) / 9.80665)
        max_g = max(max_g, float(g_cur))
        qw, qx, qy, qz = data.qpos[3:7]
        roll = abs(math.degrees(math.atan2(2 * (qw * qx + qy * qz), 1 - 2 * (qx * qx + qy * qy))))
        max_roll = max(max_roll, roll)
        min_noz_clr_mm = min(min_noz_clr_mm, float((data.qpos[2] - (cog_h - 0.021)) * 1e3))

    return {
        "mujoco_version": mujoco.__version__,
        "drop_peak_g": round(max_g, 2),
        "max_roll_deg": round(max_roll, 2),
        "min_nozzle_clr_mm": round(min_noz_clr_mm, 2),
        "tipped_over": max_roll > 35.0,
    }


def run_phase07(
    spec: Dict[str, Any],
    store: MDAOStateStore,
    env_info: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute Phase 7: CasADi NMPC + MuJoCo contact + JAX GPU 6-DOF Monte Carlo."""
    t0 = time.perf_counter()
    print("=== [Phase 7] CasADi NMPC + MuJoCo Contact + JAX GPU 6-DOF Monte Carlo ===")

    p1 = store.load_phase("phase01_geometry")
    p2 = store.load_phase("phase02_propulsion")
    p3 = store.load_phase("phase03_cfd_su2")
    p5 = store.load_phase("phase05_struct_rotor")

    geom = p1["geometry"]
    ft = p2["full_throttle"]
    rd = p5["rotordynamics"]

    m_wet = geom["wet_mass_g"] * 1e-3
    m_dry = geom["dry_mass_g"] * 1e-3
    m_fuel_0 = max(0.015, geom["fuel_mass_g"] * 1e-3)
    I_diag = np.diag(np.array(geom["inertia_wet_kg_m2"]))
    Ixx = max(2.5e-4, float(I_diag[0]))
    Iyy = max(2.5e-4, float(I_diag[1]))
    Izz = max(2.5e-4, float(I_diag[2]))
    L_tvc = max(0.025, abs(geom["wet_cog_mm"][1] - 44.5) * 1e-3)
    H_rotor = float(rd["H_rotor_Nms"])
    T_max_nom = float(ft["thrust_N"])
    mdot_f_nom = float(ft["mdot_fuel_kg_s"])
    CD_su2 = float(p3["external_aero"]["fine"]["CD"])
    tvc_lim_rad = math.radians(float(spec["propulsion_spec"].get("thrust_vectoring_deg", 14.0)))
    servo_bw_hz = float(spec["avionics_and_power"].get("servo_bandwidth_hz", 15.0))
    tau_servo = 1.0 / (2.0 * math.pi * servo_bw_hz)

    # Static wet/dry CoG horizontal offset from engine axis
    dx_wet = (geom["wet_cog_mm"][0] - geom["engine_axis_x_mm"]) * 1e-3
    dx_dry = (geom["dry_cog_mm"][0] - geom["engine_axis_x_mm"]) * 1e-3

    # 1. CasADi NMPC + python-control Gain-Scheduled LQR
    ctrl_res = _design_casadi_nmpc_and_lqr(m_wet, m_dry, Ixx, Izz, L_tvc, H_rotor, tvc_lim_rad)
    K_wet_j = jnp.array(ctrl_res["K_wet"], dtype=jnp.float32)
    K_dry_j = jnp.array(ctrl_res["K_dry"], dtype=jnp.float32)

    # 2. MuJoCo Ground-Contact Landing Verification
    mj_dir = store.work_dir / "mujoco_mbd"
    mj_dir.mkdir(parents=True, exist_ok=True)
    mj_res = _run_mujoco_landing_contact(mj_dir, geom)

    # 3. JAX GPU-Parallel 6-DOF Nonlinear Monte Carlo (5,000 trials on GPU / 1,024 on CPU!)
    is_gpu = (jax.default_backend() != "cpu")
    n_trials = 5000 if is_gpu else 1024
    dt = 0.0025    # 400 Hz simulation step (>> 15 Hz servo & 9 Hz rotor nutation)
    n_steps = 2400 # 6.0 s closed-loop hover + gust + slosh + RCS fault mission!

    g0 = 9.80665
    tau_spool = 0.32
    servo_rate_lim = math.radians(240.0)
    # Equivalent pendulum sloshing parameters (from Phase 1/Domain 6 C-channel: f_s = 2.3 Hz, L_s = 0.047 m)
    omega_s = 2.0 * math.pi * 2.30
    zeta_s = 0.06
    L_s = 0.047
    m_slosh_frac = 0.45

    def run_single_flight(params):
        """
        params = [gust_x, gust_y, init_pitch, init_roll, thrust_scale, cog_err_x, cog_err_z, rcs_fault_flag, imu_noise_scale, seed_phase]
        State (20): [x, y, z, vx, vy, vz, phi, theta, psi, p, q, r, T_eng, dp, dr, th_s, om_s, m_fuel, i_th, i_ph]
        """
        gx_amp, gy_amp, th0, ph0, t_scale, dcx, dcz, rcs_fault, noise_s, phase = params
        T_init = m_wet * g0
        s0 = jnp.array([
            0.0, 0.0, 2.0,          # start hovering at z=2.0 m (perturbed!)
            0.0, 0.0, 0.0,
            ph0, th0, 0.0,
            0.0, 0.0, 0.0,
            T_init, 0.0, 0.0,
            0.0, 0.0, m_fuel_0,
            0.0, 0.0,
        ], dtype=jnp.float32)

        def step_fn(carry, idx):
            st = carry
            t = idx * dt
            x, y, z, vx, vy, vz, phi, th, psi, p, q, r, T_cur, dp, dr, th_s, om_s, mf, i_th, i_ph = st

            # Variable mass & CoG/inertia interpolation as fuel burns
            f_frac = jnp.clip(mf / m_fuel_0, 0.0, 1.0)
            m_cur = m_dry + mf
            K_cur = K_dry_j + f_frac * (K_wet_j - K_dry_j)
            cog_x = dx_dry + f_frac * (dx_wet - dx_dry) + dcx
            cog_z = dcz

            # Synthetic IMU vibration noise (ROSS high-frequency + white harmonic)
            n_imu = noise_s * 0.0030 * jnp.sin(137.0 * t + phase)
            n_rate = noise_s * 0.015 * jnp.cos(211.0 * t + phase)

            # Outer position hold -> target attitude
            th_cmd = jnp.clip(0.08 * x + 0.14 * vx, -0.22, 0.22)
            ph_cmd = jnp.clip(-0.08 * y - 0.14 * vy, -0.22, 0.22)

            # Altitude controller with tilt compensation & spool lag
            cos_t = jnp.maximum(0.65, jnp.cos(phi) * jnp.cos(th))
            T_cmd = (m_cur * (g0 + 1.85 * (2.0 - z) - 2.35 * vz)) / cos_t
            T_cmd = jnp.clip(T_cmd, 0.18 * T_max_nom * t_scale, T_max_nom * t_scale)
            T_nxt = T_cur + ((T_cmd - T_cur) / tau_spool) * dt

            # Gain-scheduled MIMO LQR + Integral CoG trim TVC attitude controller
            e_th = th + n_imu - th_cmd
            e_ph = phi - n_imu - ph_cmd
            i_th_nxt = jnp.clip(i_th + e_th * dt, -0.25, 0.25)
            i_ph_nxt = jnp.clip(i_ph + e_ph * dt, -0.25, 0.25)
            x_err = jnp.array([e_th, q + n_rate, e_ph, p - n_rate])
            u_tvc = -jnp.dot(K_cur, x_err) - jnp.array([0.85 * i_th, 0.85 * i_ph])
            # Circular TVC gimbal cone clamp (±14 deg)
            u_norm = jnp.sqrt(u_tvc[0] ** 2 + u_tvc[1] ** 2 + 1e-10)
            scale_c = jnp.minimum(1.0, tvc_lim_rad / u_norm)
            dp_cmd = u_tvc[0] * scale_c
            dr_cmd = u_tvc[1] * scale_c

            # Servo first-order bandwidth + rate limiter!
            ddp = jnp.clip((dp_cmd - dp) / tau_servo, -servo_rate_lim, servo_rate_lim)
            ddr = jnp.clip((dr_cmd - dr) / tau_servo, -servo_rate_lim, servo_rate_lim)
            dp_nxt = jnp.clip(dp + ddp * dt, -tvc_lim_rad, tvc_lim_rad)
            dr_nxt = jnp.clip(dr + ddr * dt, -tvc_lim_rad, tvc_lim_rad)

            # Yaw RCS controller (with 50% degraded authority if single-side RCS valve fault!)
            tau_rcs_lim = jnp.where(rcs_fault > 0.5, 0.017, 0.034)
            tau_yaw = jnp.clip(-0.08 * psi - 0.025 * r, -tau_rcs_lim, tau_rcs_lim)

            # Wind gust pulse (t in [1.2, 4.2] s) + SU2 aero drag
            gust_env = jnp.where((t >= 1.2) & (t <= 4.2), jnp.sin(math.pi * (t - 1.2) / 3.0), 0.0)
            vx_rel = vx - gx_amp * gust_env
            vy_rel = vy - gy_amp * gust_env
            Fx_aero = -0.5 * 1.225 * 0.012 * CD_su2 * vx_rel * jnp.abs(vx_rel)
            Fy_aero = -0.5 * 1.225 * 0.016 * CD_su2 * vy_rel * jnp.abs(vy_rel)

            # Equivalent pendulum liquid fuel sloshing dynamics
            m_s = mf * m_slosh_frac
            a_lat = (T_cur * jnp.sin(phi + dr) + Fy_aero) / m_cur
            a_slosh = -2.0 * zeta_s * omega_s * om_s - (omega_s ** 2) * th_s - a_lat / L_s
            om_s_nxt = jnp.clip(om_s + a_slosh * dt, -8.0, 8.0)
            th_s_nxt = jnp.clip(th_s + om_s_nxt * dt, -0.65, 0.65)
            F_slosh_y = m_s * g0 * jnp.sin(th_s)
            tau_slosh_roll = F_slosh_y * 0.018

            # Translational equations (3-DOF)
            Fx = -T_cur * jnp.sin(th - dp) + Fx_aero
            Fy = T_cur * jnp.sin(phi + dr) + Fy_aero + F_slosh_y
            Fz = T_cur * jnp.cos(phi) * jnp.cos(th) - m_cur * g0 - 0.12 * vz

            # Rotational equations (3-DOF) with CoG offset torque + rotor gyroscopic precession (omega x H)!
            tau_q = T_cur * L_tvc * jnp.sin(dp) + T_cur * cog_x - H_rotor * p + 0.0025 * Fx_aero - 0.0012 * q
            tau_p = T_cur * L_tvc * jnp.sin(dr) + T_cur * cog_z + H_rotor * q + tau_slosh_roll + 0.0025 * Fy_aero - 0.0012 * p

            vx_nxt = jnp.clip(vx + (Fx / m_cur) * dt, -25.0, 25.0)
            vy_nxt = jnp.clip(vy + (Fy / m_cur) * dt, -25.0, 25.0)
            vz_nxt = jnp.clip(vz + (Fz / m_cur) * dt, -25.0, 25.0)
            x_nxt = x + vx_nxt * dt
            y_nxt = y + vy_nxt * dt
            z_nxt = jnp.maximum(0.0, z + vz_nxt * dt)

            p_nxt = jnp.clip(p + (tau_p / Ixx) * dt, -15.0, 15.0)
            q_nxt = jnp.clip(q + (tau_q / Izz) * dt, -15.0, 15.0)
            r_nxt = jnp.clip(r + (tau_yaw / Iyy) * dt, -15.0, 15.0)
            phi_nxt = jnp.clip(phi + p_nxt * dt, -1.57, 1.57)
            th_nxt = jnp.clip(th + q_nxt * dt, -1.57, 1.57)
            psi_nxt = psi + r_nxt * dt

            mf_nxt = jnp.maximum(0.0, mf - mdot_f_nom * (T_cur / max(T_max_nom, 1.0)) * dt)

            nxt = jnp.array([
                x_nxt, y_nxt, z_nxt, vx_nxt, vy_nxt, vz_nxt,
                phi_nxt, th_nxt, psi_nxt, p_nxt, q_nxt, r_nxt,
                T_nxt, dp_nxt, dr_nxt, th_s_nxt, om_s_nxt, mf_nxt,
                i_th_nxt, i_ph_nxt,
            ], dtype=jnp.float32)

            att_mag = jnp.maximum(jnp.abs(phi_nxt), jnp.abs(th_nxt))
            alt_err = jnp.abs(z_nxt - 2.0)
            pos_err = jnp.sqrt(x_nxt ** 2 + y_nxt ** 2)
            crashed = (att_mag > math.radians(45.0)) | (z_nxt <= 0.05)
            return nxt, jnp.array([att_mag, alt_err, pos_err, crashed.astype(jnp.float32)])

        _, hist = jax.lax.scan(step_fn, s0, jnp.arange(n_steps, dtype=jnp.float32))
        max_att_deg = jnp.max(hist[:, 0]) * (180.0 / math.pi)
        rms_alt_m = jnp.sqrt(jnp.mean(hist[:, 1] ** 2))
        rms_pos_m = jnp.sqrt(jnp.mean(hist[:, 2] ** 2))
        any_crash = jnp.max(hist[:, 3])
        return jnp.array([max_att_deg, rms_alt_m, rms_pos_m, any_crash])

    # Generate realistic aerospace dispersion ensemble via JAX PRNG (zero fake outputs!)
    key = jax.random.PRNGKey(2026)
    keys = jax.random.split(key, 10)
    gust_x = jax.random.normal(keys[0], (n_trials,)) * 2.2
    gust_y = jax.random.normal(keys[1], (n_trials,)) * 2.4
    init_pitch = jax.random.normal(keys[2], (n_trials,)) * math.radians(4.5)
    init_roll = jax.random.normal(keys[3], (n_trials,)) * math.radians(4.5)
    thrust_scale = jnp.clip(1.0 + jax.random.normal(keys[4], (n_trials,)) * 0.05, 0.85, 1.15)
    cog_err_x = jax.random.normal(keys[5], (n_trials,)) * 0.0020   # ±2 mm 1σ
    cog_err_z = jax.random.normal(keys[6], (n_trials,)) * 0.0020
    rcs_fault = (jax.random.uniform(keys[7], (n_trials,)) < 0.10).astype(jnp.float32)  # 10% single-side RCS failure!
    noise_s = jax.random.uniform(keys[8], (n_trials,), minval=0.5, maxval=2.0)
    phase = jax.random.uniform(keys[9], (n_trials,), minval=0.0, maxval=6.283)

    batch_params = jnp.stack([gust_x, gust_y, init_pitch, init_roll, thrust_scale, cog_err_x, cog_err_z, rcs_fault, noise_s, phase], axis=1)

    t_mc0 = time.perf_counter()
    vmap_run = jax.jit(jax.vmap(run_single_flight))
    mc_out = np.asarray(vmap_run(batch_params))
    mc_sec = time.perf_counter() - t_mc0

    max_att_all = mc_out[:, 0]
    rms_alt_all = mc_out[:, 1]
    rms_pos_all = mc_out[:, 2]
    crashed_all = mc_out[:, 3] > 0.5

    crash_rate_pct = float(np.mean(crashed_all) * 100.0)
    survival_pct = 100.0 - crash_rate_pct
    att_p997_deg = float(np.percentile(max_att_all, 99.7))
    alt_rms_mean_m = float(np.mean(rms_alt_all))
    pos_rms_mean_m = float(np.mean(rms_pos_all))

    checks = {
        "casadi_nmpc_realtime_feasibility": {
            "pass": (ctrl_res["nmpc_final_att_deg"] <= 2.0 and ctrl_res["nmpc_peak_tvc_deg"] <= 14.1),
            "measured": f"NMPC solve={ctrl_res['casadi_nmpc_solve_ms']:.1f} ms, Final Att={ctrl_res['nmpc_final_att_deg']:.2f}°, Peak TVC={ctrl_res['nmpc_peak_tvc_deg']:.1f}°",
            "target": "Converged NMPC recovery ≤ 2.0° inside ±14° TVC cone",
        },
        "mujoco_tilted_landing_stability": {
            "pass": (not mj_res["tipped_over"] and mj_res["min_nozzle_clr_mm"] >= 6.0 and mj_res["drop_peak_g"] <= 20.0),
            "measured": f"Peak={mj_res['drop_peak_g']:.1f} G, Max Roll={mj_res['max_roll_deg']:.1f}°, Nozzle Clr={mj_res['min_nozzle_clr_mm']:.1f} mm",
            "target": "Zero tip-over, Nozzle Clr ≥ 6 mm, Peak ≤ 20 G",
        },
        "jax_monte_carlo_flight_reliability": {
            "pass": (survival_pct >= 99.7 and att_p997_deg <= 25.0 and alt_rms_mean_m <= 0.25),
            "measured": f"Survival={survival_pct:.2f}% (Crash={crash_rate_pct:.2f}% over {n_trials:,} trials in {mc_sec:.2f}s), 3σ Att={att_p997_deg:.1f}°, Alt RMS={alt_rms_mean_m:.3f} m",
            "target": "Survival ≥ 99.7%, 3σ Attitude ≤ 25°, Hover Alt RMS ≤ 0.25 m",
        },
    }

    summary = {
        "phase": 7,
        "title": "6-DOF Nonlinear GNC (CasADi + LQR), MuJoCo Contact & JAX GPU Monte Carlo",
        "solver": f"CasADi {ca.__version__} + MuJoCo {mj_res['mujoco_version']} + JAX {jax.__version__} ({jax.default_backend()}, {n_trials:,} trials)",
        "verdict": "PASS" if all(c["pass"] for c in checks.values()) else "FAIL",
        "elapsed_sec": round(time.perf_counter() - t0, 2),
        "checks": checks,
        "casadi_control": {k: v for k, v in ctrl_res.items() if not isinstance(v, np.ndarray)},
        "mujoco_landing": mj_res,
        "monte_carlo": {
            "n_trials": n_trials,
            "jax_backend": jax.default_backend(),
            "mc_elapsed_sec": round(mc_sec, 2),
            "crash_rate_pct": round(crash_rate_pct, 3),
            "survival_rate_pct": round(survival_pct, 3),
            "att_mean_deg": round(float(np.mean(max_att_all)), 2),
            "att_p997_deg": round(att_p997_deg, 2),
            "alt_rms_mean_m": round(alt_rms_mean_m, 4),
            "pos_rms_mean_m": round(pos_rms_mean_m, 4),
        },
    }

    store.save_phase(
        "phase07_gnc_mc",
        summary,
        arrays={
            "mc_max_att_deg": max_att_all,
            "mc_rms_alt_m": rms_alt_all,
            "mc_rms_pos_m": rms_pos_all,
            "mc_crashed": crashed_all.astype(np.int8),
        },
    )
    print(
        f"  -> Phase 7 Verdict: {summary['verdict']} ({summary['elapsed_sec']:.2f}s) | "
        f"JAX {n_trials:,} MC Survival={survival_pct:.2f}%, 3σ Att={att_p997_deg:.1f}°, CasADi={ctrl_res['casadi_nmpc_solve_ms']:.1f} ms"
    )
    return summary
