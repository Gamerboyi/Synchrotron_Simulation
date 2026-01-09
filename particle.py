# particle.py
from dataclasses import dataclass, field
import numpy as np

C = 299_792_458.0  # speed of light (m/s)


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
    kinetic_energy: float = 0.0   # Joules
    total_energy: float = 0.0     # Joules (only meaningful if relativistic)
    gamma: float = 1.0            # relativistic factor

    # Visualization
    trail: list = field(default_factory=list)
    max_trail: int = 2500

    def speed(self) -> float:
        return float(np.sqrt(self.vx * self.vx + self.vy * self.vy))

    def update_energy(self, relativistic: bool = False):
        """
        Updates:
        - kinetic_energy
        - total_energy (if relativistic)
        - gamma (if relativistic)
        """
        v2 = self.vx * self.vx + self.vy * self.vy

        if relativistic:
            # Prevent invalid sqrt if v slightly exceeds c due to numeric error
            if v2 >= 0.999999999 * C * C:
                v2 = 0.999999999 * C * C

            self.gamma = 1.0 / np.sqrt(1.0 - v2 / (C * C))

            # Total energy = gamma*m*c^2
            self.total_energy = self.gamma * self.m * (C * C)

            # Kinetic energy = (gamma-1)*m*c^2
            self.kinetic_energy = (self.gamma - 1.0) * self.m * (C * C)

        else:
            self.gamma = 1.0
            self.kinetic_energy = 0.5 * self.m * v2
            self.total_energy = self.kinetic_energy

    def add_trail_point(self):
        """Store current (x,y) for rendering"""
        self.trail.append((self.x, self.y))
        if len(self.trail) > self.max_trail:
            self.trail.pop(0)

    def reset_trail(self):
        self.trail.clear()
