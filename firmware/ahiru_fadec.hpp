#pragma once

#include <cstdint>

namespace ahiru {

enum class EngineState : uint8_t {
  OFF = 0,
  PRECHECK = 1,
  CRANKING = 2,
  IGNITION = 3,
  RAMP_IDLE = 4,
  RUN_FLIGHT = 5,
  COOLDOWN = 6,
  EMERGENCY_CUTOFF = 7
};

struct SensorFrame {
  float gyro_rad_s[3];     // Body angular rate [p, q, r]
  float accel_m_s2[3];     // Specific force [ax, ay, az]
  float quat_wb[4];        // Attitude quaternion [w, x, y, z]
  float baro_alt_m;        // Barometric + ToF altitude [m]
  float pitot_airspeed_ms; // Airspeed from beak Pitot probe [m/s]
  float rotor_rpm;         // Optical/Hall tach RPM
  float egt_c;             // Exhaust Gas Temp [deg C]
  float v_bus_v;           // 3S LiHV bus voltage [V]
  float i_bus_a;           // Bus current [A]
  float fuel_frac;         // Remaining fuel fraction [0..1]
  float target_alt_m;      // Commanded hover/flight altitude [m]
  float target_pitch_rad;  // Commanded cruise pitch [rad]
  float target_yaw_rate;   // Commanded yaw rate [rad/s]
  uint32_t timestamp_us;
};

struct ActuatorCommand {
  float fuel_pump_duty;    // [0.0 .. 1.0]
  float starter_duty;      // [-1.0 .. 1.0] (positive=motor crank, negative=regen)
  float igniter_duty;      // [0.0 .. 1.0]
  float gimbal_pitch_rad;  // [-0.2618 .. +0.2618] (+/- 15 deg)
  float gimbal_roll_rad;   // [-0.2618 .. +0.2618] (+/- 15 deg)
  float rcs_yaw_valve;     // [-1.0 .. 1.0]
  float flaperon_rad[2];   // [left, right] [-0.35 .. +0.35]
  float tail_elev_rad;     // [-0.35 .. +0.35]
  EngineState state;
  uint32_t fault_flags;
};

constexpr uint32_t FAULT_NONE        = 0u;
constexpr uint32_t FAULT_OVER_EGT    = 1u << 0;
constexpr uint32_t FAULT_OVER_RPM    = 1u << 1;
constexpr uint32_t FAULT_LOW_VBAT    = 1u << 2;
constexpr uint32_t FAULT_FLAMEOUT    = 1u << 3;
constexpr uint32_t FAULT_ATT_EXCESS  = 1u << 4;
constexpr uint32_t FAULT_SENSOR_NAN  = 1u << 5;

class FadecController {
public:
  FadecController() noexcept;

  void reset() noexcept;
  void command_start() noexcept;
  void command_stop() noexcept;

  // Deterministic 400 Hz control step (dt = 0.0025 s), zero dynamic allocation
  ActuatorCommand step(const SensorFrame& s, float dt_s) noexcept;

  EngineState state() const noexcept { return state_; }
  uint32_t fault_flags() const noexcept { return fault_flags_; }

private:
  EngineState state_;
  uint32_t fault_flags_;
  float state_timer_s_;
  float alt_integral_;
  float pitch_integral_;
  float roll_integral_;
  float yaw_integral_;
  float prev_alt_m_;
  float prev_rpm_;
  bool start_req_;
  bool stop_req_;

  static float clampf(float v, float lo, float hi) noexcept;
  static bool is_finite_frame(const SensorFrame& s) noexcept;
};

} // namespace ahiru
