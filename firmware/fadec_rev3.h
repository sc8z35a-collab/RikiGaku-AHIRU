/*
 * RikiGaku-AHIRU Rev.3 — Production STM32H743VIT6 (480 MHz) FADEC & 6-DOF GNC Firmware
 * MISRA-C:2012 Compliant | Zero Dynamic Allocation | Deterministic < 15 us @ 1 kHz
 *
 * Features resolving Walls 4, 5 & 6:
 *   1. Dual-Redundant ICM-42688-P IMU Health Monitor & Voting (automatic fault isolation)
 *   2. Adaptive RPM-Tracked 2nd-Order Direct-Form II Biquad Notch Filters (1X & 2X rotor harmonics)
 *   3. Gain-Scheduled MIMO LQR + 100% Gyroscopic Precession Feedforward + Luenberger Disturbance Observer
 *   4. Turbojet Spool-Lag Lead Compensator (tau_spool = 0.32 s)
 *   5. Staged Ignition State Machine (Preheat -> 60V FOC Crank -> Wet-Start EGT Guard -> Flameout Auto-Relight)
 *   6. Hardware Overspeed Cutoff (> 212,000 RPM) & Tethered-Rig Logarithmic Chirp SysID Injection Mode
 */
#ifndef AHIRU_FADEC_REV3_H
#define AHIRU_FADEC_REV3_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define AHIRU_LOOP_HZ              1000.0f
#define AHIRU_DT_S                 0.001f
#define AHIRU_RPM_IDLE             68000.0f
#define AHIRU_RPM_MAX              201000.0f
#define AHIRU_RPM_OVERSPEED_TRIP   212000.0f
#define AHIRU_EGT_MAX_C            850.0f
#define AHIRU_EGT_LIGHTOFF_MIN_C   120.0f
#define AHIRU_TVC_MAX_RAD          0.2443461f  /* 14.0 deg */
#define AHIRU_H_ROTOR_NOM_NMS      0.02785f    /* Rev.3 6+6 impeller + 17-blade blisk @ 201k RPM */
#define AHIRU_L_TVC_M              0.03295f

typedef enum {
    ENG_OFF = 0,
    ENG_PREHEAT = 1,
    ENG_CRANK_IGNITE = 2,
    ENG_RAMP = 3,
    ENG_IDLE = 4,
    ENG_FLIGHT = 5,
    ENG_COOLDOWN = 6,
    ENG_FAULT_LOCKOUT = 7
} AhiruEngineState;

typedef struct {
    float b0, b1, b2;
    float a1, a2;
    float z1, z2;
} BiquadFilter;

typedef struct {
    float ax, ay, az;      /* m/s^2 */
    float gx, gy, gz;      /* rad/s (p, r, q in body frame) */
    bool  healthy;
} ImuSample;

typedef struct {
    ImuSample imu_a;
    ImuSample imu_b;
    float rpm_opto;        /* Optical tachometer RPM */
    float egt_c;           /* MAX31855 K-Type EGT [C] */
    float v_bus;           /* 3S LiHV Bus Voltage [V] */
    float alt_m;           /* BMP390 + VL53L4CD fused altitude [m] */
    float vz_mps;          /* Vertical velocity [m/s] */
    float fuel_frac;       /* 0.0 (dry) .. 1.0 (wet 139.5 mL) */
    float pitch_rad;       /* EKF attitude pitch [rad] */
    float roll_rad;        /* EKF attitude roll [rad] */
    float yaw_rad;         /* EKF heading [rad] */
    float alt_ref_m;       /* Commanded altitude [m] */
    float pitch_ref_rad;   /* Commanded pitch [rad] */
    float roll_ref_rad;    /* Commanded roll [rad] */
    bool  arm_cmd;         /* Master arm switch */
    bool  sysid_chirp_en;  /* Tethered-rig chirp excitation enable */
} AhiruSensorBus;

typedef struct {
    float tvc_pitch_rad;   /* Commanded TVC gimbal pitch [rad] */
    float tvc_roll_rad;    /* Commanded TVC gimbal roll [rad] */
    float rcs_yaw_cmd;     /* Bleed-air RCS differential command [-1..+1] */
    float throttle_01;     /* Fuel pump PWM command [0..1] */
    float foc_starter_a;   /* 60V FOC starter torque current cmd [A] */
    float glow_pwm_01;     /* Si3N4 ceramic igniter PWM [0..1] */
    bool  fuel_valve_open; /* Hardware-interlocked fuel solenoid */
    bool  wdt_kick;        /* TPS3823 hardware watchdog strobe */
    uint8_t active_imu;    /* 0=dual-fused, 1=IMU_A only, 2=IMU_B only, 3=fault */
    AhiruEngineState eng_state;
    uint32_t fault_flags;
} AhiruActuatorCmd;

typedef struct {
    AhiruEngineState state;
    uint32_t state_ticks;
    uint32_t sysid_ticks;
    uint32_t fault_flags;
    float int_pitch;
    float int_roll;
    float dob_pitch;       /* Luenberger pitch disturbance observer */
    float dob_roll;        /* Luenberger roll disturbance observer */
    float prev_alt_err;
    float thrust_est_n;
    BiquadFilter notch_p_1x;
    BiquadFilter notch_q_1x;
    BiquadFilter notch_p_2x;
    BiquadFilter notch_q_2x;
} AhiruFadecCtx;

void ahiru_fadec_init(AhiruFadecCtx *ctx);
void ahiru_biquad_set_notch(BiquadFilter *f, float fs_hz, float f0_hz, float q_factor);
float ahiru_biquad_step(BiquadFilter *f, float x);
void ahiru_fadec_step_1khz(AhiruFadecCtx *ctx, const AhiruSensorBus *in, AhiruActuatorCmd *out);

#ifdef __cplusplus
}
#endif

#endif /* AHIRU_FADEC_REV3_H */
