# main.py
import numpy as np
import matplotlib.pyplot as plt
import csv
from particle import Particle
from integrators import rk4_step_particle
from physics import derivatives_particle
from constants import PROTON_MASS, PROTON_CHARGE

# -----------------------------
# Simulation parameters
# -----------------------------
DT = 1e-9
STEPS = 20000
Bz = 1.0
NUM_PARTICLES = 50
SIGMA_POS = 0.02  # m
SIGMA_VEL = 1e5   # m/s

# -----------------------------
# Beam initialization
# -----------------------------
def create_beam():
    """
    Creates a beam of NUM_PARTICLES protons with small random spread
    """
    beam = []
    for _ in range(NUM_PARTICLES):
        x = np.random.normal(0, SIGMA_POS)
        y = np.random.normal(0, SIGMA_POS)
        # Calculate initial velocity along y for circular motion
        vx = np.random.normal(0, SIGMA_VEL)
        vy_circular = np.sqrt((Bz*PROTON_CHARGE)/PROTON_MASS)
        vy = vy_circular + np.random.normal(0, SIGMA_VEL)
        beam.append(Particle(x, y, vx, vy, PROTON_CHARGE, PROTON_MASS))
    return beam

# -----------------------------
# Run simulation
# -----------------------------
def run_simulation():
    beam = create_beam()

    xs_all = [[] for _ in beam]
    ys_all = [[] for _ in beam]

    rms_widths = []
    mean_speeds = []
    alive_counts = []

    for step in range(STEPS):
        for i, p in enumerate(beam):
            if p.alive:
                # RK4 update for particle
                rk4_step_particle(p, DT, derivatives_particle, Bz=Bz)

                # Simple loss condition: if particle leaves radius > 0.1 m
                r = np.sqrt(p.x**2 + p.y**2)
                if r > 0.1:
                    p.alive = False

            # Store trajectory
            xs_all[i].append(p.x)
            ys_all[i].append(p.y)

        # Metrics
        alive_particles = [p for p in beam if p.alive]
        alive_counts.append(len(alive_particles))
        speeds = [np.sqrt(p.vx**2 + p.vy**2) for p in alive_particles]
        mean_speeds.append(np.mean(speeds) if speeds else 0.0)
        rms_widths.append(np.sqrt(np.mean([p.x**2 + p.y**2 for p in alive_particles])) if alive_particles else 0.0)

    return xs_all, ys_all, rms_widths, mean_speeds, alive_counts

# -----------------------------
# Plot results
# -----------------------------
if __name__ == "__main__":
    xs_all, ys_all, rms_widths, mean_speeds, alive_counts = run_simulation()

    # -----------------------------
    # Orbit plot
    # -----------------------------
    plt.figure(figsize=(7,7))
    for xs, ys in zip(xs_all, ys_all):
        plt.plot(xs, ys)
    plt.xlabel("x (m)")
    plt.ylabel("y (m)")
    plt.title("Beam Orbits (2D RK4)")
    plt.axis("equal")
    plt.grid(True)
    plt.show()

    # -----------------------------
    # Beam metrics
    # -----------------------------
    plt.figure(figsize=(10,5))
    plt.plot(rms_widths, label="RMS width")
    plt.plot(mean_speeds, label="Mean speed")
    plt.plot(alive_counts, label="Alive particles")
    plt.xlabel("Time step")
    plt.ylabel("Metric")
    plt.title("Beam Metrics over Time")
    plt.legend()
    plt.grid(True)
    plt.show()

    # -----------------------------
    # Optional CSV export
    # -----------------------------
    with open("beam_data.csv", "w", newline="") as f:
        writer = csv.writer(f)
        header = ["Step"] + [f"x{i}" for i in range(NUM_PARTICLES)] + [f"y{i}" for i in range(NUM_PARTICLES)]
        writer.writerow(header)
        for step in range(STEPS):
            row = [step]
            row += [xs_all[i][step] for i in range(NUM_PARTICLES)]
            row += [ys_all[i][step] for i in range(NUM_PARTICLES)]
            writer.writerow(row)
