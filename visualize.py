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
TRAIL_COLOR = (170, 170, 170)
PARTICLE_COLOR = (255, 120, 120)
LOST_COLOR = (255, 50, 50)
TEXT_COLOR = (230, 230, 230)

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
SIGMA_POS = 0.02   # meters
SIGMA_VEL = 2e4    # m/s  (reduced to stabilize)

# -----------------------------
# Phase 3: RF Gap Settings
# -----------------------------
ENABLE_RF_GAP = True
GAP_HALFWIDTH = 0.10
E0 = 2e5           # Electric field strength
USE_RF = False     # keep false first (stable)
OMEGA = 0.0        # RF frequency (only used if USE_RF=True)

RELATIVISTIC = False

# Loss condition (relaxed)
LOSS_LOW = 0.75
LOSS_HIGH = 1.25


# -----------------------------
# Beam Initialization
# -----------------------------
def create_beam():
    beam = []

    # IMPORTANT FIX:
    # The formula v = qBr/m gives absurd values for protons at R=5m, B=1T.
    # We clamp to a safe non-relativistic orbit speed.
    v0 = 0.05 * C   # 5% of speed of light (stable for Phase 3)

    for _ in range(NUM_PARTICLES):
        x = RING_RADIUS_M + np.random.normal(0, SIGMA_POS)
        y = np.random.normal(0, SIGMA_POS)

        # Tangential velocity: at +x, tangential direction is +y
        vx = np.random.normal(0, SIGMA_VEL)
        vy = v0 + np.random.normal(0, SIGMA_VEL)

        p = Particle(x, y, vx, vy, PROTON_CHARGE, PROTON_MASS)
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


# -----------------------------
# Main Program
# -----------------------------
def main():
    global SCALE, STEPS_PER_FRAME

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Ring Accelerator Simulator (Phase 3: RF Gap Acceleration)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 18)

    cx, cy = WIDTH // 2, HEIGHT // 2

    beam = create_beam()
    paused = False

    t = 0.0

    def reset_sim():
        nonlocal beam, t
        beam = create_beam()
        t = 0.0

    while True:
        clock.tick(FPS)

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

                        # Phase 3
                        ring_radius=RING_RADIUS_M,
                        enable_rf_gap=ENABLE_RF_GAP,
                        gap_halfwidth=GAP_HALFWIDTH,
                        E0=E0,
                        use_rf=USE_RF,
                        omega=OMEGA,
                        t=t
                    )

                    # Loss condition
                    r = np.sqrt(p.x * p.x + p.y * p.y)
                    if r > RING_RADIUS_M * LOSS_HIGH or r < RING_RADIUS_M * LOSS_LOW:
                        p.alive = False

                    p.add_trail_point()

        # -----------------------------
        # Render
        # -----------------------------
        screen.fill(BACKGROUND)

        # Draw ring
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
        pygame.draw.line(screen, GAP_COLOR, (gap_x, int(cy - gap_y)), (gap_x, int(cy + gap_y)), 4)

        # Draw particles + trails
        for p in beam:

            if len(p.trail) > 2:
                pts = [world_to_screen(x, y, SCALE, cx, cy) for (x, y) in p.trail]
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

        info_lines = [
            "PHASE 3: Electric Field Gap Acceleration",
            "SPACE=Pause | R=Reset | UP/DOWN=Speed | +/-=Zoom",
            f"Bz={Bz:.2f} T | Gap={'ON' if ENABLE_RF_GAP else 'OFF'} | E0={E0:.2e} V/m",
            f"Alive={alive_count}/{NUM_PARTICLES} | Mean v={mean_speed:.3e} | Max v={max_speed:.3e}",
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
