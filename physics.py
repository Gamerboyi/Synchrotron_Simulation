# physics.py
import numpy as np

def lorentz_acceleration_2d(vx, vy, q, m, Bz=0.0, Ex=0.0, Ey=0.0):
    """
    Returns acceleration (ax, ay) for a charged particle in 2D.

    v = (vx, vy)
    B = (0, 0, Bz)
    E = (Ex, Ey, 0)

    Lorentz force: F = q(E + v x B)
    """
    ax = (q / m) * (Ex + vy * Bz)
    ay = (q / m) * (Ey - vx * Bz)
    return ax, ay


def derivatives_particle(particle, Ex=0.0, Ey=0.0, Bz=0.0, relativistic=False):
    """
    Compute derivatives for a single Particle instance
    Returns: [dx/dt, dy/dt, dvx/dt, dvy/dt]
    Updates relativistic gamma if enabled.
    """
    vx, vy = particle.vx, particle.vy
    m, q = particle.m, particle.q

    if relativistic:
        c = 299_792_458
        v2 = vx**2 + vy**2
        gamma = 1.0 / np.sqrt(1 - v2 / c**2)
        m_rel = gamma * m
        particle.gamma = gamma
    else:
        m_rel = m
        particle.gamma = 1.0

    ax, ay = lorentz_acceleration_2d(vx, vy, q, m_rel, Bz, Ex, Ey)
    return np.array([particle.vx, particle.vy, ax, ay], dtype=float)


def update_particles(particles, Ex=0.0, Ey=0.0, Bz=0.0, relativistic=False):
    """
    For a list of Particle objects, compute their derivatives.
    Returns a list of derivative arrays (dx, dy, dvx, dvy)
    """
    derivatives_list = []
    for p in particles:
        if p.alive:
            deriv = derivatives_particle(p, Ex=Ex, Ey=Ey, Bz=Bz, relativistic=relativistic)
            derivatives_list.append(deriv)
        else:
            derivatives_list.append(np.array([0.0, 0.0, 0.0, 0.0]))
    return derivatives_list
