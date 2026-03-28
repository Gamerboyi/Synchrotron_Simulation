# ⚛️ Synchrotron Ring Accelerator Simulator

> *"The universe has a beginning, but no end. — Infinite."*  
> — **Steins;Gate**, El Psy Kongroo

A **real-time particle accelerator simulation** featuring both a **Python/Pygame scientific simulator** and a **3D web-based interactive demo** (Three.js). Simulates a beam of charged particles (protons) orbiting inside a synchrotron ring with real electromagnetic physics.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Three.js](https://img.shields.io/badge/Three.js-r163-black?logo=threedotjs)
![Tests](https://img.shields.io/badge/Tests-15%20passing-brightgreen)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🌐 Live Web Demo

**▶ [Try it in your browser](https://synchrotron-simulation.vercel.app/)** — No installation needed!

The web version features a 3D torus ring with orbiting particles, real-time physics graphs, and a Steins;Gate-inspired CRT/retro-futuristic interface.

---

## 🎯 What This Simulates

| Physics Feature | Implementation |
|---|---|
| **Lorentz force** | F = q(E + v × B) — magnetic bending + electric acceleration |
| **RF cavity gap** | Sinusoidal E-field at +x gap — models real synchrotron acceleration |
| **Radial focusing** | Restoring force toward design orbit — mimics quadrupole lattice |
| **Relativistic dynamics** | γ = 1/√(1−v²/c²) — correct at all speeds |
| **RK4 integration** | 4th-order Runge-Kutta — O(h⁴) accuracy for orbit stability |
| **Beam dynamics** | 40 protons with Gaussian position/velocity spread |
| **B-ramp stabilizer** | Automatic Bz adjustment — mimics real synchrotron ramping |

---

## 🖥️ Two Versions

### 1. Web (Three.js 3D) — `web/`
- **3D torus ring** with glowing wireframe and bloom effects
- **Shader-based particles** with additive blending
- **Orbital camera** — drag to rotate, scroll to zoom
- **Glassmorphism control panel** — toggles, steppers, action buttons
- **Real-time Canvas graphs** — Energy, Radius, Bz, Momentum
- **CRT scanline overlay** — Steins;Gate retro-futuristic aesthetic

### 2. Desktop (Pygame) — `visualize.py`
- Full 2D simulation with particle trails and glow effects
- Interactive dashboard with live graphs
- Keyboard + mouse controls
- Screenshot capture

---

## 🚀 Quick Start

### Web Version (recommended)
```bash
# No installation needed — just serve the files
cd web
python -m http.server 8080
# Open http://localhost:8080 in your browser
```

### Python Version
```bash
pip install -r requirements.txt
python visualize.py
```

---

## 🧠 Physics Deep Dive

### Circular Motion in a Synchrotron
Particles travel in a circular path due to a magnetic field applied in the z-direction (Bz). The Lorentz force provides centripetal acceleration:

$$\vec{F} = q(\vec{E} + \vec{v} \times \vec{B})$$

### RF Cavity Acceleration
A real accelerator accelerates particles only inside a localized RF cavity, not everywhere. The cavity field:

$$E(t) = E_0 \sin(\omega t + \phi)$$

is applied tangentially at the +x gap position. The field is fixed in the lab frame (not particle-relative), which is the physically correct behavior.

### Relativistic Corrections

$$\gamma = \frac{1}{\sqrt{1 - v^2/c^2}}, \quad p = \gamma m v, \quad KE = (\gamma - 1)mc^2$$

### Numerical Integration
RK4 with correct time sub-stepping for the RF cavity:
- k1 evaluated at t
- k2, k3 evaluated at t + dt/2
- k4 evaluated at t + dt

This ensures the time-dependent RF field is sampled correctly across each integration step.

---

## 🏗️ Architecture

```
├── web/                    # 3D Web Simulation
│   ├── index.html          # Entry point (import maps for Three.js CDN)
│   ├── css/style.css       # Steins;Gate CRT theme
│   └── js/
│       ├── main.js         # Animation loop + beam management
│       ├── renderer.js     # Three.js scene (torus, particles, bloom)
│       ├── dashboard.js    # Canvas-based real-time graphs
│       ├── controls.js     # UI ↔ simulation state binding
│       ├── physics.js      # Lorentz, RF gap, focusing field
│       ├── integrator.js   # RK4 integrator
│       ├── particle.js     # Particle state class
│       └── constants.js    # Physical constants (CODATA 2018)
│
├── visualize.py            # Pygame 2D simulation
├── physics.py              # Physics engine (Python)
├── particle.py             # Particle class (Python)
├── integrators.py          # RK4 integrator (Python)
├── constants.py            # Physical constants (Python)
├── main.py                 # CLI simulation + matplotlib plots
│
├── tests/                  # 15 unit tests
│   ├── test_orbit_radius.py    # Cyclotron radius vs theory
│   ├── test_physics.py         # Gamma, RF, focusing, Lorentz
│   └── test_particle.py        # Energy conservation, momentum
│
├── .github/workflows/test.yml  # CI: pytest on Python 3.10-3.13
├── requirements.txt
├── CHANGELOG.md
└── LICENSE
```

---

## 🎮 Controls

### Keyboard (both versions)
| Key | Function |
|-----|----------|
| `SPACE` | Pause / Resume |
| `R` | Reset simulation |
| `G` | Toggle RF Kick |
| `F` | Toggle Focusing |
| `T` | Toggle Relativity |
| `B` | Toggle B-Ramp |

### Web Version
- **Orbit**: Left-click drag
- **Zoom**: Scroll wheel
- **Pan**: Right-click drag

---

## 🧪 Testing

```bash
# Run all 15 tests
pytest tests/ -v

# Tests cover:
# - Cyclotron radius matches r = mv/(qB)
# - Lorentz factor γ = 1 at rest, γ >> 1 near c
# - RF gap fires only at +x, respects halfwidth
# - Focusing field restores toward ring radius
# - Magnetic force perpendicular to velocity (no work done)
# - Energy conservation in pure magnetic field
# - Relativistic momentum p = γmv
```

---

## 📌 Technical Highlights

- **Correct RK4 implementation** — intermediate time evaluation for RF accuracy
- **Physics validation** — 15 tests verify against analytical solutions
- **Dual-platform** — Python for research, Web for interactive demonstration
- **No build step** — web version uses ES modules + CDN import maps
- **Responsive** — adapts from desktop to mobile layouts

---

## 📚 References

- Wiedemann, H. *"Particle Accelerator Physics"* (Springer, 4th ed.)
- Press et al. *"Numerical Recipes"* (Cambridge, 3rd ed.) — §17.1 RK4
- CODATA 2018 — Physical constants (NIST)

---

## 📜 License

MIT License — see [LICENSE](LICENSE)

---

*El Psy Kongroo.*
