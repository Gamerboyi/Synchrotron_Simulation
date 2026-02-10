# particle.py
"""
Particle state representation for the synchrotron ring simulation.

Each Particle stores its phase-space coordinates (x, y, vx, vy),
charge, mass, and derived quantities (energy, momentum, Lorentz factor).
It also tracks revolution count and per-lap trail data for visualization.
"""

import numpy as np
from constants import C, EV_TO_JOULES


class Particle:
    """
    A charged particle in 2D phase space.

    Attributes:
        x, y        : position in meters (m)
        vx, vy      : velocity components in meters/second (m/s)
        q           : charge in Coulombs (C)
        m           : rest mass in kilograms (kg)
        alive       : whether the particle is still inside the ring aperture
        gamma       : Lorentz factor γ = 1/√(1 - v²/c²)
        energy_joules : kinetic energy in Joules (J)
        energy_ev   : kinetic energy in electron-volts (eV)
        px, py      : momentum components in kg·m/s
        p           : total momentum magnitude |p| in kg·m/s
        turns       : number of completed revolutions
    """

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        q: float,
        m: float,
        alive: bool = True,
    ) -> None:
        self.x: float = float(x)
        self.y: float = float(y)
        self.vx: float = float(vx)
        self.vy: float = float(vy)

        self.q: float = float(q)
        self.m: float = float(m)

        self.alive: bool = alive

        # Relativistic factor
        self.gamma: float = 1.0

        # Energy
        self.energy_joules: float = 0.0
        self.energy_ev: float = 0.0

        # Momentum (phase-space)
        self.px: float = 0.0
        self.py: float = 0.0
        self.p: float = 0.0  # magnitude

        # Revolution tracking
        self.theta_prev: float = 0.0
        self.theta_accum: float = 0.0
        self.turns: int = 0
        self.just_completed_lap: bool = False

        # Trails (two-lap system: current lap white, previous lap green)
        self.trail_current: list[tuple[float, float]] = []
        self.trail_prev: list[tuple[float, float]] = []
        self.trail_counter: int = 0
        self.trail_prev_alpha: int = 0

        # Hypnosis wipe angle for previous lap fade
        self.prev_lap_wipe_angle: float = 0.0

    def update_energy(self, relativistic: bool = False) -> None:
        """
        Recompute kinetic energy and momentum from current velocity.

        In non-relativistic mode:
            KE = ½mv²
            p  = mv

        In relativistic mode:
            KE = (γ - 1)mc²
            p  = γmv

        Args:
            relativistic: If True, use relativistic formulas.
        """
        v2: float = self.vx * self.vx + self.vy * self.vy

        if relativistic:
            self.energy_joules = (self.gamma - 1.0) * self.m * C * C
        else:
            self.energy_joules = 0.5 * self.m * v2

        self.energy_ev = self.energy_joules / EV_TO_JOULES

        if relativistic:
            self.px = self.gamma * self.m * self.vx
            self.py = self.gamma * self.m * self.vy
        else:
            self.px = self.m * self.vx
            self.py = self.m * self.vy

        self.p = float(np.sqrt(self.px * self.px + self.py * self.py))