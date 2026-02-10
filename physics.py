# physics.py
"""
Physics engine for the synchrotron ring simulation.

Implements the core electromagnetic forces acting on charged particles
in a circular accelerator:
    - Lorentz force:  F = q(E + v × B)
    - RF cavity gap:  Sinusoidal electric field at the +x gap
    - Focusing field: Radial restoring force toward ring center

Reference: Wiedemann, H. "Particle Accelerator Physics" (Springer, 4th ed.)
"""

import numpy as np
from typing import Tuple
from constants import C


def gamma_from_v(vx: float, vy: float) -> float:
    """
    Compute the Lorentz factor γ from velocity components.

        γ = 1 / √(1 - v²/c²)

    If v >= c, clamps to 0.999999999c to avoid division by zero.

    Args:
        vx: x-component of velocity (m/s)
        vy: y-component of velocity (m/s)

    Returns:
        Lorentz factor γ (dimensionless, >= 1.0)
    """
    v2: float = vx * vx + vy * vy
    if v2 >= C * C:
        v2 = 0.999999999 * C * C
    return 1.0 / np.sqrt(1.0 - v2 / (C * C))


def lorentz_acceleration_2d(
    vx: float,
    vy: float,
    q: float,
    m_eff: float,
    Bz: float = 0.0,
    Ex: float = 0.0,
    Ey: float = 0.0,
) -> Tuple[float, float]:
    """
    Compute 2D acceleration from the Lorentz force.

    In the x-y plane with B = Bz·ẑ:
        ax = (q/m_eff) · (Ex + vy·Bz)
        ay = (q/m_eff) · (Ey - vx·Bz)

    Args:
        vx, vy : velocity components (m/s)
        q      : particle charge (C)
        m_eff  : effective mass γm for relativistic, m otherwise (kg)
        Bz     : magnetic field z-component (Tesla)
        Ex, Ey : electric field components (V/m)

    Returns:
        (ax, ay): acceleration components (m/s²)
    """
    ax: float = (q / m_eff) * (Ex + vy * Bz)
    ay: float = (q / m_eff) * (Ey - vx * Bz)
    return ax, ay


def rf_gap_kick(
    x: float,
    y: float,
    ring_radius: float,
    gap_halfwidth: float = 0.10,
    E0: float = 5e4,
    omega: float = 0.0,
    t: float = 0.0,
    rf_phi: float = 0.0,
) -> Tuple[float, float]:
    """
    RF cavity gap electric field on the +x side of the ring.

    A real synchrotron accelerates particles only inside a localized
    RF cavity. This function models a cavity at the +x midplane:
        - Active only when x > 0 AND |y| < gap_halfwidth
        - Field: E(t) = E0 · sin(ωt + φ)
        - Direction: tangential (+y at the +x gap)

    The cavity field is fixed in lab frame (not particle-relative),
    which is the physically correct behavior.

    Args:
        x, y           : particle position (m)
        ring_radius    : nominal ring radius (m) — unused but kept for API consistency
        gap_halfwidth  : half-width of the RF gap region (m)
        E0             : peak electric field amplitude (V/m)
        omega          : RF angular frequency (rad/s)
        t              : current simulation time (s)
        rf_phi         : RF phase offset (rad)

    Returns:
        (Ex, Ey): electric field components at particle location (V/m)
    """
    if x <= 0:
        return 0.0, 0.0
    if abs(y) > gap_halfwidth:
        return 0.0, 0.0

    E: float = E0 * np.sin(omega * t + rf_phi)
    return 0.0, E


def focusing_field(
    x: float,
    y: float,
    ring_radius: float,
    k_focus: float = 5e7,
) -> Tuple[float, float]:
    """
    Radial restoring (focusing) field to keep beam near ring radius.

    Models a linear restoring force proportional to radial displacement
    from the design orbit:
        F_r = -k · (r - R_ring)

    This mimics the combined effect of quadrupole magnets in a real
    synchrotron lattice (simplified to a continuous field).

    Args:
        x, y        : particle position (m)
        ring_radius : nominal ring radius (m)
        k_focus     : focusing strength (N/m)

    Returns:
        (Fx, Fy): restoring force components (N/m — per unit charge,
                  applied as effective E-field)
    """
    r: float = np.sqrt(x * x + y * y)
    if r < 1e-12:
        return 0.0, 0.0

    dr: float = r - ring_radius
    urx: float = x / r
    ury: float = y / r

    Fr: float = -k_focus * dr
    return Fr * urx, Fr * ury


def derivatives_particle(
    particle: "Particle",
    Ex: float = 0.0,
    Ey: float = 0.0,
    Bz: float = 0.0,
    relativistic: bool = False,
    ring_radius: float = 5.0,
    enable_rf_kick: bool = False,
    gap_halfwidth: float = 0.10,
    E0: float = 5e4,
    omega: float = 0.0,
    t: float = 0.0,
    rf_phi: float = 0.0,
    enable_focusing: bool = False,
    k_focus: float = 5e7,
) -> np.ndarray:
    """
    Compute state derivatives [dx/dt, dy/dt, dvx/dt, dvy/dt] for RK4 integration.

    This is the right-hand side of the ODE system:
        dx/dt  = vx
        dy/dt  = vy
        dvx/dt = ax  (from Lorentz + RF + focusing)
        dvy/dt = ay

    The function composes all force contributions (magnetic bending,
    RF cavity, focusing) into a single acceleration vector.

    Args:
        particle       : Particle object with current state
        Ex, Ey         : external electric field (V/m)
        Bz             : magnetic field z-component (T)
        relativistic   : use relativistic mass γm
        ring_radius    : design orbit radius (m)
        enable_rf_kick : apply RF cavity field
        gap_halfwidth  : RF gap half-width (m)
        E0             : RF peak field (V/m)
        omega          : RF frequency (rad/s)
        t              : current time (s)
        rf_phi         : RF phase (rad)
        enable_focusing: apply radial focusing
        k_focus        : focusing strength (N/m)

    Returns:
        numpy array [vx, vy, ax, ay]
    """
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

    if enable_rf_kick:
        Ex_gap, Ey_gap = rf_gap_kick(
            x, y,
            ring_radius=ring_radius,
            gap_halfwidth=gap_halfwidth,
            E0=E0,
            omega=omega,
            t=t,
            rf_phi=rf_phi,
        )
        Ex += Ex_gap
        Ey += Ey_gap

    if enable_focusing:
        Ex_f, Ey_f = focusing_field(x, y, ring_radius=ring_radius, k_focus=k_focus)
        Ex += Ex_f
        Ey += Ey_f

    ax, ay = lorentz_acceleration_2d(vx, vy, q, m_eff, Bz=Bz, Ex=Ex, Ey=Ey)

    return np.array([vx, vy, ax, ay], dtype=float)