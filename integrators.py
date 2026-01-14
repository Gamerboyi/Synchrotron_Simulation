# integrators.py
import numpy as np
from particle import Particle


def rk4_step_particle(particle, dt, derivs_func, **kwargs):
    """
    RK4 step for Particle object.

    derivs_func(particle, **kwargs) -> np.array([dx, dy, dvx, dvy])
    """

    # Current state vector
    s = np.array([particle.x, particle.y, particle.vx, particle.vy], dtype=float)

    # Helper to build a temp particle
    def temp_particle_from_state(state_vec):
        return Particle(
            x=float(state_vec[0]),
            y=float(state_vec[1]),
            vx=float(state_vec[2]),
            vy=float(state_vec[3]),
            q=particle.q,
            m=particle.m,
            alive=particle.alive
        )

    k1 = derivs_func(particle, **kwargs)

    p2 = temp_particle_from_state(s + 0.5 * dt * k1)
    k2 = derivs_func(p2, **kwargs)

    p3 = temp_particle_from_state(s + 0.5 * dt * k2)
    k3 = derivs_func(p3, **kwargs)

    p4 = temp_particle_from_state(s + dt * k3)
    k4 = derivs_func(p4, **kwargs)

    s_new = s + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)

    # Write back
    particle.x = float(s_new[0])
    particle.y = float(s_new[1])
    particle.vx = float(s_new[2])
    particle.vy = float(s_new[3])

    # Update energy (DO NOT update trail here)
    particle.update_energy(relativistic=kwargs.get("relativistic", False))
