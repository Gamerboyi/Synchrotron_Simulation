````md
# ⚛️ Ring Particle Accelerator Simulator (Phase 10 Final)

A **real-time ring accelerator / synchrotron-style simulation** built in **Python + Pygame**, focused on both **physics accuracy** and **portfolio-grade visualization**.

This project simulates a beam of charged particles (protons) moving inside a circular accelerator ring, including:

- **Lorentz force motion**
- **Magnetic bending field (Bz)**
- **RF gap acceleration**
- **Focusing field**
- **Relativistic energy + momentum**
- **Multi-particle beam dynamics**
- **Lap-based trail system**
- **Mean graphs dashboard (Energy, Radius, Bz, Momentum)**

---

## 🎯 Why I Built This

Most accelerator simulations are either:
- too theoretical (no visuals)
- too visual (no real physics)

This project tries to combine both:
✅ physics-based simulation  
✅ smooth visualization  
✅ real-time control toggles  
  

---

## 🧠 What This Project Simulates (Concept)

### 1) Circular Motion in a Ring (Synchrotron)
Particles travel in a circular path due to a **magnetic field**:

- Magnetic field is applied in the **z-direction**: `Bz`
- Motion is simulated in **2D (x-y plane)**

The force is:
\[
\vec{F} = q(\vec{E} + \vec{v} \times \vec{B})
\]

---

### 2) RF Gap Acceleration (Energy Gain)
A real accelerator does not accelerate particles everywhere.  
Instead, it accelerates them only inside an **RF cavity gap**.

So in this simulation:

- The RF gap exists only at the **+x side**
- Only if the particle is inside the gap region:
  - `x > 0`
  - `|y| < gap_halfwidth`

Then we apply an electric field:

\[
E(t) = E_0 \sin(\omega t + \phi)
\]

This field is applied along the particle’s velocity direction (tangential kick).

---

### 3) Focusing Field (Beam Stability)
Particles naturally drift outward/inward due to numerical noise and acceleration.

To prevent beam loss, a **restoring radial focusing field** is applied:

- If particle radius differs from ring radius:
  - it experiences a restoring force inward/outward

This keeps the beam near the ring.

---

### 4) Relativistic Energy + Momentum
At high velocity, classical mechanics fails.

So this simulation supports **relativistic dynamics**:

\[
\gamma = \frac{1}{\sqrt{1-v^2/c^2}}
\]

Relativistic momentum:

\[
p = \gamma m v
\]

Energy is tracked in eV.

---

### 5) Beam Simulation (Multiple Particles)
Instead of simulating a single particle, the project simulates a **beam bunch**:

- 40 particles by default
- Small Gaussian spread in:
  - initial position
  - initial velocity

This helps visualize beam spread and stability.

---

## 🌀 Trail System (Lap-Based)

This project uses a **true lap trail system**:

- **White trail** = current lap
- **Green trail** = previous lap fading out

Each time a particle completes one revolution:
- its current trail becomes previous
- previous begins fading out

This gives a **hypnosis-like spiral feel** (lap-by-lap memory).

---

## 📊 Dashboard (Right Panel Graphs)

The simulation tracks and graphs these values live:

### ✅ Mean Energy
- plotted using log scale (so changes are visible)

### ✅ Mean Radius
- shows how stable the beam is around ring radius

### ✅ Magnetic Field Bz
- shows the B-ramp stabilizer effect

### ✅ Mean Momentum |p|
- shows energy growth + stability

---

## 🧲 B-Ramp Stabilizer

When enabled, the simulation automatically adjusts `Bz` to keep the beam near the ring radius:

- If mean radius drifts outward → increase Bz  
- If mean radius drifts inward → decrease Bz  

This mimics real synchrotron ramping logic.

---

## 🎮 Controls

### Keyboard Controls
| Key | Function |
|-----|----------|
| `SPACE` | Pause/Resume |
| `R` | Reset Simulation |
| `UP / DOWN` | Increase/Decrease Steps per Frame |
| `+ / -` | Zoom In / Zoom Out |
| `G` | Toggle RF Kick |
| `F` | Toggle Focusing |
| `T` | Toggle Relativity |
| `B` | Toggle B-Ramp |

---

## 🏗️ Project Structure

### `visualize.py`
Main Pygame simulation:
- rendering
- trails
- glow
- UI panels
- graphs
- input controls
- simulation loop

### `particle.py`
Particle class:
- stores state (x,y,vx,vy)
- stores energy, gamma, momentum
- updates derived physics values

### `physics.py`
Physics engine:
- Lorentz acceleration
- RF gap kick
- focusing field
- derivatives function for integrator

### `integrators.py`
Numerical integration:
- RK4 integrator for stable smooth motion

### `constants.py`
Physical constants:
- proton mass
- proton charge
- speed of light

---

## ⚙️ Performance Notes

This simulation uses:
- RK4 integration (high accuracy)
- many micro steps per frame

So the simulation stays stable even at high speed.

---

## 🚀 How to Run

### 1) Install Dependencies
```bash
pip install pygame numpy
````

### 2) Run the Project

```bash
python visualize.py
```

---

## 📌 Key Learning Outcomes

This project helped me learn:

* numerical integration (RK4)
* Lorentz force physics
* relativistic momentum/energy
* RF phase acceleration
* beam stability concepts
* real-time simulation performance
* visualization design for portfolios

---

## 🌟 Future Improvements (Planned / Open Ideas)

I am open to improvements and suggestions such as:

* proper accelerator lattice (drift + quads)
* quadrupole focusing instead of simple radial spring
* real RF phase stability bucket
* better beam injection and extraction
* full 3D visualization (Unity / Godot / Panda3D / OpenGL)
* GPU acceleration for larger beams (1000+ particles)
* interactive UI sliders and clickable buttons
* exporting graphs / simulation logs

---

## 🤝 Suggestions / Feedback (Open to Improvements)

This project is my **Phase 10 Final** and I’m treating it as the final portfolio version.
But I’m always open to:

* suggestions from others
* improvements in physics accuracy
* UI/UX ideas (buttons, sliders, better graphs)
* performance optimization
* making the ring look more realistic / 3D
* adding more real accelerator components (quadrupoles, drift spaces, lattice)

If you have any feedback or want to collaborate, feel free to contact me:

📩 **Email:** [itsvedantnautiyal@gmail.com](mailto:itsvedantnautiyal@gmail.com)

---

## ⭐ If You Like This Project

If you found this interesting, feel free to star the repo ⭐
It motivates me to build more physics + simulation projects.

```
```
