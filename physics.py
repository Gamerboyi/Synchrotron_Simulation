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
        v2 = 0.999999999 * C * C
    return 1.0 / np.sqrt(1.0 - v2 / (C * C))


def rf_gap_electric_field(x, y, vx, vy, ring_radius, gap_halfwidth=0.08,
                          E0=2e5, use_rf=True, t=0.0, omega=0.0):
    """
    Electric field only exists inside a small gap region near +x axis.

    gap region: |y| < gap_halfwidth AND x > 0

    If use_rf=True:
        Ex = E0 * sin(omega * t)
    else:
        Ex = E0 (constant)

    Field direction: tangential push (approx) along velocity direction.
    """
    # only accelerate near the gap
    if x > 0 and abs(y) < gap_halfwidth:
        # Optional RF oscillation
        if use_rf and omega != 0.0:
            E = E0 * np.sin(omega * t)
        else:
            E = E0

        # Push along direction of motion (tangential acceleration)
        speed = np.sqrt(vx * vx + vy * vy)
        if speed < 1e-12:
            return 0.0, 0.0

        ux = vx / speed
        uy = vy / speed

        Ex = E * ux
        Ey = E * uy
        return Ex, Ey

    return 0.0, 0.0


def derivatives_particle(
    particle,
    Ex=0.0,
    Ey=0.0,
    Bz=0.0,
    relativistic=False,

    # Phase 3 new params:
    ring_radius=5.0,
    enable_rf_gap=False,
    gap_halfwidth=0.08,
    E0=2e5,
    use_rf=False,
    omega=0.0,
    t=0.0
):
    """
    Returns derivatives:
        [dx/dt, dy/dt, dvx/dt, dvy/dt]
    """

    vx, vy = particle.vx, particle.vy
    q, m = particle.q, particle.m

    # -----------------------------
    # Relativistic effective mass
    # -----------------------------
    if relativistic:
        gamma = gamma_from_v(vx, vy)
        particle.gamma = gamma
        m_eff = gamma * m
    else:
        particle.gamma = 1.0
        m_eff = m

    # -----------------------------
    # Phase 3: RF acceleration gap
    # -----------------------------
    if enable_rf_gap:
        Ex_gap, Ey_gap = rf_gap_electric_field(
            particle.x, particle.y, vx, vy,
            ring_radius=ring_radius,
            gap_halfwidth=gap_halfwidth,
            E0=E0,
            use_rf=use_rf,
            t=t,
            omega=omega
        )
        Ex += Ex_gap
        Ey += Ey_gap

    # -----------------------------
    # Lorentz acceleration
    # -----------------------------
    ax, ay = lorentz_acceleration_2d(vx, vy, q, m_eff, Bz=Bz, Ex=Ex, Ey=Ey)

    return np.array([vx, vy, ax, ay], dtype=float)
