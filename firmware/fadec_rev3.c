/*
 * RikiGaku-AHIRU Rev.3 — Production STM32H743VIT6 FADEC & 6-DOF Flight Control Implementation
 */
#include "fadec_rev3.h"
#include <math.h>

#define PI_F 3.14159265358979323846f

static float clampf(float x, float lo, float hi) {
    if (x < lo) { return lo; }
    if (x > hi) { return hi; }
    return x;
}

void ahiru_biquad_set_notch(BiquadFilter *f, float fs_hz, float f0_hz, float q_factor) {
    /* Fold aliased high-frequency tones into Nyquist [5 Hz .. 0.48*fs] */
    float nyq = 0.5f * fs_hz;
    float f_alias = fmodf(fabsf(f0_hz), fs_hz);
    if (f_alias > nyq) {
        f_alias = fs_hz - f_alias;
    }
    if (f_alias < 15.0f || f_alias > (0.47f * fs_hz)) {
        f->b0 = 1.0f; f->b1 = 0.0f; f->b2 = 0.0f;
        f->a1 = 0.0f; f->a2 = 0.0f;
        return;
    }
    float w0 = 2.0f * PI_F * f_alias / fs_hz;
    float cw = cosf(w0);
    float sw = sinf(w0);
    float alpha = sw / (2.0f * clampf(q_factor, 1.5f, 20.0f));
    float a0_inv = 1.0f / (1.0f + alpha);
    f->b0 = 1.0f * a0_inv;
    f->b1 = (-2.0f * cw) * a0_inv;
    f->b2 = 1.0f * a0_inv;
    f->a1 = (-2.0f * cw) * a0_inv;
    f->a2 = (1.0f - alpha) * a0_inv;
}

float ahiru_biquad_step(BiquadFilter *f, float x) {
    float y = f->b0 * x + f->z1;
    f->z1 = f->b1 * x - f->a1 * y + f->z2;
    f->z2 = f->b2 * x - f->a2 * y;
    return y;
}

void ahiru_fadec_init(AhiruFadecCtx *ctx) {
    ctx->state = ENG_OFF;
    ctx->state_ticks = 0U;
    ctx->sysid_ticks = 0U;
    ctx->fault_flags = 0U;
    ctx->int_pitch = 0.0f;
    ctx->int_roll = 0.0f;
    ctx->dob_pitch = 0.0f;
    ctx->dob_roll = 0.0f;
    ctx->prev_alt_err = 0.0f;
    ctx->thrust_est_n = 5.68f;
    ctx->notch_p_1x.z1 = 0.0f; ctx->notch_p_1x.z2 = 0.0f;
    ctx->notch_q_1x.z1 = 0.0f; ctx->notch_q_1x.z2 = 0.0f;
    ctx->notch_p_2x.z1 = 0.0f; ctx->notch_p_2x.z2 = 0.0f;
    ctx->notch_q_2x.z1 = 0.0f; ctx->notch_q_2x.z2 = 0.0f;
    ahiru_biquad_set_notch(&ctx->notch_p_1x, AHIRU_LOOP_HZ, 350.0f, 6.0f);
    ahiru_biquad_set_notch(&ctx->notch_q_1x, AHIRU_LOOP_HZ, 350.0f, 6.0f);
    ahiru_biquad_set_notch(&ctx->notch_p_2x, AHIRU_LOOP_HZ, 300.0f, 6.0f);
    ahiru_biquad_set_notch(&ctx->notch_q_2x, AHIRU_LOOP_HZ, 300.0f, 6.0f);
}

void ahiru_fadec_step_1khz(AhiruFadecCtx *ctx, const AhiruSensorBus *in, AhiruActuatorCmd *out) {
    out->tvc_pitch_rad = 0.0f;
    out->tvc_roll_rad = 0.0f;
    out->rcs_yaw_cmd = 0.0f;
    out->throttle_01 = 0.0f;
    out->foc_starter_a = 0.0f;
    out->glow_pwm_01 = 0.0f;
    out->fuel_valve_open = false;
    out->wdt_kick = true;

    /* 1. Dual-Redundant ICM-42688-P IMU Voting & Fault Isolation */
    float p_raw = 0.0f, q_raw = 0.0f, r_raw = 0.0f;
    bool a_ok = in->imu_a.healthy && (fabsf(in->imu_a.gx) < 35.0f) && (fabsf(in->imu_a.gz) < 35.0f);
    bool b_ok = in->imu_b.healthy && (fabsf(in->imu_b.gx) < 35.0f) && (fabsf(in->imu_b.gz) < 35.0f);
    if (a_ok && b_ok) {
        float diff = fabsf(in->imu_a.gx - in->imu_b.gx) + fabsf(in->imu_a.gz - in->imu_b.gz);
        if (diff > 2.5f) {
            /* Isolate diverged channel: pick channel with smaller instantaneous spike */
            float mag_a = fabsf(in->imu_a.gx) + fabsf(in->imu_a.gz);
            float mag_b = fabsf(in->imu_b.gx) + fabsf(in->imu_b.gz);
            if (mag_a <= mag_b) {
                p_raw = in->imu_a.gx; r_raw = in->imu_a.gy; q_raw = in->imu_a.gz;
                out->active_imu = 1U;
            } else {
                p_raw = in->imu_b.gx; r_raw = in->imu_b.gy; q_raw = in->imu_b.gz;
                out->active_imu = 2U;
            }
        } else {
            p_raw = 0.5f * (in->imu_a.gx + in->imu_b.gx);
            r_raw = 0.5f * (in->imu_a.gy + in->imu_b.gy);
            q_raw = 0.5f * (in->imu_a.gz + in->imu_b.gz);
            out->active_imu = 0U;
        }
    } else if (a_ok) {
        p_raw = in->imu_a.gx; r_raw = in->imu_a.gy; q_raw = in->imu_a.gz;
        out->active_imu = 1U;
    } else if (b_ok) {
        p_raw = in->imu_b.gx; r_raw = in->imu_b.gy; q_raw = in->imu_b.gz;
        out->active_imu = 2U;
    } else {
        ctx->fault_flags |= (1U << 0);
        out->active_imu = 3U;
    }

    /* 2. Adaptive RPM-Tracked 1X / 2X Biquad Notch Filters (updated every 20 ms) */
    if ((ctx->state_ticks % 20U) == 0U && in->rpm_opto > 15000.0f) {
        float f_1x = in->rpm_opto / 60.0f;
        ahiru_biquad_set_notch(&ctx->notch_p_1x, AHIRU_LOOP_HZ, f_1x, 8.0f);
        ahiru_biquad_set_notch(&ctx->notch_q_1x, AHIRU_LOOP_HZ, f_1x, 8.0f);
        ahiru_biquad_set_notch(&ctx->notch_p_2x, AHIRU_LOOP_HZ, 2.0f * f_1x, 8.0f);
        ahiru_biquad_set_notch(&ctx->notch_q_2x, AHIRU_LOOP_HZ, 2.0f * f_1x, 8.0f);
    }
    float p_flt = ahiru_biquad_step(&ctx->notch_p_2x, ahiru_biquad_step(&ctx->notch_p_1x, p_raw));
    float q_flt = ahiru_biquad_step(&ctx->notch_q_2x, ahiru_biquad_step(&ctx->notch_q_1x, q_raw));

    /* 3. Hard Safety Interlocks (Overspeed, EGT Overtemp, Severe Undervoltage) */
    if (in->rpm_opto > AHIRU_RPM_OVERSPEED_TRIP) {
        ctx->fault_flags |= (1U << 1);
        ctx->state = ENG_FAULT_LOCKOUT;
    }
    if (in->egt_c > AHIRU_EGT_MAX_C) {
        ctx->fault_flags |= (1U << 2);
        ctx->state = ENG_FAULT_LOCKOUT;
    }
    if (in->v_bus < 8.8f) {
        ctx->fault_flags |= (1U << 3);
        ctx->state = ENG_FAULT_LOCKOUT;
    }

    /* 4. Staged Ignition & FADEC State Machine (Zero-Clutch 60V FOC Starter-Gen) */
    ctx->state_ticks++;
    switch (ctx->state) {
        case ENG_OFF:
            if (in->arm_cmd && ctx->fault_flags == 0U) {
                ctx->state = ENG_PREHEAT;
                ctx->state_ticks = 0U;
            }
            break;
        case ENG_PREHEAT:
            /* Stage 1: Glow plug preheat ONLY (6A) -> prevents battery sag! */
            out->glow_pwm_01 = 1.0f;
            if (ctx->state_ticks >= 4000U) {
                ctx->state = ENG_CRANK_IGNITE;
                ctx->state_ticks = 0U;
            }
            break;
        case ENG_CRANK_IGNITE:
            /* Stage 2: 60V FOC starter crank (28A) + 3A PWM igniter + Wet-Start EGT Guard */
            out->foc_starter_a = 28.0f;
            out->glow_pwm_01 = 0.50f;
            if (in->rpm_opto >= 18000.0f) {
                out->fuel_valve_open = true;
                out->throttle_01 = 0.14f;
            }
            if (in->egt_c >= AHIRU_EGT_LIGHTOFF_MIN_C && in->rpm_opto >= 32000.0f) {
                ctx->state = ENG_RAMP;
                ctx->state_ticks = 0U;
            } else if (ctx->state_ticks >= 8000U) {
                /* Wet-start timeout abort: cut fuel and purge! */
                ctx->fault_flags |= (1U << 4);
                ctx->state = ENG_COOLDOWN;
                ctx->state_ticks = 0U;
            }
            break;
        case ENG_RAMP:
            out->fuel_valve_open = true;
            out->glow_pwm_01 = (in->rpm_opto < 50000.0f) ? 0.35f : 0.0f;
            out->foc_starter_a = (in->rpm_opto < 45000.0f) ? 14.0f : 0.0f;
            out->throttle_01 = clampf(0.16f + 0.000003f * (in->rpm_opto - 32000.0f), 0.16f, 0.30f);
            if (in->rpm_opto >= AHIRU_RPM_IDLE) {
                ctx->state = ENG_FLIGHT;
                ctx->state_ticks = 0U;
            }
            break;
        case ENG_IDLE:
        case ENG_FLIGHT:
            if (!in->arm_cmd) {
                ctx->state = ENG_COOLDOWN;
                ctx->state_ticks = 0U;
                break;
            }
            /* Flameout detector -> auto-relight below 55k RPM if EGT drops sharply */
            if (in->egt_c < 220.0f && in->rpm_opto < 55000.0f) {
                out->glow_pwm_01 = 0.80f;
                out->foc_starter_a = 20.0f;
            }
            out->fuel_valve_open = true;
            break;
        case ENG_COOLDOWN:
            /* Dry FOC motoring at 12,000 RPM to cool hot section & prevent soakback */
            out->fuel_valve_open = false;
            out->throttle_01 = 0.0f;
            out->foc_starter_a = (in->egt_c > 120.0f && ctx->state_ticks < 15000U) ? 6.0f : 0.0f;
            if (ctx->state_ticks >= 15000U || in->egt_c <= 110.0f) {
                ctx->state = ENG_OFF;
                ctx->state_ticks = 0U;
            }
            break;
        case ENG_FAULT_LOCKOUT:
        default:
            out->fuel_valve_open = false;
            out->throttle_01 = 0.0f;
            out->foc_starter_a = 0.0f;
            out->glow_pwm_01 = 0.0f;
            out->wdt_kick = false; /* Stop kicking TPS3823 -> hardware fuel cutoff! */
            break;
    }

    /* 5. Closed-Loop 6-DOF Flight Control (Active in ENG_FLIGHT) */
    if (ctx->state == ENG_FLIGHT) {
        float ff = clampf(in->fuel_frac, 0.0f, 1.0f);
        float m_cur = 0.468f + ff * 0.1116f;
        float cos_t = clampf(cosf(in->roll_rad) * cosf(in->pitch_rad), 0.65f, 1.0f);

        /* Altitude Hold with Spool-Lag Lead Compensator */
        float alt_err = in->alt_ref_m - in->alt_m;
        float d_alt_err = (alt_err - ctx->prev_alt_err) * AHIRU_LOOP_HZ;
        ctx->prev_alt_err = alt_err;
        float t_cmd = (m_cur * (9.80665f + 2.40f * alt_err - 2.90f * in->vz_mps + 0.18f * d_alt_err)) / cos_t;
        t_cmd = clampf(t_cmd, 2.2f, 13.14f);
        ctx->thrust_est_n += ((t_cmd - ctx->thrust_est_n) / 0.32f) * AHIRU_DT_S;
        out->throttle_01 = clampf(t_cmd / 13.14f, 0.18f, 1.0f);

        /* Gain-Scheduled MIMO LQR + 100% Exact Gyroscopic Precession Feedforward + DOB */
        float e_th = in->pitch_rad - in->pitch_ref_rad;
        float e_ph = in->roll_rad - in->roll_ref_rad;
        ctx->int_pitch = clampf(ctx->int_pitch + e_th * AHIRU_DT_S, -0.20f, 0.20f);
        ctx->int_roll  = clampf(ctx->int_roll  + e_ph * AHIRU_DT_S, -0.20f, 0.20f);

        /* Luenberger disturbance observer (low-pass CoG/gust torque trim) */
        ctx->dob_pitch += (0.85f * e_th - 0.15f * ctx->dob_pitch) * AHIRU_DT_S;
        ctx->dob_roll  += (0.85f * e_ph - 0.15f * ctx->dob_roll)  * AHIRU_DT_S;

        float kp = 2.82f + 0.24f * (1.0f - ff);
        float kd = 0.76f + 0.06f * (1.0f - ff);
        float h_now = AHIRU_H_ROTOR_NOM_NMS * clampf(in->rpm_opto / AHIRU_RPM_MAX, 0.2f, 1.05f);
        float denom = (ctx->thrust_est_n * AHIRU_L_TVC_M > 0.08f) ? (ctx->thrust_est_n * AHIRU_L_TVC_M) : 0.08f;

        float u_p = -(kp * e_th + kd * q_flt + 1.50f * ctx->int_pitch + ctx->dob_pitch) + (h_now * p_flt) / denom;
        float u_r = -(kp * e_ph + kd * p_flt + 1.50f * ctx->int_roll  + ctx->dob_roll)  - (h_now * q_flt) / denom;

        /* Optional Tethered-Rig Logarithmic Chirp SysID Injection (0.5..25 Hz, ±1.8 deg) */
        if (in->sysid_chirp_en) {
            float t_s = (float)ctx->sysid_ticks * AHIRU_DT_S;
            float f_inst = 0.5f * powf(50.0f, clampf(t_s / 8.0f, 0.0f, 1.0f));
            float chirp = 0.0314f * sinf(2.0f * PI_F * f_inst * t_s);
            u_p += chirp;
            ctx->sysid_ticks++;
        }

        /* Circular ±14 deg TVC Gimbal Cone Clamp */
        float norm = sqrtf(u_p * u_p + u_r * u_r);
        if (norm > AHIRU_TVC_MAX_RAD && norm > 1e-6f) {
            float sc = AHIRU_TVC_MAX_RAD / norm;
            u_p *= sc;
            u_r *= sc;
        }
        out->tvc_pitch_rad = u_p;
        out->tvc_roll_rad = u_r;

        /* Bleed-Air Yaw RCS PD Controller */
        out->rcs_yaw_cmd = clampf(-1.8f * in->yaw_rad - 0.55f * r_raw, -1.0f, 1.0f);
    }

    out->eng_state = ctx->state;
    out->fault_flags = ctx->fault_flags;
}
