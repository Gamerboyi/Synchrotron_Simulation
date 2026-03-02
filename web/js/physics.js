// physics.js
import { C } from './constants.js';

export function gammaFromV(vx, vy) {
    let v2 = vx * vx + vy * vy;
    if (v2 >= C * C) v2 = 0.999999999 * C * C;
    return 1.0 / Math.sqrt(1.0 - v2 / (C * C));
}

export function lorentzAcceleration2D(vx, vy, q, mEff, Bz = 0, Ex = 0, Ey = 0) {
    const ax = (q / mEff) * (Ex + vy * Bz);
    const ay = (q / mEff) * (Ey - vx * Bz);
    return [ax, ay];
}

export function rfGapKick(x, y, ringRadius, gapHalfwidth = 0.10, E0 = 5e4, omega = 0, t = 0, rfPhi = 0) {
    if (x <= 0) return [0, 0];
    if (Math.abs(y) > gapHalfwidth) return [0, 0];
    const E = E0 * Math.sin(omega * t + rfPhi);
    return [0, E];
}

export function focusingField(x, y, ringRadius, kFocus = 5e7) {
    const r = Math.sqrt(x * x + y * y);
    if (r < 1e-12) return [0, 0];
    const dr = r - ringRadius;
    const urx = x / r;
    const ury = y / r;
    const Fr = -kFocus * dr;
    return [Fr * urx, Fr * ury];
}

export function derivativesParticle(particle, params) {
    const {
        Ex: exIn = 0, Ey: eyIn = 0, Bz = 0,
        relativistic = false, ringRadius = 5.0,
        enableRfKick = false, gapHalfwidth = 0.10,
        E0 = 5e4, omega = 0, t = 0, rfPhi = 0,
        enableFocusing = false, kFocus = 5e7
    } = params;

    let Ex = exIn, Ey = eyIn;
    const { x, y, vx, vy, q, m } = particle;
    let mEff = m;

    if (relativistic) {
        const gamma = gammaFromV(vx, vy);
        particle.gamma = gamma;
        mEff = gamma * m;
    } else {
        particle.gamma = 1.0;
    }

    if (enableRfKick) {
        const [exG, eyG] = rfGapKick(x, y, ringRadius, gapHalfwidth, E0, omega, t, rfPhi);
        Ex += exG;
        Ey += eyG;
    }

    if (enableFocusing) {
        const [exF, eyF] = focusingField(x, y, ringRadius, kFocus);
        Ex += exF;
        Ey += eyF;
    }

    const [ax, ay] = lorentzAcceleration2D(vx, vy, q, mEff, Bz, Ex, Ey);
    return [vx, vy, ax, ay];
}
