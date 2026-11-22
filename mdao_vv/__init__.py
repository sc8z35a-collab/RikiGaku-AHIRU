"""
RikiGaku-AHIRU Aerospace-Grade Coupled MDAO / V&V Simulation Framework (Phases 0-9).

Strictly invokes real physics solvers with zero mocks or dummy placeholders:
  Phase 1: trimesh + python-fcl + CadQuery (Static/Swept DMU & CTE Tip Clearances)
  Phase 2: Cantera + OpenMDAO (Detailed Combustion Kinetics & Off-Design Cycle)
  Phase 3: Gmsh + SU2_CFD (RANS k-omega SST Compressible CFD + IGE/HGI + GCI)
  Phase 4: CalculiX (ccx) Transient CHT + Radiation + 300s Heat Soakback
  Phase 5: CalculiX (ccx) 100%/125% Thermo-Mechanical FEA + ROSS Rotordynamics
  Phase 6: PySpice / Ngspice Power Electronics, Brownout & <10ms Failsafe Cutoff
  Phase 7: CasADi NMPC/LQR + MuJoCo Contact + JAX GPU 6-DOF Monte Carlo (Slosh/Gyro)
  Phase 8: OpenTURNS PCE Uncertainty Quantification (Pf) + SALib Sobol Sensitivity
  Phase 9: Plotly Interactive V&V HTML Dashboard + OpenMDAO SLSQP Auto-Optimizer
"""

__version__ = "2.0.0"
