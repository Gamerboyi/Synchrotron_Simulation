# visualize.py
import pygame
import sys
import numpy as np
from constants import PROTON_MASS, PROTON_CHARGE
from particle import Particle
from physics import derivatives_particle
from integrators import rk4_step_particle

# -----------------------------
# Settings
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
# Ring & Simulation params
# -----------------------------
RING_RADIUS_M = 5.0
SCALE = 80  # pixels per meter
DT = 1e-9
STEPS_PER_FRAME = 300
Bz = 1.0

# -----------------------------
# Beam params
# -----------------------------
NUM_PARTICLES = 50
SIGMA_POS = 0.02  # meters
SIGMA_VEL = 1e5   # m/s

def create_beam():
    beam = []
    for _ in range(NUM_PARTICLES):
        # start near the ring radius
        x = RING_RADIUS_M + np.random.normal(0, SIGMA_POS)
        y = np.random.normal(0, SIGMA_POS)
        vx = np.random.normal(0, SIGMA_VEL)
        vy = np.sqrt((Bz*PROTON_CHARGE*RING_RADIUS_M)/PROTON_MASS) + np.random.normal(0, SIGMA_VEL)
        p = Particle(x, y, vx, vy, PROTON_CHARGE, PROTON_MASS)
        beam.append(p)
    return beam

beam = create_beam()

# -----------------------------
# Utilities
# -----------------------------
def world_to_screen(x, y, scale, cx, cy):
    sx = int(cx + x * scale)
    sy = int(cy - y * scale)
    return sx, sy

# -----------------------------
# Main loop
# -----------------------------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Ring Accelerator Simulator")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 18)

cx, cy = WIDTH//2, HEIGHT//2
paused = False

def reset_sim():
    global beam
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
                STEPS_PER_FRAME = min(5000, STEPS_PER_FRAME + 100)
            if event.key == pygame.K_DOWN:
                STEPS_PER_FRAME = max(1, STEPS_PER_FRAME - 100)
            if event.key in [pygame.K_PLUS, pygame.K_EQUALS]:
                SCALE *= 1.1
            if event.key == pygame.K_MINUS:
                SCALE /= 1.1

    # -----------------------------
    # Physics update
    # -----------------------------
    if not paused:
        for _ in range(STEPS_PER_FRAME):
            for p in beam:
                if p.alive:
                    rk4_step_particle(p, DT, derivatives_particle, Bz=Bz)

                    # Check for beam loss
                    r = np.sqrt(p.x**2 + p.y**2)
                    if r > RING_RADIUS_M * 1.05:
                        p.alive = False

                    # Add trail point
                    p.add_trail_point()

    # -----------------------------
    # Render
    # -----------------------------
    screen.fill(BACKGROUND)

    # Draw ring
    pygame.draw.circle(screen, RING_COLOR, (cx, cy), int(RING_RADIUS_M*SCALE), 2)

    # Draw particles and trails
    for p in beam:
        # Trail
        if len(p.trail) > 2:
            pts = [world_to_screen(x, y, SCALE, cx, cy) for x, y in p.trail]
            pygame.draw.lines(screen, TRAIL_COLOR, False, pts, 2)
        # Particle
        color = PARTICLE_COLOR if p.alive else LOST_COLOR
        px, py = world_to_screen(p.x, p.y, SCALE, cx, cy)
        pygame.draw.circle(screen, color, (px, py), 5)

    # -----------------------------
    # HUD
    # -----------------------------
    alive_count = sum(p.alive for p in beam)
    speeds = [np.sqrt(p.vx**2 + p.vy**2) for p in beam if p.alive]
    mean_speed = np.mean(speeds) if speeds else 0.0

    info_lines = [
        "SPACE=Pause | R=Reset | UP/DOWN=Speed | +/-=Zoom",
        f"Bz={Bz:.2f} T | Particles Alive={alive_count} | Mean speed={mean_speed:.3e} m/s",
        f"Steps/frame={STEPS_PER_FRAME} | DT={DT:.1e} s"
    ]
    y_text = 10
    for line in info_lines:
        txt = font.render(line, True, TEXT_COLOR)
        screen.blit(txt, (10, y_text))
        y_text += 22

    pygame.display.flip()
