# RikiGaku-AHIRU Rev.3 — Manufacturing, Balancing, Test-Bench & Flight-Qualification Manual

## 1. Metrology & Shop-Floor Acceptance Gates (Before Assembly)
1. **Inconel 718 Shaft (`AHIRU-R3-003`)**: CMM inspect journals to `Ø5.000 +0.000/-0.005 mm (h5)`, `Ra <= 0.2 µm`, Total Indicated Runout `TIR <= 2 µm` between front and rear bearing seats.
2. **Diffuser Bearing Tunnel (`AHIRU-R3-004`)**: Air-gauge bore `Ø11.000 +0.011/-0.000 mm (H6)`, coaxiality `<= 5 µm`, verify AS568-013 Viton 60A O-ring groove depth (`14%` radial squeeze). Pressure-test dual `Ø0.25 mm` ruby lube restrictors with filtered Jet-A1 @ `1.8 bar` (`0.12 ± 0.01 mL/min` each).
3. **2-Plane Dynamic Rotor Balancing (ISO 1940 G0.4)**:
   - Balance shaft + compressor + turbine + SmCo28/IN718 starter sleeve **as a mated rotating assembly** on a Schenck / Hofmann high-speed micro-balancer.
   - Remove trim mass ONLY from the designated front compressor balance collar (`AHIRU-R3-001`) and rear turbine balance boss (`AHIRU-R3-002`).
   - **Acceptance**: Residual unbalance `<= 0.22 mg·mm` (`0.00022 g·mm`) per plane (`ISO 1940 G0.4` at `201,000 RPM`, `<= 0.55 mg·mm` for `G1.0` after reassembly). Mark angular phasing across shaft/impeller/turbine before teardown and re-torque M4 locking nuts with high-temp nickel anti-seize.
4. **Pre-Flight 3-Point Load-Cell CoG Verification**: Verify dry and full-fuel (`139.5 mL`) lateral/longitudinal CoG within `±2.5 mm` of thrust axis (`X = -2.0 mm, Z = 0.0 mm`) prior to arming (adjust split tail LiHV cell shim if required).

## 2. Engine Hot-Fire Test-Bench Qualification Protocol (Outdoor Blast-Shielded Cell)
- **Safety Gear Mandatory**: Double hearing protection (`114.3 dB @ 1 m`), Class B CO₂ fire extinguisher (never water/powder into turbine!), polycarbonate blast shield, remote `E-STOP` fuel solenoid kill switch.
- **Fuel Mix**: Filtered (`5 µm`) Jet-A1 or Kerosene + **5.0% AeroShell Turbine Oil 500** (critical for GRW 685 ceramic bearing mist lubrication!).
- **Gate B1 — Cold Spin & Lube Verification**: Spin with 60V FOC starter to `35,000 RPM` (`I <= 28 A`, `V_bus >= 9.5 V`), confirm bearing mist discharge at exhaust tailcone and zero rubbing noise.
- **Gate B2 — Staged Ignition & Wet-Start Guard**: Execute FADEC `PREHEAT (6 A, 4 s) -> CRANK_IGNITE (28 A FOC + 3 A PWM glow)`. Verify light-off EGT rises `>= 120 °C` within `3.5 s` (auto-abort if EGT `> 850 °C` or no light-off).
- **Gate B3 — Idle to 201,000 RPM Map & Vibration Sweep**: Step throttle `68k -> 100k -> 140k -> 180k -> 201k RPM` on load-cell thrust stand. Verify:
  - Peak thrust `>= 13.0 N` (`T_net`), EGT `<= 730 °C` continuous, bearing case temp `<= 115 °C`.
  - Confirm `0.1 mm` NO10 stator core cooling and `60V` FOC active rectifier charging (`+18 W` net into 3S LiHV, `V_emf = 25.8 V`).
  - Record accelerometer FFT to confirm zero sub-synchronous whirl and `< 0.5 mm/s` RMS casing vibration.
- **Gate B4 — 300 s Post-Shutdown Soakback**: Cut fuel from full power; log chest LiHV temperature for `300 s` (must stay `<= 50 °C`).

## 3. Tethered 3-DOF Gimbal Rig System Identification (SysID) & Flight Envelope Expansion
- **Gate F1 — IMU Vibration Isolation Verification**: Mount live FADEC (`AHIRU-R3-020`) on Sorbothane 50D grommets (`AHIRU-R3-021`). Run engine at `68k..201k RPM` and verify dual `ICM-42688-P` raw gyro noise `< 0.08 deg/s RMS` after adaptive RPM-tracked 1X/2X biquad notch filter.
- **Gate F2 — Tethered Chirp SysID**: Suspend aircraft on a 3-axis safety tether (`0.5 m` slack). Inject FADEC built-in `0.5–25 Hz` logarithmic chirp into pitch/roll TVC and throttle. Verify identified closed-loop `GM >= 6 dB`, `PM >= 45°`, and spool-lag lead compensation bandwidth `>= 1.8 Hz`.
- **Gate F3 — Ground-Effect HGI Check (`H = 5, 15, 30 cm`)**: Measure intake duct thermocouple during hover over concrete in `0–5 m/s` wind (`ΔT_HGI <= 20 K`, zero compressor surge).
- **Gate F4 — Free Hover & Transition**: Perform `30 s` hover at `H = 1.5 m` over fireproof pad → lateral step maneuvers → `8 m/s` forward cruise transition → vertical touchdown (`v_z <= 0.5 m/s`).

## 4. Legal & Regulatory Compliance Checklist (Japan / International)
- **Civil Aeronautics Act (航空法 / MLIT DIPS 2.0)**: Unmanned aircraft `>= 100 g` (`579 g` MTOW) requires **Airframe Registration + Remote ID** and specific flight category approval (Level II/III or private test-range waiver; avoid DID/airports/night/BVLOS without permit).
- **Fire Service Act (消防法)**: Jet-A1 / kerosene is Class 4 Category 2 Petroleum (`第4類第2石油類`); store `< 200 L` in UN-certified metal safety cans with secondary containment and CO₂ extinguisher on site.
- **Noise Compliance**: `97.4 dB @ 7 m` meets RC jet field limits (`<= 98 dB`), operate only at approved turbine flying sites or acoustic-buffered test cells.
