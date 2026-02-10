# constants.py
"""
Physical constants used throughout the synchrotron simulation.

All values are in SI units (meters, kilograms, seconds, Coulombs).
Reference: CODATA 2018 recommended values (NIST).
"""

# Speed of light in vacuum (m/s)
C: float = 299_792_458.0

# Proton rest mass (kg)
PROTON_MASS: float = 1.67262192369e-27

# Elementary charge / proton charge (Coulombs)
PROTON_CHARGE: float = 1.602176634e-19

# Electron-volt to Joules conversion factor
EV_TO_JOULES: float = 1.602176634e-19