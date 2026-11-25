#include "ahiru_fadec.hpp"
#include <cmath>

namespace ahiru {

namespace {
constexpr float kMaxGimbalRad = 0.26179939f; // 15 deg
constexpr float kMaxAeroRad   = 0.34906585f; // 20 deg
constexpr float kMaxRpm       = 255000.0f;
constexpr float kMaxEgtC      = 890.0f;
constexpr float kMinSafeVolt  = 9.6f;
constexpr float kMaxTiltRad   = 0.95993109f; // 55 deg safety abort
} // namespace

FadecController::FadecController() noexcept
    : state_(EngineState::OFF),
      fault_flags_(FAULT_NONE),
      state_timer_s_(0.0f),
      alt_integral_(0.0f),
      pitch_integral_(0.0f),
      roll_integral_(0.0f),
      yaw_integral_(0.0f),
      prev_alt_m_(0.0f),
      prev_rpm_(0.0f),
      start_req_(false),
      stop_req_(false) {}

void FadecController::reset() noexcept {
  state_ = EngineState::OFF;
  fault_flags_ = FAULT_NONE;
  state_timer_s_ = 0.0f;
  alt_integral_ = 0.0f;
  pitch_integral_ = 0.0f;
  roll_integral_ = 0.0f;
  yaw_integral_ = 0.0f;
  prev_alt_m_ = 0.0f;
  prev_rpm_ = 0.0f;
  start_req_ = false;
  stop_req_ = false;
}

void FadecController::command_start() noexcept {
  start_req_ = true;
  stop_req_ = false;
}

void FadecController::command_stop() noexcept {
  stop_req_ = true;
  start_req_ = false;
}

float FadecController::clampf(float v, float lo, float hi) noexcept {
  return (v < lo) ? lo : ((v > hi) ? hi : v);
}

bool FadecController::is_finite_frame(const SensorFrame& s) noexcept {
  for (int i = 0; i < 3; ++i) {
    if (!std::isfinite(s.gyro_rad_s[i]) || !std::isfinite(s.accel_m_s2[i])) return false;
  }
  for (int i = 0; i < 4; ++i) {
    if (!std::isfinite(s.quat_wb[i])) return false;
  }
  return std::isfinite(s.baro_alt_m) && std::isfinite(s.pitot_airspeed_ms) &&
         std::isfinite(s.rotor_rpm) && std::isfinite(s.egt_c) &&
         std::isfinite(s.v_bus_v) && std::isfinite(s.i_bus_a) &&
         std::isfinite(s.fuel_frac) && std::isfinite(s.target_alt_m) &&
         std::isfinite(s.target_pitch_rad) && std::isfinite(s.target_yaw_rate);
}

ActuatorCommand FadecController::step(const SensorFrame& s, float dt_s) noexcept {
  ActuatorCommand cmd{};
  const float dt = clampf(dt_s, 0.0005f, 0.02f);

  if (!is_finite_frame(s)) {
    fault_flags_ |= FAULT_SENSOR_NAN;
    state_ = EngineState::EMERGENCY_CUTOFF;
  }

  // Quaternion -> Roll & Pitch (body frame: X forward, Y up, Z right)
  const float qw = s.quat_wb[0];
  const float qx = s.quat_wb[1];
  const float qy = s.quat_wb[2];
  const float qz = s.quat_wb[3];
  const float roll_rad  = std::atan2(2.0f * (qw * qx + qy * qz), 1.0f - 2.0f * (qx * qx + qy * qy));
  const float sin_p     = clampf(2.0f * (qw * qz - qx * qy), -1.0f, 1.0f);
  const float pitch_rad = std::asin(sin_p);

  // Hard real-time safety interlocks
  if (s.egt_c > kMaxEgtC) {
    fault_flags_ |= FAULT_OVER_EGT;
    state_ = EngineState::EMERGENCY_CUTOFF;
  }
  if (s.rotor_rpm > kMaxRpm) {
    fault_flags_ |= FAULT_OVER_RPM;
    state_ = EngineState::EMERGENCY_CUTOFF;
  }
  if (s.v_bus_v < kMinSafeVolt) {
    fault_flags_ |= FAULT_LOW_VBAT;
    state_ = EngineState::EMERGENCY_CUTOFF;
  }
  if ((state_ == EngineState::RUN_FLIGHT) && (std::fabs(roll_rad) > kMaxTiltRad || std::fabs(pitch_rad) > kMaxTiltRad)) {
    fault_flags_ |= FAULT_ATT_EXCESS;
    state_ = EngineState::EMERGENCY_CUTOFF;
  }
  if (stop_req_ && state_ != EngineState::OFF && state_ != EngineState::EMERGENCY_CUTOFF) {
    state_ = EngineState::COOLDOWN;
    state_timer_s_ = 0.0f;
  }

  state_timer_s_ += dt;

  switch (state_) {
    case EngineState::OFF: {
      if (start_req_ && s.v_bus_v >= 11.2f && s.fuel_frac > 0.08f) {
        state_ = EngineState::PRECHECK;
        state_timer_s_ = 0.0f;
      }
      break;
    }
    case EngineState::PRECHECK: {
      if (state_timer_s_ >= 0.25f) {
        state_ = EngineState::CRANKING;
        state_timer_s_ = 0.0f;
      }
      break;
    }
    case EngineState::CRANKING: {
      cmd.starter_duty = clampf(0.45f + (45000.0f - s.rotor_rpm) * 0.00002f, 0.2f, 0.9f);
      cmd.igniter_duty = 0.85f; // Pre-heat ceramic glow plug
      if (s.rotor_rpm >= 38000.0f) {
        state_ = EngineState::IGNITION;
        state_timer_s_ = 0.0f;
      } else if (state_timer_s_ > 6.0f) {
        fault_flags_ |= FAULT_FLAMEOUT;
        state_ = EngineState::EMERGENCY_CUTOFF;
      }
      break;
    }
    case EngineState::IGNITION: {
      cmd.starter_duty = 0.60f;
      cmd.igniter_duty = 1.0f;
      cmd.fuel_pump_duty = 0.14f;
      if (s.egt_c >= 420.0f && s.rotor_rpm >= 52000.0f) {
        state_ = EngineState::RAMP_IDLE;
        state_timer_s_ = 0.0f;
      } else if (state_timer_s_ > 4.5f) {
        fault_flags_ |= FAULT_FLAMEOUT;
        state_ = EngineState::EMERGENCY_CUTOFF;
      }
      break;
    }
    case EngineState::RAMP_IDLE: {
      const float rpm_err = 120000.0f - s.rotor_rpm;
      cmd.starter_duty = (s.rotor_rpm < 80000.0f) ? 0.35f : -0.15f; // Switch to regen
      cmd.igniter_duty = (s.rotor_rpm < 95000.0f) ? 0.4f : 0.0f;
      cmd.fuel_pump_duty = clampf(0.18f + rpm_err * 0.000003f, 0.14f, 0.48f);
      if (s.rotor_rpm >= 115000.0f) {
        state_ = EngineState::RUN_FLIGHT;
        state_timer_s_ = 0.0f;
      } else if (state_timer_s_ > 8.0f) {
        fault_flags_ |= FAULT_FLAMEOUT;
        state_ = EngineState::EMERGENCY_CUTOFF;
      }
      break;
    }
    case EngineState::RUN_FLIGHT: {
      // Flameout watchdog
      if (s.egt_c < 360.0f || s.rotor_rpm < 90000.0f) {
        fault_flags_ |= FAULT_FLAMEOUT;
        state_ = EngineState::EMERGENCY_CUTOFF;
        break;
      }
      // Altitude hold outer loop -> RPM/fuel inner loop
      const float vz = (s.baro_alt_m - prev_alt_m_) / dt;
      const float alt_err = clampf(s.target_alt_m - s.baro_alt_m, -2.0f, 2.0f);
      alt_integral_ = clampf(alt_integral_ + alt_err * dt, -1.5f, 1.5f);
      const float target_rpm = clampf(192000.0f + alt_err * 32000.0f + alt_integral_ * 14000.0f - vz * 22000.0f,
                                      120000.0f, 240000.0f);
      const float rpm_err = target_rpm - s.rotor_rpm;
      const float drpm = (s.rotor_rpm - prev_rpm_) / dt;
      cmd.fuel_pump_duty = clampf(0.51f + (target_rpm - 192000.0f) / 145000.0f + rpm_err * 0.0000045f - drpm * 0.0000003f,
                                  0.20f, 1.0f);
      cmd.starter_duty = -0.22f; // Continuous 15-25W alternator regen to recharge bus

      // 2-axis thrust-vectoring inverted pendulum stabilization (400 Hz)
      const float p_err = s.target_pitch_rad - pitch_rad;
      const float r_err = -roll_rad;
      pitch_integral_ = clampf(pitch_integral_ + p_err * dt, -0.25f, 0.25f);
      roll_integral_  = clampf(roll_integral_ + r_err * dt, -0.25f, 0.25f);

      const float g_pitch = -(p_err * 1.45f + pitch_integral_ * 0.35f - s.gyro_rad_s[2] * 0.28f);
      const float g_roll  = -(r_err * 1.45f + roll_integral_ * 0.35f - s.gyro_rad_s[0] * 0.28f);
      cmd.gimbal_pitch_rad = clampf(g_pitch, -kMaxGimbalRad, kMaxGimbalRad);
      cmd.gimbal_roll_rad  = clampf(g_roll, -kMaxGimbalRad, kMaxGimbalRad);

      // Yaw RCS cold-air bleed counter-torque + rate damping
      const float yaw_err = s.target_yaw_rate - s.gyro_rad_s[1];
      yaw_integral_ = clampf(yaw_integral_ + yaw_err * dt, -0.5f, 0.5f);
      cmd.rcs_yaw_valve = clampf(yaw_err * 0.65f + yaw_integral_ * 0.20f, -1.0f, 1.0f);

      // Coupled aerodynamic surfaces for forward cruise flight
      const float aero_gain = clampf(s.pitot_airspeed_ms / 12.0f, 0.0f, 1.0f);
      cmd.flaperon_rad[0] = clampf(aero_gain * (r_err * 0.6f - s.target_pitch_rad * 0.5f), -kMaxAeroRad, kMaxAeroRad);
      cmd.flaperon_rad[1] = clampf(aero_gain * (-r_err * 0.6f - s.target_pitch_rad * 0.5f), -kMaxAeroRad, kMaxAeroRad);
      cmd.tail_elev_rad   = clampf(aero_gain * (p_err * 0.8f), -kMaxAeroRad, kMaxAeroRad);
      break;
    }
    case EngineState::COOLDOWN: {
      cmd.fuel_pump_duty = 0.0f;
      cmd.starter_duty = (s.egt_c > 180.0f) ? 0.18f : 0.0f; // Dry motoring cool-down
      if (s.egt_c < 140.0f && s.rotor_rpm < 3000.0f) {
        state_ = EngineState::OFF;
        stop_req_ = false;
      }
      break;
    }
    case EngineState::EMERGENCY_CUTOFF: {
      cmd.fuel_pump_duty = 0.0f;
      cmd.igniter_duty = 0.0f;
      cmd.starter_duty = 0.0f;
      cmd.gimbal_pitch_rad = 0.0f;
      cmd.gimbal_roll_rad = 0.0f;
      cmd.rcs_yaw_valve = 0.0f;
      break;
    }
  }

  prev_alt_m_ = s.baro_alt_m;
  prev_rpm_ = s.rotor_rpm;
  cmd.state = state_;
  cmd.fault_flags = fault_flags_;
  return cmd;
}

} // namespace ahiru
