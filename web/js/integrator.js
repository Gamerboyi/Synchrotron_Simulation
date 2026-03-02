// integrator.js
import { derivativesParticle } from './physics.js';

export function rk4Step(particle, dt, params) {
    const y0 = [particle.x, particle.y, particle.vx, particle.vy];
    const t0 = params.t || 0;

    // k1 at (y0, t)
    params.t = t0;
    const k1 = derivativesParticle(particle, params);

    // k2 at (y0 + 0.5*dt*k1, t + dt/2)
    particle.x  = y0[0] + 0.5 * dt * k1[0];
    particle.y  = y0[1] + 0.5 * dt * k1[1];
    particle.vx = y0[2] + 0.5 * dt * k1[2];
    particle.vy = y0[3] + 0.5 * dt * k1[3];
    params.t = t0 + 0.5 * dt;
    const k2 = derivativesParticle(particle, params);

    // k3 at (y0 + 0.5*dt*k2, t + dt/2)
    particle.x  = y0[0] + 0.5 * dt * k2[0];
    particle.y  = y0[1] + 0.5 * dt * k2[1];
    particle.vx = y0[2] + 0.5 * dt * k2[2];
    particle.vy = y0[3] + 0.5 * dt * k2[3];
    params.t = t0 + 0.5 * dt;
    const k3 = derivativesParticle(particle, params);

    // k4 at (y0 + dt*k3, t + dt)
    particle.x  = y0[0] + dt * k3[0];
    particle.y  = y0[1] + dt * k3[1];
    particle.vx = y0[2] + dt * k3[2];
    particle.vy = y0[3] + dt * k3[3];
    params.t = t0 + dt;
    const k4 = derivativesParticle(particle, params);

    // Final weighted sum
    particle.x  = y0[0] + (dt / 6) * (k1[0] + 2*k2[0] + 2*k3[0] + k4[0]);
    particle.y  = y0[1] + (dt / 6) * (k1[1] + 2*k2[1] + 2*k3[1] + k4[1]);
    particle.vx = y0[2] + (dt / 6) * (k1[2] + 2*k2[2] + 2*k3[2] + k4[2]);
    particle.vy = y0[3] + (dt / 6) * (k1[3] + 2*k2[3] + 2*k3[3] + k4[3]);

    params.t = t0;
}
