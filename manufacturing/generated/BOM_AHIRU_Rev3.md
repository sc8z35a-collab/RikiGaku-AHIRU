# RikiGaku-AHIRU Rev.3 — Production Bill of Materials (BOM)

- **Dry Mass Roll-Up**: `487.8 g` (+ `111.6 g` Jet-A1 / 5% AeroShell 500 oil = **`599.4 g`** MTOW)
- **Single-Unit Aerospace Prototype Cost (One-Off CNC/DMLS)**: **`$13,467`**
- **10-Unit Small-Batch Unit Cost**: **`$4,496`**
- **COTS Engine Fallback Option**: For rapid 1st-flight prototyping without custom Ø38mm DMLS turbine tooling, scale airframe 1.25× and drop in a certified COTS micro-turbine (`JetCat P20-SX` / `KingTech K30G` / `Xicoy X45`, ~$2,200–$2,600 complete with ECU/pump).

| # | Part No | Subsystem | Component | Spec / COTS P/N | Material | Qty | Mass (g) | Proto ($) |
|---|---|---|---|---|---|---:|---:|---:|
| 01 | `AHIRU-R3-001` | Propulsion | 6+6 Splitter Centrifugal Compressor Impeller | Ø38.0mm, Ø5.000 H6 bore, G0.4 collar | Ti-6Al-4V Gr.5 | 1 | 6.4 | $950 |
| 02 | `AHIRU-R3-002` | Propulsion | 17-Blade Tapered Bleed-Cooled Turbine Blisk | Ø36.4mm, Ø4.000 H6 bore, G0.4 boss | Inconel 718 | 1 | 5.8 | $1,650 |
| 03 | `AHIRU-R3-003` | Propulsion | High-Stiffness Rotor Main Shaft | Ø5.000 h5 journals, Ra 0.2, TIR<=2um | Inconel 718 | 1 | 10.0 | $480 |
| 04 | `AHIRU-R3-004` | Propulsion | 15-Vane Diffuser & Integral Bearing Tunnel | Ø11.000 H6, AS568-013 grooves, lube ports | Al 7075-T651 | 1 | 18.5 | $820 |
| 05 | `AHIRU-R3-005` | Propulsion | Reverse-Flow Annular Combustor + 12 Vaporizers | 0.8mm wall, 36 film/dilution jets | Inconel 718 | 1 | 21.4 | $1,100 |
| 06 | `AHIRU-R3-006` | Propulsion | 12-Vane Turbine Stator NGV + Tailcone | 12 vanes (coprime to 17 blades) | Inconel 718 | 1 | 15.2 | $850 |
| 07 | `AHIRU-R3-007` | Propulsion | 360° Blade Containment Ring + A286 Flange | 2.05mm wall, 6x M2.5 A286 + Belleville | Inconel 718 / A286 | 1 | 17.6 | $540 |
| 08 | `AHIRU-R3-008` | Propulsion | Hybrid Ceramic Angular-Contact Bearings | GRW 685-2Z-CE Si3N4 (Ø5xØ11x4, ABEC-7) | 440C / Si3N4 | 2 | 3.0 | $240 |
| 09 | `AHIRU-R3-009` | Propulsion | Squeeze-Film Damper O-Rings | AS568-013 FKM Viton 60A (k=0.65 MN/m) | FKM Viton 60A | 2 | 0.4 | $12 |
| 10 | `AHIRU-R3-010` | Lubrication | Metered Oil-Mist Restrictors & Capillary Lines | Lee IEPA1211241H / Ø0.25mm Ruby Orifice | Ti-6Al-4V / Ruby | 2 | 2.8 | $190 |
| 11 | `AHIRU-R3-011` | Thermal | Silica Aerogel Shroud + Gold Liner + ZrO2 Firewall | ε=0.035 Au foil + 2mm ZrO2 isolators | Aerogel/Au/YSZ | 1 | 22.8 | $420 |
| 12 | `AHIRU-R3-012` | Starter-Gen | Celeroton-Class Direct-Coupled Starter-Generator | 2-Pole SmCo28 + 0.35mm IN718 sleeve, Kv=7.8k, 0.1mm NO10 | SmCo28/IN718/NO10 | 1 | 19.4 | $1,450 |
| 13 | `AHIRU-R3-013` | TVC/RCS | Choked Chevron De Laval Nozzle & Ti Gimbal | r_t=7.4, r_e=8.6, 12 chevrons, ±14° | Inconel 718 / Ti | 1 | 27.5 | $920 |
| 14 | `AHIRU-R3-014` | TVC/RCS | High-Speed Metal-Gear HV TVC Servos + Ti Linkages | KST X08H Plus (2.8 kg·cm @ 8.4V, 0.07s) | Al / Steel / Ti | 2 | 18.4 | $130 |
| 15 | `AHIRU-R3-015` | TVC/RCS | Bleed-Air Proportional Yaw RCS Valves & Nozzles | Lee LHDA0523111H micro-solenoid + Ti tubes | Ti-6Al-4V | 2 | 10.2 | $280 |
| 16 | `AHIRU-R3-016` | Fuel | 290° Conformal Saddle Tank + 3 Baffles + UAT | 139.5 mL, Fluoroelastomer-lined PA12 | PA12 / FKM | 1 | 31.6 | $340 |
| 17 | `AHIRU-R3-017` | Fuel | Brushless Micro Gear Fuel Pump + Si3N4 Igniter | Flightworks 200-series / AGMA brass gears + 11V glow | Al / Brass / Si3N4 | 1 | 26.8 | $290 |
| 18 | `AHIRU-R3-018` | Airframe | Duck CFRP Shell, S-Duct Intakes, Wings & Belly | PEEK-CF30 1.25mm + ZrO2 belly shield | PEEK-CF30 / YSZ | 1 | 108.5 | $1,350 |
| 19 | `AHIRU-R3-019` | Airframe | Al 7075-T6 Internal Frame & 26.8mm Oleo-Ti Struts | k=2395 N/m, c=31 Ns/m, 15.6mm stroke | Al 7075 / Ti-6Al-4V | 1 | 41.2 | $760 |
| 20 | `AHIRU-R3-020` | Avionics | 4-Layer STM32H743 FADEC + 60V FOC + Dual IMU PCBA | STM32H743, 2x ICM-42688-P, DRV8353RS, 6x BSC028N06 | FR-4 High-Tg 2oz | 1 | 11.4 | $380 |
| 21 | `AHIRU-R3-021` | Avionics | Sorbothane 50D IMU Isolation Mount + Optical Eyes | f_n=38 Hz grommets + VL53L4CD ToF + K-Type EGT | Sorbothane / Glass | 1 | 5.2 | $110 |
| 22 | `AHIRU-R3-022` | Power | Split-Balanced 3S 750 mAh 60C LiHV Battery Pack | 2x Chest + 1x Tail cell (Custom Spot-Welded Pack) | LiHV Pouch 4.35V | 1 | 49.5 | $85 |
| 23 | `AHIRU-R3-023` | Fasteners | Harnesses, Silicone/PTFE Wire, XT30, Hardware | AWG14 Silicone + PTFE Coax + Ti M2/M2.5 | Cu / PTFE / Ti | 1 | 14.2 | $120 |
