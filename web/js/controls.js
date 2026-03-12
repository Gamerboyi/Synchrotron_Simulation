// controls.js — UI controls ↔ simulation state binding
export class Controls {
    constructor(simState, onReset, onRespawn) {
        this.sim = simState;
        this.onReset = onReset;
        this.onRespawn = onRespawn;
        this._bindToggles();
        this._bindSteppers();
        this._bindActions();
        this._bindKeyboard();
        this._updateAllDisplays();
    }

    _bindToggles() {
        const toggles = [
            { id: 'toggle-rf',       attr: 'enableRfKick' },
            { id: 'toggle-focus',    attr: 'enableFocusing' },
            { id: 'toggle-rel',     attr: 'relativistic' },
            { id: 'toggle-bramp',   attr: 'enableBRamp' },
            { id: 'toggle-trails',  attr: 'drawTrails' },
            { id: 'toggle-glow',    attr: 'enableGlow' },
        ];

        toggles.forEach(({ id, attr }) => {
            const btn = document.getElementById(id);
            if (!btn) return;
            btn.addEventListener('click', () => {
                this.sim[attr] = !this.sim[attr];
                this._updateToggle(btn, this.sim[attr]);
            });
            this._updateToggle(btn, this.sim[attr]);
        });
    }

    _updateToggle(btn, isOn) {
        btn.classList.toggle('on', isOn);
        btn.classList.toggle('off', !isOn);
        const label = btn.dataset.label || '';
        btn.querySelector('.toggle-status').textContent = isOn ? 'ON' : 'OFF';
    }

    _bindSteppers() {
        const steppers = [
            {
                minusId: 'steps-minus', plusId: 'steps-plus', displayId: 'steps-val',
                get: () => this.sim.stepsPerFrame,
                set: (v) => { this.sim.stepsPerFrame = v; },
                min: 100, max: 3000, step: 100,
                format: (v) => v.toString(),
            },
            {
                minusId: 'bz-minus', plusId: 'bz-plus', displayId: 'bz-val',
                get: () => this.sim.Bz,
                set: (v) => { this.sim.Bz = v; },
                min: 0.01, max: 2.0, step: 0.005,
                format: (v) => v.toFixed(4) + ' T',
            },
            {
                minusId: 'e0-minus', plusId: 'e0-plus', displayId: 'e0-val',
                get: () => this.sim.E0,
                set: (v) => { this.sim.E0 = v; },
                min: 1e3, max: 5e5, step: 5000,
                format: (v) => (v / 1e3).toFixed(0) + ' kV',
            },
            {
                minusId: 'kf-minus', plusId: 'kf-plus', displayId: 'kf-val',
                get: () => this.sim.kFocus,
                set: (v) => { this.sim.kFocus = v; },
                min: 1e6, max: 5e8, step: 5e6,
                format: (v) => (v / 1e6).toFixed(0) + ' MN',
            },
        ];

        steppers.forEach(s => {
            const minus = document.getElementById(s.minusId);
            const plus = document.getElementById(s.plusId);
            const display = document.getElementById(s.displayId);
            if (!minus || !plus || !display) return;

            minus.addEventListener('click', () => {
                s.set(Math.max(s.min, s.get() - s.step));
                display.textContent = s.format(s.get());
            });
            plus.addEventListener('click', () => {
                s.set(Math.min(s.max, s.get() + s.step));
                display.textContent = s.format(s.get());
            });
            display.textContent = s.format(s.get());
        });

        this._stepperDefs = steppers;
    }

    _bindActions() {
        const pauseBtn = document.getElementById('btn-pause');
        const resetBtn = document.getElementById('btn-reset');
        const respawnBtn = document.getElementById('btn-respawn');

        if (pauseBtn) {
            pauseBtn.addEventListener('click', () => {
                this.sim.paused = !this.sim.paused;
                pauseBtn.textContent = this.sim.paused ? '▶ RUN' : '⏸ PAUSE';
                pauseBtn.classList.toggle('paused', this.sim.paused);
            });
        }
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.onReset());
        }
        if (respawnBtn) {
            respawnBtn.addEventListener('click', () => this.onRespawn());
        }
    }

    _bindKeyboard() {
        window.addEventListener('keydown', (e) => {
            // Don't process shortcuts while intro overlay is visible
            const intro = document.getElementById('intro-overlay');
            if (intro && !intro.classList.contains('hidden')) return;

            const key = e.key.toLowerCase();
            const pauseBtn = document.getElementById('btn-pause');

            switch(key) {
                case ' ':
                    e.preventDefault();
                    this.sim.paused = !this.sim.paused;
                    if (pauseBtn) {
                        pauseBtn.textContent = this.sim.paused ? '▶ RUN' : '⏸ PAUSE';
                        pauseBtn.classList.toggle('paused', this.sim.paused);
                    }
                    break;
                case 'r': this.onReset(); break;
                case 'n': this.onRespawn(); break;
                case 'g':
                    this.sim.enableRfKick = !this.sim.enableRfKick;
                    this._refreshToggles();
                    break;
                case 'f':
                    this.sim.enableFocusing = !this.sim.enableFocusing;
                    this._refreshToggles();
                    break;
                case 't':
                    this.sim.relativistic = !this.sim.relativistic;
                    this._refreshToggles();
                    break;
                case 'b':
                    this.sim.enableBRamp = !this.sim.enableBRamp;
                    this._refreshToggles();
                    break;
            }
        });
    }

    _refreshToggles() {
        const map = {
            'toggle-rf': 'enableRfKick',
            'toggle-focus': 'enableFocusing',
            'toggle-rel': 'relativistic',
            'toggle-bramp': 'enableBRamp',
            'toggle-trails': 'drawTrails',
            'toggle-glow': 'enableGlow',
        };
        Object.entries(map).forEach(([id, attr]) => {
            const btn = document.getElementById(id);
            if (btn) this._updateToggle(btn, this.sim[attr]);
        });
    }

    _updateAllDisplays() {
        this._refreshToggles();
        if (this._stepperDefs) {
            this._stepperDefs.forEach(s => {
                const display = document.getElementById(s.displayId);
                if (display) display.textContent = s.format(s.get());
            });
        }
    }

    updateStats(stats) {
        const els = {
            'stat-alive': `${stats.alive} / ${stats.total}`,
            'stat-bz': `${stats.Bz.toFixed(4)} T`,
            'stat-radius': `${stats.meanR.toFixed(4)} m`,
            'stat-energy': `${stats.meanE.toFixed(2)} eV`,
            'stat-time': `${stats.t.toExponential(3)} s`,
            'stat-turns': `${stats.maxTurns}`,
            'stat-fps': `${stats.fps}`,
        };
        Object.entries(els).forEach(([id, val]) => {
            const el = document.getElementById(id);
            if (el) el.textContent = val;
        });
    }
}
