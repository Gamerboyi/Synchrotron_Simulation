# physics.py
import numpy as np
from constants import C


def lorentz_acceleration_2d(vx, vy, q, m_eff, Bz=0.0, Ex=0.0, Ey=0.0):
    ax = (q / m_eff) * (Ex + vy * Bz)
    ay = (q / m_eff) * (Ey - vx * Bz)
    return ax, ay


def gamma_from_v(vx, vy):
    v2 = vx * vx + vy * vy
    if v2 >= C * C:
        v2 = 0.999999999 * C * C
    return 1.0 / np.sqrt(1.0 - v2 / (C * C))


# -----------------------------
# Phase 5/6: RF Kick (Synchrotron gap)
# -----------------------------
def rf_kick_electric_field(
    x, y, vx, vy, ring_radius,
    gap_halfwidth=0.10,
    E0=5e4,
    t=0.0,
    omega=0.0,
    rf_phi=0.0
):
    # Gap on +x side
    if x > 0 and abs(y) < gap_halfwidth:

        # Sinusoidal accelerating field
        E = E0 * np.sin(omega * t + rf_phi)

        speed = np.sqrt(vx * vx + vy * vy)
        if speed < 1e-12:
            return 0.0, 0.0

        # Along velocity direction
        ux = vx / speed
        uy = vy / speed

        return E * ux, E * uy

    return 0.0, 0.0


# -----------------------------
# Phase 4/6: Radial Focusing
# -----------------------------
def focusing_field(x, y, ring_radius, k_focus=5e7):
    r = np.sqrt(x * x + y * y)
    if r < 1e-12:
        return 0.0, 0.0

    dr = r - ring_radius

    urx = x / r
    ury = y / r

    Fr = -k_focus * dr

    Ex = Fr * urx
    Ey = Fr * ury
    return Ex, Ey


# -----------------------------
# Main Derivatives Function
# -----------------------------
def derivatives_particle(
    particle,
    Ex=0.0,
    Ey=0.0,
    Bz=0.0,
    relativistic=False,

    ring_radius=5.0,

    # Phase 5/6 RF Kick
    enable_rf_kick=False,
    gap_halfwidth=0.10,
    E0=5e4,
    omega=0.0,
    t=0.0,
    rf_phi=0.0,

    # Phase 4/6 focusing
    enable_focusing=False,
    k_focus=5e7
):
    vx, vy = particle.vx, particle.vy
    q, m = particle.q, particle.m

    # Relativistic effective mass
    if relativistic:
        gamma = gamma_from_v(vx, vy)
        particle.gamma = gamma
        m_eff = gamma * m
    else:
        particle.gamma = 1.0
        m_eff = m

    # Phase 5/6 RF kick
    if enable_rf_kick:
        Ex_gap, Ey_gap = rf_kick_electric_field(
            particle.x, particle.y, vx, vy,
            ring_radius=ring_radius,
            gap_halfwidth=gap_halfwidth,
            E0=E0,
            t=t,
            omega=omega,
            rf_phi=rf_phi
        )
        Ex += Ex_gap
        Ey += Ey_gap

    # Phase 4/6 focusing
    if enable_focusing:
        Ex_focus, Ey_focus = focusing_field(
            particle.x, particle.y,
            ring_radius=ring_radius,
            k_focus=k_focus
        )
        Ex += Ex_focus
        Ey += Ey_focus

    # Lorentz acceleration
    ax, ay = lorentz_acceleration_2d(
        vx, vy, q, m_eff,
        Bz=Bz,
        Ex=Ex,
        Ey=Ey
    )

    return np.array([vx, vy, ax, ay], dtype=float)
