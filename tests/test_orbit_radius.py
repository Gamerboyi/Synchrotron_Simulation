import numpy as np

from particle import Particle
from constants import PROTON_CHARGE, PROTON_MASS
from physics import derivatives_particle
from integrators import rk4_step_particle


def test_cyclotron_radius_matches_theory():
    """
    Validate that simulated orbit radius matches:
        r = m*v / (q*B)
    """

    Bz = 1.0
    dt = 1e-10
    steps = 50000

    # Pick speed (non-relativistic)
    v = 2.0e6

    # Theoretical radius
    r_theory = (PROTON_MASS * v) / (PROTON_CHARGE * Bz)

    # Start at (0, r) and move in +x direction.
    # This produces a circle centered at (0,0) for q>0, Bz>0.
    p = Particle(
        x=0.0,
        y=r_theory,
        vx=v,
        vy=0.0,
        q=PROTON_CHARGE,
        m=PROTON_MASS
    )

    rs = []

    for _ in range(steps):
        rk4_step_particle(p, dt, derivatives_particle, Bz=Bz, relativistic=False)
        rs.append(np.sqrt(p.x**2 + p.y**2))

    r_sim = np.mean(rs[int(steps * 0.2):])
    error = abs(r_sim - r_theory) / r_theory

    # 1% tolerance
    assert error < 0.01
