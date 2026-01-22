# physics.py
import numpy as np
from constants import C


def gamma_from_v(vx, vy):
    v2 = vx * vx + vy * vy
    if v2 >= C * C:
        v2 = 0.999999999 * C * C
    return 1.0 / np.sqrt(1.0 - v2 / (C * C))


def lorentz_acceleration_2d(vx, vy, q, m_eff, Bz=0.0, Ex=0.0, Ey=0.0):
    ax = (q / m_eff) * (Ex + vy * Bz)
    ay = (q / m_eff) * (Ey - vx * Bz)
    return ax, ay


def rf_gap_kick(x, y, ring_radius, gap_halfwidth=0.10, E0=5e4, omega=0.0, t=0.0, rf_phi=0.0):
    """
    RF gap on the +x side of the ring.
    Force is applied along the LOCAL TANGENT at the gap (fixed +y direction at x=+R),
    not along the particle velocity. This is physically correct — the cavity field
    is fixed in space, not particle-relative.
    """
    if x <= 0:
        return 0.0, 0.0
    if abs(y) > gap_halfwidth:
        return 0.0, 0.0

    # Sinusoidal RF field — only tangential (y) component at the +x gap
    E = E0 * np.sin(omega * t + rf_phi)

    # At the +x gap, the ideal tangent direction is +y
    # So the electric kick is purely in y
    return 0.0, E


def focusing_field(x, y, ring_radius, k_focus=5e7):
    r = np.sqrt(x * x + y * y)
    if r < 1e-12:
        return 0.0, 0.0

    dr = r - ring_radius
    urx = x / r
    ury = y / r

    Fr = -k_focus * dr
    return Fr * urx, Fr * ury


def derivatives_particle(
    particle,
    Ex=0.0,
    Ey=0.0,
    Bz=0.0,
    relativistic=False,
    ring_radius=5.0,
    enable_rf_kick=False,
    gap_halfwidth=0.10,
    E0=5e4,
    omega=0.0,
    t=0.0,
    rf_phi=0.0,
    enable_focusing=False,
    k_focus=5e7
):
    # Read position/velocity from particle state (set by RK4 before each k eval)
    x, y = particle.x, particle.y
    vx, vy = particle.vx, particle.vy
    q, m = particle.q, particle.m

    if relativistic:
        gamma = gamma_from_v(vx, vy)
        particle.gamma = gamma
        m_eff = gamma * m
    else:
        particle.gamma = 1.0
        m_eff = m

    # RF kick: evaluated at current intermediate position (x, y) and time t
    if enable_rf_kick:
        Ex_gap, Ey_gap = rf_gap_kick(
            x, y,
            ring_radius=ring_radius,
            gap_halfwidth=gap_halfwidth,
            E0=E0,
            omega=omega,
            t=t,
            rf_phi=rf_phi
        )
        Ex += Ex_gap
        Ey += Ey_gap

    # Focusing: evaluated at current intermediate position
    if enable_focusing:
        Ex_f, Ey_f = focusing_field(x, y, ring_radius=ring_radius, k_focus=k_focus)
        Ex += Ex_f
        Ey += Ey_f

    ax, ay = lorentz_acceleration_2d(vx, vy, q, m_eff, Bz=Bz, Ex=Ex, Ey=Ey)

    return np.array([vx, vy, ax, ay], dtype=float)