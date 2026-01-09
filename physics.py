# physics.py
import numpy as np
from constants import C


def lorentz_acceleration_2d(vx, vy, q, m_eff, Bz=0.0, Ex=0.0, Ey=0.0):
    """
    2D Lorentz acceleration:
        F = q(E + v x B)

    v = (vx, vy, 0)
    B = (0, 0, Bz)

    v x B = (vy*Bz, -vx*Bz, 0)
    """
    ax = (q / m_eff) * (Ex + vy * Bz)
    ay = (q / m_eff) * (Ey - vx * Bz)
    return ax, ay


def gamma_from_v(vx, vy):
    v2 = vx * vx + vy * vy
    if v2 >= C * C:
        # Clamp to avoid numerical explosion
        v2 = 0.999999999 * C * C
    return 1.0 / np.sqrt(1.0 - v2 / (C * C))


def derivatives_particle(particle, Ex=0.0, Ey=0.0, Bz=0.0, relativistic=False):
    """
    Returns derivatives:
        [dx/dt, dy/dt, dvx/dt, dvy/dt]
    """
    vx, vy = particle.vx, particle.vy
    q, m = particle.q, particle.m

    if relativistic:
        gamma = gamma_from_v(vx, vy)
        particle.gamma = gamma
        m_eff = gamma * m
    else:
        particle.gamma = 1.0
        m_eff = m

    ax, ay = lorentz_acceleration_2d(vx, vy, q, m_eff, Bz=Bz, Ex=Ex, Ey=Ey)

    return np.array([vx, vy, ax, ay], dtype=float)
