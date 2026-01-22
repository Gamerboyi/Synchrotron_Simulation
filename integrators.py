# integrators.py
import numpy as np


def rk4_step_particle(particle, dt, derivs_func, **kwargs):
    """
    RK4 integrator for Particle objects.

    FIX: The RF kick depends on time `t`. Each RK4 sub-step should evaluate
    at the correct intermediate time:
        k1 at t
        k2 at t + dt/2
        k3 at t + dt/2
        k4 at t + dt

    We extract `t` from kwargs and pass corrected values per sub-step.
    """

    y0 = np.array([particle.x, particle.y, particle.vx, particle.vy], dtype=float)
    t0 = kwargs.get('t', 0.0)

    # --- k1 at (y0, t) ---
    kwargs['t'] = t0
    k1 = derivs_func(particle, **kwargs)

    # --- k2 at (y0 + 0.5*dt*k1, t + dt/2) ---
    particle.x  = y0[0] + 0.5 * dt * k1[0]
    particle.y  = y0[1] + 0.5 * dt * k1[1]
    particle.vx = y0[2] + 0.5 * dt * k1[2]
    particle.vy = y0[3] + 0.5 * dt * k1[3]
    kwargs['t'] = t0 + 0.5 * dt
    k2 = derivs_func(particle, **kwargs)

    # --- k3 at (y0 + 0.5*dt*k2, t + dt/2) ---
    particle.x  = y0[0] + 0.5 * dt * k2[0]
    particle.y  = y0[1] + 0.5 * dt * k2[1]
    particle.vx = y0[2] + 0.5 * dt * k2[2]
    particle.vy = y0[3] + 0.5 * dt * k2[3]
    kwargs['t'] = t0 + 0.5 * dt
    k3 = derivs_func(particle, **kwargs)

    # --- k4 at (y0 + dt*k3, t + dt) ---
    particle.x  = y0[0] + dt * k3[0]
    particle.y  = y0[1] + dt * k3[1]
    particle.vx = y0[2] + dt * k3[2]
    particle.vy = y0[3] + dt * k3[3]
    kwargs['t'] = t0 + dt
    k4 = derivs_func(particle, **kwargs)

    # --- Final weighted sum ---
    particle.x  = y0[0] + (dt / 6.0) * (k1[0] + 2*k2[0] + 2*k3[0] + k4[0])
    particle.y  = y0[1] + (dt / 6.0) * (k1[1] + 2*k2[1] + 2*k3[1] + k4[1])
    particle.vx = y0[2] + (dt / 6.0) * (k1[2] + 2*k2[2] + 2*k3[2] + k4[2])
    particle.vy = y0[3] + (dt / 6.0) * (k1[3] + 2*k2[3] + 2*k3[3] + k4[3])

    # Restore original t in kwargs so the caller's t is unchanged
    kwargs['t'] = t0