# visualize.py
import pygame
import sys
import numpy as np

from constants import PROTON_MASS, PROTON_CHARGE
from particle import Particle
from physics import derivatives_particle
from integrators import rk4_step_particle

# -----------------------------
# Window Settings
# -----------------------------
WIDTH, HEIGHT = 1000, 800
FPS = 60

BACKGROUND = (10, 10, 18)
RING_COLOR = (100, 120, 180)
TRAIL_COLOR = (180, 180, 180)
PARTICLE_COLOR = (255, 120, 120)
LOST_COLOR = (255, 50, 50)
TEXT_COLOR = (230, 230, 230)

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
# Beam Parameters (UPDATED)
# -----------------------------
NUM_PARTICLES = 50

# Smaller spread = more stable beam
SIGMA_POS = 0.002   # meters (was 0.02)
SIGMA_VEL = 1e3     # m/s     (was 1e5)

# Trail length limit (prevents lag)
MAX_TRAIL = 200


# -----------------------------
# Beam Initialization
# -----------------------------
def create_beam():
    beam = []

    # Correct speed for circular orbit:
    # r = (m*v)/(q*B)  =>  v = (r*q*B)/m
    v0 = (RING_RADIUS_M * PROTON_CHARGE * Bz) / PROTON_MASS

    for _ in range(NUM_PARTICLES):
        # Start close to ring radius
        x = RING_RADIUS_M + np.random.normal(0, SIGMA_POS)
        y = np.random.normal(0, SIGMA_POS)

        # Velocity near perfect circular orbit
        vx = np.random.normal(0, SIGMA_VEL)
        vy = v0 + np.random.normal(0, SIGMA_VEL)

        p = Particle(x, y, vx, vy, PROTON_CHARGE, PROTON_MASS)

        # Start trail
        p.trail = []
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
    pygame.display.set_caption("2D Ring Accelerator Simulator (Beam + RK4)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 18)

    cx, cy = WIDTH // 2, HEIGHT // 2

    beam = create_beam()
    paused = False

    def reset_sim():
        nonlocal beam
        beam = create_beam()

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
                    STEPS_PER_FRAME = min(8000, STEPS_PER_FRAME + 100)

                if event.key == pygame.K_DOWN:
                    STEPS_PER_FRAME = max(1, STEPS_PER_FRAME - 100)

                if event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                    SCALE *= 1.1

                if event.key == pygame.K_MINUS:
                    SCALE /= 1.1

        # -----------------------------
        # Physics Update
        # -----------------------------
        if not paused:
            for _ in range(STEPS_PER_FRAME):
                for p in beam:
                    if not p.alive:
                        continue

                    rk4_step_particle(p, DT, derivatives_particle, Bz=Bz)

                    # Loss condition (UPDATED: wider band)
                    r = np.sqrt(p.x * p.x + p.y * p.y)
                    if r > RING_RADIUS_M * 1.30 or r < RING_RADIUS_M * 0.70:
                        p.alive = False

                    # Trail limit
                    p.add_trail_point()
                    if len(p.trail) > MAX_TRAIL:
                        p.trail.pop(0)

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

        # Draw particles + trails
        for p in beam:

            # Trail
            if len(p.trail) > 2:
                pts = [world_to_screen(x, y, SCALE, cx, cy) for (x, y) in p.trail]
                pygame.draw.lines(screen, TRAIL_COLOR, False, pts, 2)

            # Particle
            px, py = world_to_screen(p.x, p.y, SCALE, cx, cy)
            color = PARTICLE_COLOR if p.alive else LOST_COLOR
            pygame.draw.circle(screen, color, (px, py), 5)

        # -----------------------------
        # HUD
        # -----------------------------
        alive_count = sum(1 for p in beam if p.alive)
        speeds = [np.sqrt(p.vx * p.vx + p.vy * p.vy) for p in beam if p.alive]
        mean_speed = float(np.mean(speeds)) if speeds else 0.0

        info_lines = [
            "SPACE=Pause | R=Reset | UP/DOWN=Speed | +/-=Zoom",
            f"Bz={Bz:.2f} T | Alive={alive_count}/{NUM_PARTICLES} | Mean speed={mean_speed:.3e} m/s",
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
