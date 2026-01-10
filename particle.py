# particle.py
from dataclasses import dataclass, field
import numpy as np
from constants import C


@dataclass
class Particle:
    # State
    x: float
    y: float
    vx: float
    vy: float

    # Properties
    q: float
    m: float

    # Status
    alive: bool = True

    # Diagnostics
    energy: float = 0.0          # kinetic energy (J)
    gamma: float = 1.0           # relativistic gamma factor
    trail: list = field(default_factory=list)

    def speed(self) -> float:
        """Return particle speed (m/s)."""
        return float(np.sqrt(self.vx * self.vx + self.vy * self.vy))

    def update_energy(self, relativistic: bool = False):
        """
        Update kinetic energy.
        - Non-relativistic: KE = 1/2 m v^2
        - Relativistic:     KE = (gamma - 1) m c^2
        """
        v2 = self.vx * self.vx + self.vy * self.vy

        if relativistic:
            # Prevent invalid gamma if numerical error pushes v >= c
            if v2 >= C * C:
                v2 = 0.999999999 * C * C

            self.gamma = 1.0 / np.sqrt(1.0 - v2 / (C * C))
            self.energy = (self.gamma - 1.0) * self.m * (C * C)
        else:
            self.gamma = 1.0
            self.energy = 0.5 * self.m * v2

    def add_trail_point(self, max_len: int = 3000):
        """
        Store position for visualization.
        max_len keeps memory stable.
        """
        self.trail.append((self.x, self.y))
        if len(self.trail) > max_len:
            self.trail.pop(0)
