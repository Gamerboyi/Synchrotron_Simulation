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

        # Momentum (phase-space)
        self.px = 0.0
        self.py = 0.0
        self.p = 0.0   # magnitude

        # Revolution tracking
        self.theta_prev = 0.0
        self.theta_accum = 0.0
        self.turns = 0
        self.just_completed_lap = False

        # Trails (two-lap system: current lap white, previous lap green)
        self.trail_current = []
        self.trail_prev = []
        self.trail_counter = 0

        # Hypnosis wipe angle for previous lap fade
        self.prev_lap_wipe_angle = 0.0

    def update_energy(self, relativistic=False):
        v2 = self.vx * self.vx + self.vy * self.vy

        if relativistic:
            self.energy_joules = (self.gamma - 1.0) * self.m * C * C
        else:
            self.energy_joules = 0.5 * self.m * v2

        e_charge = 1.602176634e-19
        self.energy_ev = self.energy_joules / e_charge

        if relativistic:
            self.px = self.gamma * self.m * self.vx
            self.py = self.gamma * self.m * self.vy
        else:
            self.px = self.m * self.vx
            self.py = self.m * self.vy

        self.p = float(np.sqrt(self.px * self.px + self.py * self.py))