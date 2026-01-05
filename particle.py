# particle.py
from dataclasses import dataclass, field
import numpy as np

@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    q: float
    m: float
    alive: bool = True
    energy: float = 0.0          # total kinetic energy (updated each step)
    gamma: float = 1.0           # relativistic factor (optional)
    trail: list = field(default_factory=list)  # store trajectory for visualization

    def update_energy(self, relativistic=False):
        """Update particle energy"""
        v2 = self.vx**2 + self.vy**2
        if relativistic:
            c = 299_792_458  # m/s
            self.gamma = 1.0 / np.sqrt(1 - v2 / c**2)
            self.energy = self.gamma * self.m * c**2
        else:
            self.energy = 0.5 * self.m * v2

    def add_trail_point(self):
        """Append current position to trail"""
        self.trail.append((self.x, self.y))
        # Optional: limit trail length
        if len(self.trail) > 3000:
            self.trail.pop(0)
