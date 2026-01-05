# integrators.py
import numpy as np

def rk4_step_particle(particle, dt, derivs_func, **kwargs):
    """
    One RK4 step for a single Particle object.

    particle: Particle instance
    dt: timestep
    derivs_func: function(particle, **kwargs) -> derivatives [dx, dy, dvx, dvy]
    """
    state = np.array([particle.x, particle.y, particle.vx, particle.vy], dtype=float)

    # k1
    k1 = derivs_func(particle, **kwargs)

    # k2
    temp_state = state + 0.5 * dt * k1
    particle_temp = particle.__class__(*temp_state, q=particle.q, m=particle.m)
    k2 = derivs_func(particle_temp, **kwargs)

    # k3
    temp_state = state + 0.5 * dt * k2
    particle_temp = particle.__class__(*temp_state, q=particle.q, m=particle.m)
    k3 = derivs_func(particle_temp, **kwargs)

    # k4
    temp_state = state + dt * k3
    particle_temp = particle.__class__(*temp_state, q=particle.q, m=particle.m)
    k4 = derivs_func(particle_temp, **kwargs)

    # RK4 update
    new_state = state + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
    particle.x, particle.y, particle.vx, particle.vy = new_state

    # Optional relativistic energy update
    if hasattr(particle, "update_energy"):
        particle.update_energy(relativistic=kwargs.get("relativistic", False))

    # Optional trail update
    if hasattr(particle, "add_trail_point"):
        particle.add_trail_point()


def rk4_step_particles(particles, dt, derivs_func, **kwargs):
    """
    One RK4 step for a list of Particle objects.
    Only updates particles with alive=True.
    """
    for p in particles:
        if p.alive:
            rk4_step_particle(p, dt, derivs_func, **kwargs)


def rk4_step(state, dt, derivs_func, *args, **kwargs):
    """
    Legacy RK4 step for numpy state array (x, y, vx, vy).
    Keeps old functionality compatible with main.py non-particle version.
    """
    k1 = derivs_func(state, *args, **kwargs)
    k2 = derivs_func(state + 0.5 * dt * k1, *args, **kwargs)
    k3 = derivs_func(state + 0.5 * dt * k2, *args, **kwargs)
    k4 = derivs_func(state + dt * k3, *args, **kwargs)
    return state + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
