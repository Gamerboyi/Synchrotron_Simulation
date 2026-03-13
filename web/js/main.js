// main.js — Orchestration, simulation loop, beam management
import { Particle } from './particle.js';
import { rk4Step } from './integrator.js';
import { Renderer } from './renderer.js';
import { Dashboard } from './dashboard.js';
import { Controls } from './controls.js';
import { PROTON_MASS, PROTON_CHARGE, C } from './constants.js';

// ─── Simulation State ───
const sim = {
    enableRfKick: true,
    enableFocusing: true,
    relativistic: true,
    enableBRamp: true,
    drawTrails: true,
    enableGlow: true,
    paused: false,
    stepsPerFrame: 1200,
    Bz: 0.0313,
    BzInit: 0.0313,
    BzMax: 2.0,
    E0: 5e4,
    kFocus: 5e7,
    ringRadius: 5.0,
    dt: 1e-9,
    gapHalfwidth: 0.10,
    omega: 2 * Math.PI * 2e7,
    rfPhi: 0.0,
    lossLow: 0.70,
    lossHigh: 1.30,
    bGain: 5.0,
    numParticles: 40,
    sigmaPos: 0.02,
    sigmaVel: 2e4,
    trailAddEvery: 8,
    maxTrailPoints: 180,
};

let beam = [];
let simTime = 0;
let frameCount = 0;
let lastFpsTime = performance.now();
let currentFps = 60;

// ─── Gaussian random (Box-Muller) ───
function gaussRandom(mean = 0, std = 1) {
    const u1 = Math.random();
    const u2 = Math.random();
    return mean + std * Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// ─── Beam Creation ───
function createBeam() {
    const b = [];
    const v0 = 0.05 * C;

    for (let i = 0; i < sim.numParticles; i++) {
        const theta = gaussRandom(0, 0.06);
        const r = sim.ringRadius + gaussRandom(0, sim.sigmaPos);
        const x = r * Math.cos(theta);
        const y = r * Math.sin(theta);
        const tx = -Math.sin(theta);
        const ty = Math.cos(theta);
        const speed = v0 + gaussRandom(0, sim.sigmaVel);

        const p = new Particle(x, y, speed * tx, speed * ty, PROTON_CHARGE, PROTON_MASS);
        p.updateEnergy(sim.relativistic);
        p.thetaPrev = Math.atan2(y, x);
        p.thetaAccum = 0;
        p.turns = 0;
        p.justCompletedLap = false;
        p.trail = [[x, y]];
        p.trailCounter = 0;
        b.push(p);
    }
    return b;
}

function updateRevolutionCounter(p) {
    const theta = Math.atan2(p.y, p.x);
    let dtheta = theta - p.thetaPrev;
    if (dtheta > Math.PI) dtheta -= 2 * Math.PI;
    if (dtheta < -Math.PI) dtheta += 2 * Math.PI;
    p.thetaAccum += dtheta;
    const turns = Math.floor(Math.abs(p.thetaAccum) / (2 * Math.PI));
    p.justCompletedLap = (turns !== p.turns);
    p.turns = turns;
    p.thetaPrev = theta;
}

function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }

// ─── Initialize ───
const viewportEl = document.getElementById('viewport');
const graphsEl = document.getElementById('graphs-container');

const renderer = new Renderer(viewportEl);
const dashboard = new Dashboard(graphsEl);

function doReset() {
    beam = createBeam();
    sim.Bz = sim.BzInit;
    simTime = 0;
    sim.paused = false;
    const pauseBtn = document.getElementById('btn-pause');
    if (pauseBtn) {
        pauseBtn.textContent = '⏸ PAUSE';
        pauseBtn.classList.remove('paused');
    }
}

function doRespawn() {
    beam = createBeam();
    sim.Bz = sim.BzInit;
}

const controls = new Controls(sim, doReset, doRespawn);

beam = createBeam();

// ─── Intro Overlay ───
const introOverlay = document.getElementById('intro-overlay');
const introStartBtn = document.getElementById('intro-start');
function dismissIntro() {
    if (introOverlay && !introOverlay.classList.contains('hidden')) {
        introOverlay.classList.add('hidden');
        setTimeout(() => introOverlay.style.display = 'none', 700);
    }
}
if (introStartBtn) introStartBtn.addEventListener('click', dismissIntro);
window.addEventListener('keydown', (e) => {
    if (e.key === ' ' && introOverlay && !introOverlay.classList.contains('hidden')) {
        e.preventDefault();
        dismissIntro();
    }
});

// ─── About Section Toggle ───
const aboutToggle = document.getElementById('about-toggle');
const aboutSection = document.getElementById('about-section');
const aboutArrow = document.getElementById('about-arrow');
if (aboutToggle && aboutSection) {
    aboutToggle.addEventListener('click', () => {
        aboutSection.classList.toggle('collapsed');
        if (aboutArrow) aboutArrow.textContent = aboutSection.classList.contains('collapsed') ? '▶' : '▼';
    });
}

// ─── Narration Engine ───
const narrationEl = document.getElementById('narration-text');
let narrationTimer = 0;
let lastNarration = '';

function updateNarration(stats) {
    narrationTimer++;
    if (narrationTimer % 90 !== 0) return; // Update every ~1.5s at 60fps

    let msg = '';
    const alive = stats.alive;
    const total = stats.total;
    const pctAlive = (alive / total * 100).toFixed(0);

    if (sim.paused) {
        msg = `⏸ <strong>Paused</strong> — ${alive} of ${total} protons alive. Press SPACE to resume.`;
    } else if (alive === 0) {
        msg = `💀 <strong>Beam lost!</strong> All particles escaped the aperture. Press R to reset.`;
    } else if (stats.maxTurns < 3) {
        msg = `🚀 <strong>Beam injected</strong> — ${alive} protons orbiting at ~5% speed of light. The magnetic field (Bz = ${stats.Bz.toFixed(3)} T) bends them into a circle.`;
    } else if (stats.maxTurns < 10) {
        msg = `⚡ <strong>Accelerating</strong> — The RF cavity kicks each proton once per revolution. Energy: ${stats.meanE.toFixed(0)} eV after ${stats.maxTurns} turns.`;
    } else if (alive < total * 0.5 && !sim.enableFocusing) {
        msg = `⚠️ <strong>Beam loss!</strong> Only ${pctAlive}% of protons survive. Try enabling <strong>Focus</strong> to add a restoring force that keeps them on orbit.`;
    } else if (sim.enableBRamp && stats.Bz > sim.BzInit * 1.5) {
        msg = `🧲 <strong>B-field ramping</strong> — Bz has increased to ${stats.Bz.toFixed(3)} T to keep the beam on its design orbit as energy rises. This is how real synchrotrons work.`;
    } else if (stats.maxTurns >= 10) {
        msg = `🔬 <strong>Stable orbit</strong> — ${alive} protons completing turn #${stats.maxTurns}. ${sim.relativistic ? 'Relativistic corrections (γ factor) applied.' : 'Classical (non-relativistic) mode.'}`;
    } else {
        msg = `📡 <strong>${alive} protons</strong> circulating. Mean radius: ${stats.meanR.toFixed(3)} m | Energy: ${stats.meanE.toFixed(0)} eV`;
    }

    if (msg !== lastNarration && narrationEl) {
        narrationEl.innerHTML = msg;
        lastNarration = msg;
    }
}

// ─── Animation Loop ───
function animate() {
    requestAnimationFrame(animate);

    // FPS counter
    frameCount++;
    const now = performance.now();
    if (now - lastFpsTime >= 1000) {
        currentFps = frameCount;
        frameCount = 0;
        lastFpsTime = now;
    }

    if (!sim.paused) {
        const alive = beam.filter(p => p.alive);

        // B-ramp stabilizer
        if (sim.enableBRamp && alive.length > 0) {
            let meanR = 0;
            alive.forEach(p => { meanR += Math.sqrt(p.x * p.x + p.y * p.y); });
            meanR /= alive.length;
            const rErr = (meanR - sim.ringRadius) / sim.ringRadius;
            sim.Bz += sim.bGain * rErr * sim.Bz * sim.dt * sim.stepsPerFrame;
            sim.Bz = clamp(sim.Bz, sim.BzInit, sim.BzMax);
        }

        // Physics steps
        const params = {
            Bz: sim.Bz,
            relativistic: sim.relativistic,
            ringRadius: sim.ringRadius,
            enableRfKick: sim.enableRfKick,
            gapHalfwidth: sim.gapHalfwidth,
            E0: sim.E0,
            omega: sim.omega,
            t: simTime,
            rfPhi: sim.rfPhi,
            enableFocusing: sim.enableFocusing,
            kFocus: sim.kFocus,
        };

        for (let s = 0; s < sim.stepsPerFrame; s++) {
            simTime += sim.dt;
            params.t = simTime;

            for (const p of beam) {
                if (!p.alive) continue;

                rk4Step(p, sim.dt, params);
                p.updateEnergy(sim.relativistic);
                updateRevolutionCounter(p);

                // Lap completion
                if (p.justCompletedLap) {
                    p.trailPrev = [...p.trail];
                    p.trailPrevAlpha = 220;
                    p.trail = [[p.x, p.y]];
                }

                // Loss condition
                const r = Math.sqrt(p.x * p.x + p.y * p.y);
                if (r < sim.lossLow * sim.ringRadius || r > sim.lossHigh * sim.ringRadius) {
                    p.alive = false;
                }

                // Trail recording
                p.trailCounter++;
                if (p.trailCounter >= sim.trailAddEvery) {
                    p.trailCounter = 0;
                    p.trail.push([p.x, p.y]);
                    if (p.trail.length > sim.maxTrailPoints) p.trail.shift();
                }
            }
        }
    }

    // ─── Update Visuals ───
    renderer.updateParticles(beam, sim.ringRadius);
    if (sim.drawTrails) {
        renderer.updateTrails(beam, sim.ringRadius);
    } else {
        // Hide all trail lines when trails are off
        renderer.trailLines.forEach(l => l.geometry.setDrawRange(0, 0));
    }

    // Paused overlay
    const pausedOverlay = document.getElementById('paused-overlay');
    if (pausedOverlay) {
        pausedOverlay.classList.toggle('visible', sim.paused);
    }

    // Stats
    const alive = beam.filter(p => p.alive);
    let meanE = 0, meanR = 0, meanP = 0, maxTurns = 0;
    if (alive.length > 0) {
        alive.forEach(p => {
            meanE += Math.log10(p.energyEv + 1);
            meanR += Math.sqrt(p.x * p.x + p.y * p.y);
            meanP += p.p;
            if (p.turns > maxTurns) maxTurns = p.turns;
        });
        meanE /= alive.length;
        meanR /= alive.length;
        meanP /= alive.length;
    }

    // Dashboard graphs
    dashboard.push('energy', meanE);
    dashboard.push('radius', meanR);
    dashboard.push('bz', sim.Bz);
    dashboard.push('momentum', meanP);
    dashboard.render();

    // Stats display
    const meanEeV = alive.length > 0 ? alive.reduce((s, p) => s + p.energyEv, 0) / alive.length : 0;
    controls.updateStats({
        alive: alive.length,
        total: beam.length,
        Bz: sim.Bz,
        meanR,
        meanE: meanEeV,
        t: simTime,
        maxTurns,
        fps: currentFps,
    });

    // Viewport HUD — always visible
    const hudTurns = document.getElementById('hud-turns');
    const hudEnergy = document.getElementById('hud-energy');
    const hudAlive = document.getElementById('hud-alive');
    const hudTime = document.getElementById('hud-time');
    if (hudTurns) hudTurns.textContent = maxTurns;
    if (hudEnergy) hudEnergy.textContent = meanEeV > 1e6 ? (meanEeV / 1e6).toFixed(1) + ' MeV' : meanEeV > 1e3 ? (meanEeV / 1e3).toFixed(1) + ' keV' : meanEeV.toFixed(0) + ' eV';
    if (hudAlive) hudAlive.textContent = `${alive.length}/${beam.length}`;
    if (hudTime) hudTime.textContent = simTime.toExponential(2) + 's';

    // Narration
    updateNarration({
        alive: alive.length,
        total: beam.length,
        Bz: sim.Bz,
        meanR,
        meanE: alive.length > 0 ? alive.reduce((s, p) => s + p.energyEv, 0) / alive.length : 0,
        maxTurns,
    });

    // Three.js render
    renderer.render(now * 0.001);
}

animate();
