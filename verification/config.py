"""
Physical constants, aerospace material database, part-to-material mapping,
README claimed specifications, and NVIDIA A100 GPU accelerator helper.
"""
from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from typing import Dict, Any, Tuple

# Physical Constants
G0 = 9.80665            # Standard gravity [m/s^2]
R_AIR = 287.058         # Specific gas constant of air [J/(kg*K)]
GAMMA_AIR = 1.40        # Ratio of specific heats (cold air)
GAMMA_GAS = 1.33        # Ratio of specific heats (hot combustion gas)
CP_AIR = 1004.5         # Specific heat of cold air [J/(kg*K)]
CP_GAS = 1150.0         # Specific heat of hot gas [J/(kg*K)]
SIGMA_SB = 5.670374e-8  # Stefan-Boltzmann constant [W/(m^2*K^4)]
T_AMB = 288.15          # ISA sea-level temperature [K] (15 C)
P_AMB = 101325.0        # ISA sea-level pressure [Pa]
RHO_AIR = 1.225         # ISA sea-level air density [kg/m^3]
MU_0 = 4.0 * 3.141592653589793e-7   # Vacuum permeability [H/m]
EPS_0 = 8.8541878128e-12            # Vacuum permittivity [F/m]
C0 = 299792458.0                    # Speed of light [m/s]

# Claimed Design Specifications from README.md & index.html (Rev.3 Flight-Qualified & Manufacturing Release)
DESIGN_SPEC: Dict[str, Any] = {
    "name": "RikiGaku-AHIRU Rev.3 (AHIRU-μTJ42V Flight-Qualified)",
    "envelope_mm": (180.0, 200.0, 100.0),      # (X length, Y height, Z width)
    "engine_axis_x_mm": -2.0,
    "claimed_dry_mass_g": 468.0,
    "claimed_wet_mass_g": 579.4,
    "claimed_fuel_vol_ml": 139.5,
    "claimed_fuel_mass_g": 111.6,
    "claimed_weight_N": 5.68,
    "claimed_max_thrust_N": 13.14,
    "claimed_twr": 2.31,
    "claimed_hover_throttle_pct": 46.5,
    "claimed_hover_endurance_min": 5.2,
    # Rev.2 Operating point targets for 38mm-impeller vertical reverse-flow micro-turbojet
    "design_rpm_max": 201000.0,                # Continuous rated max for PR>=2.80, DN<=1.71M, SF>=1.7, SPL@7m<=98 dB
    "design_rpm_idle": 68000.0,
    "design_rpm_ignition": 32000.0,
    "design_pr_compressor": 2.82,
    "design_tit_max_K": 1050.0,                # Bleed-cooled Inconel 718 blisk continuous target (<=1220 K)
    "design_gimbal_max_deg": 14.0,             # ±14 deg 2-axis thrust vectoring
    "jet_a1_lhv_J_kg": 43.15e6,                # Jet-A1 Lower Heating Value [J/kg]
    "jet_a1_density_kg_m3": 800.0,
    "jet_a1_flash_point_C": 38.0,
    "jet_a1_boil_initial_C": 150.0,
    "jet_a1_autoignition_C": 210.0,
    "battery_cells_s": 3,
    "battery_v_nom": 11.4,                     # 3S LiHV nominal (3.8 V/cell)
    "battery_v_max": 13.05,                    # 3S LiHV full (4.35 V/cell)
    "battery_v_min": 9.9,                      # 3S LiHV cutoff (3.3 V/cell)
    "battery_cap_mah": 780.0,
    "battery_max_safe_temp_C": 60.0,
    "battery_runaway_temp_C": 130.0,
}


@dataclass(frozen=True)
class MaterialProps:
    name: str
    density: float          # kg/m^3
    E_GPa: float            # Young's modulus [GPa]
    nu: float               # Poisson's ratio
    yield_MPa: float        # Yield strength at room temp [MPa]
    uts_MPa: float          # Ultimate tensile strength [MPa]
    k_W_mK: float           # Thermal conductivity [W/(m*K)]
    cp_J_kgK: float         # Specific heat [J/(kg*K)]
    cte_1e6_K: float        # Linear CTE [1e-6 / K]
    max_temp_C: float       # Max continuous service temp [C]
    emissivity: float       # Surface thermal emissivity
    K_IC_MPa_sqrtm: float   # Fracture toughness [MPa*sqrt(m)]
    endurance_MPa: float    # HCF endurance limit at 1e7 cycles [MPa]


MATERIALS: Dict[str, MaterialProps] = {
    "PEEK_CFRP": MaterialProps(
        "PEEK-CF30 Aerospace Composite", 1420.0, 22.0, 0.36, 175.0, 210.0,
        0.92, 1150.0, 22.0, 240.0, 0.85, 5.5, 85.0
    ),
    "AL7075_T6": MaterialProps(
        "Al 7075-T6 Anodized", 2810.0, 71.7, 0.33, 503.0, 572.0,
        130.0, 960.0, 23.6, 150.0, 0.77, 29.0, 159.0
    ),
    "TI6AL4V": MaterialProps(
        "Ti-6Al-4V Grade 5", 4430.0, 113.8, 0.342, 880.0, 950.0,
        6.7, 526.0, 8.6, 400.0, 0.35, 75.0, 450.0
    ),
    "INCONEL718": MaterialProps(
        "Inconel 718 (AMS 5662 / SLM)", 8190.0, 200.0, 0.29, 1035.0, 1240.0,
        11.4, 435.0, 13.0, 980.0, 0.65, 96.0, 420.0
    ),
    "SI3N4": MaterialProps(
        "Si3N4 Silicon Nitride Ceramic", 3210.0, 310.0, 0.27, 650.0, 700.0,
        30.0, 710.0, 3.2, 1200.0, 0.80, 6.1, 380.0
    ),
    "BEARING_STEEL": MaterialProps(
        "AISI 440C / M50 Bearing Steel", 7800.0, 204.0, 0.29, 1850.0, 1960.0,
        24.2, 460.0, 10.2, 315.0, 0.25, 22.0, 780.0
    ),
    "AEROGEL_CERAMIC": MaterialProps(
        "Silica Aerogel Ceramic Blanket", 200.0, 0.08, 0.20, 1.5, 2.0,
        0.022, 950.0, 2.0, 1050.0, 0.88, 0.3, 0.5
    ),
    "GOLD_FOIL": MaterialProps(
        "Gold-Plated Thermal Radiation Liner", 8900.0, 120.0, 0.34, 210.0, 310.0,
        310.0, 385.0, 14.2, 850.0, 0.035, 45.0, 90.0
    ),
    "ZRO2_CERAMIC": MaterialProps(
        "YSZ ZrO2 Thermal Barrier Ceramic", 5680.0, 210.0, 0.30, 500.0, 700.0,
        2.2, 460.0, 10.5, 1350.0, 0.72, 8.5, 280.0
    ),
    "COPPER": MaterialProps(
        "C11000 Oxygen-Free Copper", 8960.0, 117.0, 0.34, 210.0, 260.0,
        398.0, 385.0, 16.5, 260.0, 0.15, 65.0, 90.0
    ),
    "BRASS": MaterialProps(
        "C36000 Free-Machining Brass", 8500.0, 97.0, 0.31, 310.0, 400.0,
        115.0, 380.0, 20.5, 220.0, 0.22, 45.0, 140.0
    ),
    "FR4_PCB": MaterialProps(
        "FR-4 High-Tg PCB + SMD Stack", 2150.0, 24.0, 0.15, 280.0, 310.0,
        0.45, 1100.0, 14.0, 170.0, 0.88, 4.0, 90.0
    ),
    "LIHV_CELL": MaterialProps(
        "3S LiHV Pouch Cell Pack", 2250.0, 1.5, 0.30, 25.0, 35.0,
        1.8, 1050.0, 45.0, 60.0, 0.85, 1.5, 10.0
    ),
    "JET_A1": MaterialProps(
        "Jet-A1 Aviation Kerosene", 800.0, 0.001, 0.499, 0.0, 0.0,
        0.13, 2010.0, 950.0, 150.0, 0.92, 0.0, 0.0
    ),
    "NYLON_FUEL_TANK": MaterialProps(
        "PA12 / Fluoroelastomer Fuel Tank", 1050.0, 1.9, 0.39, 48.0, 55.0,
        0.24, 1700.0, 95.0, 125.0, 0.90, 3.5, 22.0
    ),
    "GLASS_OPTICS": MaterialProps(
        "Sapphire / BK7 ToF Optical Lens", 3980.0, 345.0, 0.28, 300.0, 400.0,
        35.0, 760.0, 5.5, 450.0, 0.85, 2.5, 120.0
    ),
    "SORBOTHANE_50D": MaterialProps(
        "Sorbothane 50D Viscoelastic IMU Isolator", 1360.0, 0.0025, 0.49, 1.8, 3.2,
        0.18, 1600.0, 180.0, 93.0, 0.92, 0.2, 1.0
    ),
}

# Mapping of all 61 CAD parts extracted from index.html (Rev.3 Flight-Qualification) to aerospace materials
PART_MATERIALS: Dict[str, str] = {
    "shellR": "PEEK_CFRP",
    "shellL": "PEEK_CFRP",
    "beak": "PEEK_CFRP",
    "pitot": "TI6AL4V",
    "wingR": "PEEK_CFRP",
    "wingL": "PEEK_CFRP",
    "flapR": "PEEK_CFRP",
    "flapL": "PEEK_CFRP",
    "tailVane": "PEEK_CFRP",
    "bellyShield": "ZRO2_CERAMIC",
    "footR": "PEEK_CFRP",
    "footL": "PEEK_CFRP",
    "struts": "TI6AL4V",
    "frame": "AL7075_T6",
    "thermalIsolators": "ZRO2_CERAMIC",
    "intakes": "PEEK_CFRP",
    "starterHousing": "AL7075_T6",
    "starterCoils": "COPPER",
    "bellmouth": "AL7075_T6",
    "compressor": "TI6AL4V",
    "diffuser": "AL7075_T6",
    "bearingTopRaces": "BEARING_STEEL",
    "bearingTopBalls": "SI3N4",
    "shaft": "INCONEL718",
    "combustor": "INCONEL718",
    "vaporizers": "INCONEL718",
    "shroudR": "AEROGEL_CERAMIC",
    "goldLinerR": "GOLD_FOIL",
    "shroudL": "AEROGEL_CERAMIC",
    "goldLinerL": "GOLD_FOIL",
    "thermalBaffle": "ZRO2_CERAMIC",
    "bearingBotRaces": "BEARING_STEEL",
    "bearingBotBalls": "SI3N4",
    "ngv": "INCONEL718",
    "containmentRing": "INCONEL718",
    "turbine": "INCONEL718",
    "tailcone": "INCONEL718",
    "engineFlanges": "INCONEL718",
    "gimbal": "TI6AL4V",
    "nozzle": "INCONEL718",
    "servos": "AL7075_T6",
    "servoRodR": "TI6AL4V",
    "servoRodL": "TI6AL4V",
    "rcs": "TI6AL4V",
    "fuelPump": "AL7075_T6",
    "pumpGear1": "BRASS",
    "pumpGear2": "BRASS",
    "fuelLines": "COPPER",
    "lubeLines": "TI6AL4V",
    "fuelBaffles": "NYLON_FUEL_TANK",
    "imuMount": "SORBOTHANE_50D",
    "fadecPCB": "FR4_PCB",
    "fadecGold": "COPPER",
    "fadecChips": "FR4_PCB",
    "eyes": "GLASS_OPTICS",
    "eyeBezels": "AL7075_T6",
    "battery": "LIHV_CELL",
    "batteryBus": "COPPER",
    "plasma": "JET_A1",          # Visual plasma mesh (excluded from mass)
    "fuelLiquid": "JET_A1",
    "fuelTank": "NYLON_FUEL_TANK",
}


def detect_compute_environment() -> Dict[str, Any]:
    """Detect NVIDIA A100/GPU availability, CUDA version, and installed native CLI engines."""
    info: Dict[str, Any] = {
        "device": "cpu",
        "gpu_name": None,
        "gpu_vram_gb": 0.0,
        "cuda_available": False,
        "torch_available": False,
        "cpu_count": os.cpu_count() or 1,
        "native_tools": {},
        "python_solvers": {},
    }
    try:
        import torch
        info["torch_available"] = True
        if torch.cuda.is_available():
            info["cuda_available"] = True
            info["device"] = "cuda"
            props = torch.cuda.get_device_properties(0)
            info["gpu_name"] = props.name
            info["gpu_vram_gb"] = round(props.total_memory / (1024 ** 3), 2)
    except Exception:
        pass

    for tool_name, binary in [
        ("node", "node"),
        ("calculix_ccx", "ccx"),
        ("gmsh", "gmsh"),
        ("ngspice", "ngspice"),
        ("kicad_cli", "kicad-cli"),
        ("openfoam_simple", "rhoSimpleFoam"),
        ("xfoil", "xfoil"),
        ("openscad", "openscad"),
        ("cppcheck", "cppcheck"),
        ("clang", "clang"),
        ("gcc", "gcc"),
        ("spin", "spin"),
        ("scram", "scram"),
    ]:
        info["native_tools"][tool_name] = shutil.which(binary)

    for mod_name in [
        "numpy", "scipy", "matplotlib", "torch", "trimesh", "fcl", "cadquery",
        "cantera", "ross", "mujoco", "control", "casadi", "z3",
    ]:
        try:
            __import__(mod_name)
            info["python_solvers"][mod_name] = True
        except Exception:
            info["python_solvers"][mod_name] = False

    return info
