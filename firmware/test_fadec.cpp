#include "ahiru_fadec.hpp"
#include <cassert>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <limits>

int main() {
  using namespace ahiru;
  FadecController ctrl;
  SensorFrame s{};
  s.quat_wb[0] = 1.0f;
  s.v_bus_v = 12.6f;
  s.fuel_frac = 1.0f;
  s.target_alt_m = 1.5f;

  // 1. Nominal start -> crank -> ignition -> ramp -> flight -> cooldown
  ctrl.command_start();
  auto c = ctrl.step(s, 0.0025f);
  assert(c.state == EngineState::PRECHECK);

  for (int i = 0; i < 120; ++i) c = ctrl.step(s, 0.0025f);
  assert(c.state == EngineState::CRANKING);

  s.rotor_rpm = 42000.0f;
  c = ctrl.step(s, 0.0025f);
  assert(c.state == EngineState::IGNITION);

  s.egt_c = 560.0f;
  s.rotor_rpm = 60000.0f;
  c = ctrl.step(s, 0.0025f);
  assert(c.state == EngineState::RAMP_IDLE);

  s.rotor_rpm = 122000.0f;
  c = ctrl.step(s, 0.0025f);
  assert(c.state == EngineState::RUN_FLIGHT);

  // 2. Measure 400 Hz WCET across 100,000 iterations
  s.rotor_rpm = 195000.0f;
  s.egt_c = 790.0f;
  s.baro_alt_m = 1.42f;
  s.quat_wb[0] = 0.999f;
  s.quat_wb[3] = 0.044f;

  double max_us = 0.0;
  double sum_us = 0.0;
  constexpr int N = 100000;
  for (int i = 0; i < N; ++i) {
    auto t0 = std::chrono::high_resolution_clock::now();
    c = ctrl.step(s, 0.0025f);
    auto t1 = std::chrono::high_resolution_clock::now();
    double us = std::chrono::duration<double, std::micro>(t1 - t0).count();
    if (us > max_us) max_us = us;
    sum_us += us;
    assert(std::fabs(c.gimbal_pitch_rad) <= 0.262f);
    assert(c.fuel_pump_duty >= 0.0f && c.fuel_pump_duty <= 1.0f);
  }

  // 3. Safety interlocks: Over-EGT & NaN injection must immediately cut fuel
  s.egt_c = 910.0f;
  c = ctrl.step(s, 0.0025f);
  assert(c.state == EngineState::EMERGENCY_CUTOFF);
  assert(c.fuel_pump_duty == 0.0f);
  assert((c.fault_flags & FAULT_OVER_EGT) != 0u);

  ctrl.reset();
  s.egt_c = 600.0f;
  s.baro_alt_m = std::numeric_limits<float>::quiet_NaN();
  c = ctrl.step(s, 0.0025f);
  assert(c.state == EngineState::EMERGENCY_CUTOFF);
  assert((c.fault_flags & FAULT_SENSOR_NAN) != 0u);

  // 4. Cooldown sequence test
  ctrl.reset();
  s.baro_alt_m = 0.0f;
  ctrl.command_start();
  c = ctrl.step(s, 0.0025f);
  assert(c.state == EngineState::PRECHECK);
  assert(ctrl.state() == EngineState::PRECHECK);
  assert(ctrl.fault_flags() == FAULT_NONE);
  ctrl.command_stop();
  c = ctrl.step(s, 0.0025f);
  assert(c.state == EngineState::COOLDOWN);
  s.egt_c = 110.0f;
  s.rotor_rpm = 1200.0f;
  c = ctrl.step(s, 0.0025f);
  assert(c.state == EngineState::OFF);

  std::printf("FADEC_SIL_PASS mean_us=%.4f max_us=%.4f\n", sum_us / N, max_us);
  return 0;
}
