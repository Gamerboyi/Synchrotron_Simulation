# visualize.py
import pygame
import sys
import numpy as np

from constants import PROTON_MASS, PROTON_CHARGE, C
from particle import Particle
from physics import derivatives_particle
from integrators import rk4_step_particle

# -----------------------------
# Window Settings
# -----------------------------
WIDTH, HEIGHT = 1100, 850
FPS = 60

BACKGROUND = (10, 10, 18)
RING_COLOR = (100, 120, 180)

# Trail / particle colors
TRAIL_COLOR = (170, 170, 170)
PARTICLE_COLOR = (255, 120, 120)
LOST_COLOR = (255, 50, 50)

# TEXT COLOR = #3a (closest correct RGB)
TEXT_COLOR = (0, 51, 170)

GAP_COLOR = (100, 255, 180)

# -----------------------------
# Physics / Ring Parameters
# -----------------------------
RING_RADIUS_M = 5.0
Bz = 1.0

# Scaling: pixels per meter
SCALE = 80.0

# Time step
DT = 1e-9

# Simulation speed
STEPS_PER_FRAME = 300

# -----------------------------
# Beam Parameters
# -----------------------------
NUM_PARTICLES = 40
SIGMA_POS = 0.02
SIGMA_VEL = 2e4

# -----------------------------
# Phase 5: RF Kick Settings (NEW)
# -----------------------------
ENABLE_RF_KICK = True
GAP_HALFWIDTH = 0.10
E0 = 5e4

# RF frequency
# (this is not real-world exact, but visually stable)
OMEGA = 2 * np.pi * 2e7  # 20 MHz

# RF phase (0 = sin wave starts at 0)
RF_PHI = 0.0

# -----------------------------
# Phase 4: Focusing Settings
# -----------------------------
ENABLE_FOCUSING = True
K_FOCUS = 5e7

# -----------------------------
# Relativity
# -----------------------------
RELATIVISTIC = True

# -----------------------------
# Loss condition
# -----------------------------
LOSS_LOW = 0.65
LOSS_HIGH = 1.35

# -----------------------------
# Trail settings
# -----------------------------
MAX_TRAIL_POINTS = 140
DRAW_TRAILS = True
TRAIL_DRAW_EVERY = 2


# -----------------------------
# Beam Initialization
# -----------------------------
def create_beam():
    beam = []

    v0 = 0.05 * C

    for _ in range(NUM_PARTICLES):
        x = RING_RADIUS_M + np.random.normal(0, SIGMA_POS)
        y = np.random.normal(0, SIGMA_POS)

        vx = np.random.normal(0, SIGMA_VEL)
        vy = v0 + np.random.normal(0, SIGMA_VEL)

        p = Particle(x, y, vx, vy, PROTON_CHARGE, PROTON_MASS)

        # ---- revolution tracking ----
        p.theta_prev = np.arctan2(p.y, p.x)
        p.theta_accum = 0.0
        p.turns = 0

        p.add_trail_point()
        beam.append(p)

    return beam


# -----------------------------
# Utility
# -----------------------------
def world_to_screen(x, y, scale, cx, cy):
    sx = int(cx + x * scale)
    sy = int(cy - y * scale)
    return sx, sy


def update_revolution_counter(p):
    theta_now = np.arctan2(p.y, p.x)
    theta_prev = getattr(p, "theta_prev", theta_now)

    dtheta = theta_now - theta_prev

    if dtheta > np.pi:
        dtheta -= 2 * np.pi
    elif dtheta < -np.pi:
        dtheta += 2 * np.pi

    p.theta_accum += dtheta
    p.turns = int(abs(p.theta_accum) / (2 * np.pi))
    p.theta_prev = theta_now


# -----------------------------
# Main Program
# -----------------------------
def main():
    global SCALE, STEPS_PER_FRAME
    global ENABLE_RF_KICK, ENABLE_FOCUSING, RELATIVISTIC

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Ring Accelerator Simulator (Phase 5: Synchrotron RF Kick)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 18)

    cx, cy = WIDTH // 2, HEIGHT // 2

    beam = create_beam()
    paused = False

    # Simulation time (seconds) (physics time)
    t = 0.0

    # REAL alive-time (seconds)
    alive_timer_real = 0.0
    all_dead_time_real = None

    def reset_sim():
        nonlocal beam, t, alive_timer_real, all_dead_time_real
        beam = create_beam()
        t = 0.0
        alive_timer_real = 0.0
        all_dead_time_real = None

    while True:
        # IMPORTANT FIX:
        dt_real = clock.tick(FPS) / 1000.0

        # -----------------------------
        # Events
        # -----------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_SPACE:
                    paused = not paused

                if event.key == pygame.K_r:
                    reset_sim()

                if event.key == pygame.K_UP:
                    STEPS_PER_FRAME = min(12000, STEPS_PER_FRAME + 200)

                if event.key == pygame.K_DOWN:
                    STEPS_PER_FRAME = max(1, STEPS_PER_FRAME - 200)

                if event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                    SCALE *= 1.1

                if event.key == pygame.K_MINUS:
                    SCALE /= 1.1

                # Toggles
                if event.key == pygame.K_g:
                    ENABLE_RF_KICK = not ENABLE_RF_KICK

                if event.key == pygame.K_f:
                    ENABLE_FOCUSING = not ENABLE_FOCUSING

                if event.key == pygame.K_t:
                    RELATIVISTIC = not RELATIVISTIC

        # -----------------------------
        # Physics Update
        # -----------------------------
        if not paused:
            for _ in range(STEPS_PER_FRAME):
                t += DT

                for p in beam:
                    if not p.alive:
                        continue

                    rk4_step_particle(
                        p,
                        DT,
                        derivatives_particle,
                        Bz=Bz,
                        relativistic=RELATIVISTIC,

                        ring_radius=RING_RADIUS_M,

                        # Phase 5
                        enable_rf_kick=ENABLE_RF_KICK,
                        gap_halfwidth=GAP_HALFWIDTH,
                        E0=E0,
                        omega=OMEGA,
                        t=t,
                        rf_phi=RF_PHI,

                        # Phase 4
                        enable_focusing=ENABLE_FOCUSING,
                        k_focus=K_FOCUS
                    )

                    update_revolution_counter(p)

                    r = np.sqrt(p.x * p.x + p.y * p.y)
                    if r > RING_RADIUS_M * LOSS_HIGH or r < RING_RADIUS_M * LOSS_LOW:
                        p.alive = False

                    p.add_trail_point()
                    if len(p.trail) > MAX_TRAIL_POINTS:
                        p.trail.pop(0)

            alive_count_now = sum(1 for p in beam if p.alive)

            if alive_count_now > 0:
                alive_timer_real += dt_real
            else:
                if all_dead_time_real is None:
                    all_dead_time_real = alive_timer_real

        # -----------------------------
        # Render
        # -----------------------------
        screen.fill(BACKGROUND)

        pygame.draw.circle(
            screen,
            RING_COLOR,
            (cx, cy),
            int(RING_RADIUS_M * SCALE),
            2
        )

        # Draw gap region on +x side
        gap_y = GAP_HALFWIDTH * SCALE
        gap_x = int(cx + RING_RADIUS_M * SCALE)
        pygame.draw.line(
            screen,
            GAP_COLOR,
            (gap_x, int(cy - gap_y)),
            (gap_x, int(cy + gap_y)),
            4
        )

        for p in beam:
            if DRAW_TRAILS and len(p.trail) > 2:
                pts = [world_to_screen(x, y, SCALE, cx, cy) for (x, y) in p.trail[::TRAIL_DRAW_EVERY]]
                pygame.draw.lines(screen, TRAIL_COLOR, False, pts, 2)

            px, py = world_to_screen(p.x, p.y, SCALE, cx, cy)
            color = PARTICLE_COLOR if p.alive else LOST_COLOR
            pygame.draw.circle(screen, color, (px, py), 5)

        # -----------------------------
        # HUD
        # -----------------------------
        alive_count = sum(1 for p in beam if p.alive)

        speeds = [np.sqrt(p.vx * p.vx + p.vy * p.vy) for p in beam if p.alive]
        mean_speed = float(np.mean(speeds)) if speeds else 0.0
        max_speed = float(np.max(speeds)) if speeds else 0.0

        gammas = [getattr(p, "gamma", 1.0) for p in beam if p.alive]
        mean_gamma = float(np.mean(gammas)) if gammas else 1.0

        radii = [np.sqrt(p.x * p.x + p.y * p.y) for p in beam if p.alive]
        mean_r = float(np.mean(radii)) if radii else 0.0
        spread_r = float(np.std(radii)) if radii else 0.0

        turns_alive = [getattr(p, "turns", 0) for p in beam if p.alive]
        max_turns = int(np.max(turns_alive)) if turns_alive else 0
        mean_turns = float(np.mean(turns_alive)) if turns_alive else 0.0

        if all_dead_time_real is None:
            dead_line = "All dead at(real)=---"
        else:
            dead_line = f"All dead at(real)={all_dead_time_real:.2f} s"

        info_lines = [
            "PHASE 5: Synchrotron RF Kick + Revolutions Counter",
            "SPACE=Pause | R=Reset | UP/DOWN=Speed | +/-=Zoom",
            "G=Toggle RF Kick | F=Toggle Focusing | T=Toggle Relativity",
            f"Bz={Bz:.2f} T | RF-Kick={'ON' if ENABLE_RF_KICK else 'OFF'} | Focus={'ON' if ENABLE_FOCUSING else 'OFF'}",
            f"E0={E0:.2e} V/m | omega={OMEGA:.2e} rad/s | phi={RF_PHI:.2f} rad",
            f"k_focus={K_FOCUS:.2e} | Relativistic={'ON' if RELATIVISTIC else 'OFF'}",
            f"Alive={alive_count}/{NUM_PARTICLES}",
            f"Mean v={mean_speed:.3e} | Max v={max_speed:.3e} | Mean gamma={mean_gamma:.6f}",
            f"Mean r={mean_r:.4f} m | Orbit spread σr={spread_r:.4f} m",
            f"Sim time={t:.6f} s | Alive time(real)={alive_timer_real:.2f} s | {dead_line}",
            f"Turns: mean={mean_turns:.2f} | max={max_turns}",
            f"Steps/frame={STEPS_PER_FRAME} | DT={DT:.1e} s | Scale={SCALE:.1f} px/m",
        ]

        y_text = 10
        for line in info_lines:
            txt = font.render(line, True, TEXT_COLOR)
            screen.blit(txt, (10, y_text))
            y_text += 22

        pygame.display.flip()


if __name__ == "__main__":
    main()
