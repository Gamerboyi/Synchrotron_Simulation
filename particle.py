# particle.py
import numpy as np
from constants import C


class Particle:
    def __init__(self, x, y, vx, vy, q, m, alive=True):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)

        self.q = float(q)
        self.m = float(m)

        self.alive = alive

        # Relativistic factor
        self.gamma = 1.0

        # Energy
        self.energy_joules = 0.0
        self.energy_ev = 0.0

        # Trail
        self.trail = []
        self.max_trail_points = 400

        # -----------------------------
        # PHASE 7 FIX: Momentum values
        # -----------------------------
        # These are used by phase-space plots in visualize.py
        self.px = 0.0
        self.py = 0.0

    def add_trail_point(self):
        self.trail.append((self.x, self.y))

        if len(self.trail) > self.max_trail_points:
            self.trail.pop(0)

    def update_energy(self, relativistic=False):
        v2 = self.vx * self.vx + self.vy * self.vy

        if relativistic:
            self.energy_joules = (self.gamma - 1.0) * self.m * C * C
        else:
            self.energy_joules = 0.5 * self.m * v2

        # Convert to eV
        e_charge = 1.602176634e-19
        self.energy_ev = self.energy_joules / e_charge

        # -----------------------------
        # PHASE 7: Update momenta
        # -----------------------------
        # p = gamma*m*v
        if relativistic:
            self.px = self.gamma * self.m * self.vx
            self.py = self.gamma * self.m * self.vy
        else:
            self.px = self.m * self.vx
            self.py = self.m * self.vy
