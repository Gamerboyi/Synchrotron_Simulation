# integrators.py
"""
Numerical integration methods for the particle simulation.

Implements a 4th-order Runge-Kutta (RK4) integrator that operates
directly on Particle objects. RK4 provides O(h⁴) local truncation
error, which is critical for maintaining orbit stability over many
thousands of revolutions.

Reference: Press et al. "Numerical Recipes" (Cambridge, 3rd ed.), §17.1
"""

from __future__ import annotations

import numpy as np
from typing import Callable, Any

from particle import Particle


def rk4_step_particle(
    particle: Particle,
    dt: float,
    derivs_func: Callable[..., np.ndarray],
    **kwargs: Any,
) -> None:
    """
    Advance a particle by one RK4 time step.

    Updates particle.x, particle.y, particle.vx, particle.vy in-place
    using the classical 4th-order Runge-Kutta method:

        k1 = f(y_n,         t)
        k2 = f(y_n + h/2·k1, t + h/2)
        k3 = f(y_n + h/2·k2, t + h/2)
        k4 = f(y_n + h·k3,   t + h)

        y_{n+1} = y_n + (h/6)(k1 + 2k2 + 2k3 + k4)

    The particle's position/velocity are temporarily modified for each
    sub-step evaluation, then restored to the final weighted sum.

    Time `t` in kwargs is correctly adjusted per sub-step so that
    time-dependent forces (e.g., RF cavity) are evaluated at the
    proper intermediate times.

    Args:
        particle    : Particle object to advance
        dt          : time step size in seconds (s)
        derivs_func : function returning [vx, vy, ax, ay] given particle + kwargs
        **kwargs    : additional arguments forwarded to derivs_func
                      (Bz, relativistic, enable_rf_kick, t, etc.)
    """
    y0: np.ndarray = np.array(
        [particle.x, particle.y, particle.vx, particle.vy], dtype=float
    )
    t0: float = kwargs.get("t", 0.0)

    # --- k1 at (y0, t) ---
    kwargs["t"] = t0
    k1: np.ndarray = derivs_func(particle, **kwargs)

    # --- k2 at (y0 + 0.5·dt·k1, t + dt/2) ---
    particle.x = y0[0] + 0.5 * dt * k1[0]
    particle.y = y0[1] + 0.5 * dt * k1[1]
    particle.vx = y0[2] + 0.5 * dt * k1[2]
    particle.vy = y0[3] + 0.5 * dt * k1[3]
    kwargs["t"] = t0 + 0.5 * dt
    k2: np.ndarray = derivs_func(particle, **kwargs)

    # --- k3 at (y0 + 0.5·dt·k2, t + dt/2) ---
    particle.x = y0[0] + 0.5 * dt * k2[0]
    particle.y = y0[1] + 0.5 * dt * k2[1]
    particle.vx = y0[2] + 0.5 * dt * k2[2]
    particle.vy = y0[3] + 0.5 * dt * k2[3]
    kwargs["t"] = t0 + 0.5 * dt
    k3: np.ndarray = derivs_func(particle, **kwargs)

    # --- k4 at (y0 + dt·k3, t + dt) ---
    particle.x = y0[0] + dt * k3[0]
    particle.y = y0[1] + dt * k3[1]
    particle.vx = y0[2] + dt * k3[2]
    particle.vy = y0[3] + dt * k3[3]
    kwargs["t"] = t0 + dt
    k4: np.ndarray = derivs_func(particle, **kwargs)

    # --- Final weighted sum ---
    particle.x = y0[0] + (dt / 6.0) * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
    particle.y = y0[1] + (dt / 6.0) * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
    particle.vx = y0[2] + (dt / 6.0) * (k1[2] + 2 * k2[2] + 2 * k3[2] + k4[2])
    particle.vy = y0[3] + (dt / 6.0) * (k1[3] + 2 * k2[3] + 2 * k3[3] + k4[3])

    # Restore original t in kwargs so the caller's t is unchanged
    kwargs["t"] = t0