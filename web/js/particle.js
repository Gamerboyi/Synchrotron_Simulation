// particle.js
import { C, EV_TO_JOULES } from './constants.js';

export class Particle {
    constructor(x, y, vx, vy, q, m) {
        this.x = x;
        this.y = y;
        this.vx = vx;
        this.vy = vy;
        this.q = q;
        this.m = m;
        this.alive = true;

        this.gamma = 1.0;
        this.energyJoules = 0;
        this.energyEv = 0;
        this.px = 0;
        this.py = 0;
        this.p = 0;

        // Revolution tracking
        this.thetaPrev = 0;
        this.thetaAccum = 0;
        this.turns = 0;
        this.justCompletedLap = false;

        // Trail storage (ring positions as angles for 3D mapping)
        this.trail = [];
        this.trailPrev = [];
        this.trailPrevAlpha = 0;
        this.trailCounter = 0;
    }

    updateEnergy(relativistic) {
        const v2 = this.vx * this.vx + this.vy * this.vy;
        if (relativistic) {
            this.energyJoules = (this.gamma - 1.0) * this.m * C * C;
        } else {
            this.energyJoules = 0.5 * this.m * v2;
        }
        this.energyEv = this.energyJoules / EV_TO_JOULES;

        if (relativistic) {
            this.px = this.gamma * this.m * this.vx;
            this.py = this.gamma * this.m * this.vy;
        } else {
            this.px = this.m * this.vx;
            this.py = this.m * this.vy;
        }
        this.p = Math.sqrt(this.px * this.px + this.py * this.py);
    }
}
