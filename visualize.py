# visualize.py  (PHASE 8: Portfolio Mode Rendering + Glow + Energy Colors)
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
WIDTH, HEIGHT = 1500, 850
FPS = 60

BACKGROUND = (8, 8, 14)
RING_COLOR = (120, 140, 220)

TEXT_COLOR = (0, 51, 170)  # #3a style
GAP_COLOR = (100, 255, 180)

# -----------------------------
# Ring Parameters
# -----------------------------
RING_RADIUS_M = 5.0
SCALE = 80.0

DT = 1e-9
STEPS_PER_FRAME = 300

# -----------------------------
# Beam Parameters
# -----------------------------
NUM_PARTICLES = 40
SIGMA_POS = 0.02
SIGMA_VEL = 2e4

# -----------------------------
# Phase 6: Synchrotron B-Ramp
# -----------------------------
ENABLE_B_RAMP = True
Bz0 = 0.8
Bz_max = 6.0
B_GAIN = 0.7

# -----------------------------
# RF Kick
# -----------------------------
ENABLE_RF_KICK = True
GAP_HALFWIDTH = 0.10
E0 = 5e4
OMEGA = 2 * np.pi * 2e7
RF_PHI = 0.0

# -----------------------------
# Focusing
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
MAX_TRAIL_POINTS = 160
TRAIL_DRAW_EVERY = 2
DRAW_TRAILS = True

# -----------------------------
# HUD / Dashboard
# -----------------------------
HUD_W = 520
HUD_PAD = 16

GRAPH_BG = (14, 14, 24)
GRAPH_GRID = (40, 40, 64)
GRAPH_BORDER = (90, 90, 140)

GRAPH_LINE = (240, 240, 240)
SCATTER_COLOR = (255, 180, 180)

HISTORY_LEN = 240

GRAPH_W = HUD_W - 2 * HUD_PAD
GRAPH_H = 120
PHASE_H = 170

# -----------------------------
# Glow / Visual style
# -----------------------------
GLOW_STRENGTH = 3
PARTICLE_RADIUS = 4

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

        # revolution tracking
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


def clamp(x, a, b):
    return max(a, min(b, x))


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
# Color mapping (energy -> RGB)
# -----------------------------
def energy_to_color(E, Emin, Emax):
    """
    Maps energy to a nice gradient:
    low = bluish
    mid = purple
    high = hot pink/red
    """
    if Emax <= Emin + 1e-12:
        return (180, 180, 255)

    t = (E - Emin) / (Emax - Emin)
    t = clamp(t, 0.0, 1.0)

    # Smooth curve
    t2 = t * t

    # custom gradient
    r = int(80 + 175 * t2)
    g = int(80 + 50 * (1 - t))
    b = int(220 - 140 * t)

    return (clamp(r, 0, 255), clamp(g, 0, 255), clamp(b, 0, 255))


# -----------------------------
# Glow circle
# -----------------------------
def draw_glow_circle(surface, x, y, radius, color):
    """
    Draws glow by rendering multiple alpha circles.
    """
    for i in range(GLOW_STRENGTH, 0, -1):
        rr = radius + i * 3
        alpha = int(30 / i)
        glow = pygame.Surface((rr * 2, rr * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color, alpha), (rr, rr), rr)
        surface.blit(glow, (x - rr, y - rr))


# -----------------------------
# Fading trail draw
# -----------------------------
def draw_fading_trail(surface, pts, color):
    """
    pts: list of screen points
    draw as fading alpha segments
    """
    if len(pts) < 3:
        return

    n = len(pts)
    for i in range(1, n):
        a = int(180 * (i / n))
        if a < 5:
            continue
        c = (color[0], color[1], color[2], a)

        seg = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.line(seg, c, pts[i - 1], pts[i], 2)
        surface.blit(seg, (0, 0))


# -----------------------------
# Graph drawing
# -----------------------------
def draw_graph(surface, x, y, w, h, values, label, unit=""):
    pygame.draw.rect(surface, GRAPH_BG, (x, y, w, h), border_radius=12)
    pygame.draw.rect(surface, GRAPH_BORDER, (x, y, w, h), 2, border_radius=12)

    for i in range(1, 5):
        gx = x + int(i * w / 5)
        pygame.draw.line(surface, GRAPH_GRID, (gx, y + 8), (gx, y + h - 8), 1)

    for i in range(1, 4):
        gy = y + int(i * h / 4)
        pygame.draw.line(surface, GRAPH_GRID, (x + 8, gy), (x + w - 8, gy), 1)

    if len(values) < 2:
        return

    vmin = float(min(values))
    vmax = float(max(values))
    if abs(vmax - vmin) < 1e-12:
        vmax = vmin + 1.0

    font = pygame.font.SysFont("consolas", 16)
    txt = font.render(f"{label}", True, TEXT_COLOR)
    surface.blit(txt, (x + 12, y + 8))

    font2 = pygame.font.SysFont("consolas", 14)
    tmin = font2.render(f"{vmin:.3g}{unit}", True, (160, 160, 190))
    tmax = font2.render(f"{vmax:.3g}{unit}", True, (160, 160, 190))
    surface.blit(tmax, (x + w - tmax.get_width() - 12, y + 8))
    surface.blit(tmin, (x + w - tmin.get_width() - 12, y + h - 22))

    pts = []
    n = len(values)

    for i, v in enumerate(values):
        px = x + int((i / (n - 1)) * (w - 24)) + 12
        norm = (v - vmin) / (vmax - vmin)
        py = y + h - 12 - int(norm * (h - 24))
        pts.append((px, py))

    pygame.draw.lines(surface, GRAPH_LINE, False, pts, 2)


def draw_phase_space(surface, x, y, w, h, xs, ps, label_x="x", label_p="px"):
    pygame.draw.rect(surface, GRAPH_BG, (x, y, w, h), border_radius=12)
    pygame.draw.rect(surface, GRAPH_BORDER, (x, y, w, h), 2, border_radius=12)

    for i in range(1, 5):
        gx = x + int(i * w / 5)
        pygame.draw.line(surface, GRAPH_GRID, (gx, y + 8), (gx, y + h - 8), 1)

    for i in range(1, 4):
        gy = y + int(i * h / 4)
        pygame.draw.line(surface, GRAPH_GRID, (x + 8, gy), (x + w - 8, gy), 1)

    font = pygame.font.SysFont("consolas", 16)
    txt = font.render(f"Phase Space: {label_x} vs {label_p}", True, TEXT_COLOR)
    surface.blit(txt, (x + 12, y + 8))

    if len(xs) < 2:
        return

    xmin, xmax = float(min(xs)), float(max(xs))
    pmin, pmax = float(min(ps)), float(max(ps))

    if abs(xmax - xmin) < 1e-15:
        xmax = xmin + 1e-3
    if abs(pmax - pmin) < 1e-15:
        pmax = pmin + 1e-3

    xpad = 0.15 * (xmax - xmin)
    ppad = 0.15 * (pmax - pmin)

    xmin -= xpad
    xmax += xpad
    pmin -= ppad
    pmax += ppad

    for xi, pi in zip(xs, ps):
        px = x + 12 + int((xi - xmin) / (xmax - xmin) * (w - 24))
        py = y + h - 12 - int((pi - pmin) / (pmax - pmin) * (h - 24))
        pygame.draw.circle(surface, SCATTER_COLOR, (px, py), 2)


# -----------------------------
# Main
# -----------------------------
def main():
    global SCALE, STEPS_PER_FRAME
    global ENABLE_RF_KICK, ENABLE_FOCUSING, RELATIVISTIC, ENABLE_B_RAMP

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Ring Accelerator Simulator (PHASE 8: Portfolio Mode)")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("consolas", 18)

    cx = (WIDTH - HUD_W) // 2
    cy = HEIGHT // 2

    beam = create_beam()
    paused = False

    t = 0.0
    alive_timer_real = 0.0
    all_dead_time_real = None

    Bz = Bz0

    # histories
    hist_energy = []
    hist_rmean = []
    hist_alive = []
    hist_turns = []
    hist_Bz = []

    def reset_sim():
        nonlocal beam, t, alive_timer_real, all_dead_time_real, Bz
        nonlocal hist_energy, hist_rmean, hist_alive, hist_turns, hist_Bz
        beam = create_beam()
        t = 0.0
        alive_timer_real = 0.0
        all_dead_time_real = None
        Bz = Bz0

        hist_energy = []
        hist_rmean = []
        hist_alive = []
        hist_turns = []
        hist_Bz = []

    while True:
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

                if event.key == pygame.K_g:
                    ENABLE_RF_KICK = not ENABLE_RF_KICK

                if event.key == pygame.K_f:
                    ENABLE_FOCUSING = not ENABLE_FOCUSING

                if event.key == pygame.K_t:
                    RELATIVISTIC = not RELATIVISTIC

                if event.key == pygame.K_b:
                    ENABLE_B_RAMP = not ENABLE_B_RAMP

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

                        enable_rf_kick=ENABLE_RF_KICK,
                        gap_halfwidth=GAP_HALFWIDTH,
                        E0=E0,
                        omega=OMEGA,
                        t=t,
                        rf_phi=RF_PHI,

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

            alive_particles = [p for p in beam if p.alive]

            # Synchrotron B ramp feedback
            if ENABLE_B_RAMP and alive_particles:
                radii = [np.sqrt(p.x * p.x + p.y * p.y) for p in alive_particles]
                r_mean = float(np.mean(radii))

                err = (r_mean - RING_RADIUS_M) / RING_RADIUS_M
                Bz = Bz * (1.0 + B_GAIN * err)
                Bz = clamp(Bz, 0.1, Bz_max)

        # -----------------------------
        # Render
        # -----------------------------
        screen.fill(BACKGROUND)

        # ring
        pygame.draw.circle(
            screen,
            RING_COLOR,
            (cx, cy),
            int(RING_RADIUS_M * SCALE),
            2
        )

        # RF gap
        gap_y = GAP_HALFWIDTH * SCALE
        gap_x = int(cx + RING_RADIUS_M * SCALE)
        pygame.draw.line(
            screen,
            GAP_COLOR,
            (gap_x, int(cy - gap_y)),
            (gap_x, int(cy + gap_y)),
            4
        )

        # particles for energy mapping
        alive_particles = [p for p in beam if p.alive]
        energies = [p.energy_ev for p in alive_particles]

        Emin = min(energies) if energies else 0.0
        Emax = max(energies) if energies else 1.0

        # trails + particles
        for p in beam:

            # Trails (fade)
            if DRAW_TRAILS and len(p.trail) > 4:
                pts = [world_to_screen(x, y, SCALE, cx, cy) for (x, y) in p.trail[::TRAIL_DRAW_EVERY]]
                draw_fading_trail(screen, pts, (150, 150, 170))

            px, py = world_to_screen(p.x, p.y, SCALE, cx, cy)

            if p.alive:
                col = energy_to_color(p.energy_ev, Emin, Emax)
                draw_glow_circle(screen, px, py, PARTICLE_RADIUS, col)
                pygame.draw.circle(screen, col, (px, py), PARTICLE_RADIUS)
            else:
                pygame.draw.circle(screen, (255, 60, 60), (px, py), 3)

        # -----------------------------
        # Stats
        # -----------------------------
        alive_count = len(alive_particles)

        mean_energy = float(np.mean(energies)) if energies else 0.0

        radii = [np.sqrt(p.x * p.x + p.y * p.y) for p in alive_particles]
        mean_r = float(np.mean(radii)) if radii else 0.0

        turns_alive = [getattr(p, "turns", 0) for p in alive_particles]
        mean_turns = float(np.mean(turns_alive)) if turns_alive else 0.0
        max_turns = int(np.max(turns_alive)) if turns_alive else 0

        # histories
        hist_energy.append(mean_energy)
        hist_rmean.append(mean_r)
        hist_alive.append(alive_count)
        hist_turns.append(mean_turns)
        hist_Bz.append(Bz)

        if len(hist_energy) > HISTORY_LEN:
            hist_energy.pop(0)
            hist_rmean.pop(0)
            hist_alive.pop(0)
            hist_turns.pop(0)
            hist_Bz.pop(0)

        # -----------------------------
        # HUD Left text
        # -----------------------------
        if all_dead_time_real is None:
            dead_line = "All dead at(real)=---"
        else:
            dead_line = f"All dead at(real)={all_dead_time_real:.2f} s"

        info_lines = [
            "PHASE 8: PORTFOLIO MODE (Glow + Energy Coloring + Diagnostics)",
            "SPACE=Pause | R=Reset | UP/DOWN=Speed | +/-=Zoom",
            "G=RF Kick | F=Focusing | T=Relativity | B=B-Ramp",
            f"Bz={Bz:.3f} T | B-Ramp={'ON' if ENABLE_B_RAMP else 'OFF'}",
            f"RF={'ON' if ENABLE_RF_KICK else 'OFF'} | Focus={'ON' if ENABLE_FOCUSING else 'OFF'}",
            f"Alive={alive_count}/{NUM_PARTICLES}",
            f"Mean r={mean_r:.4f} m | Turns mean={mean_turns:.2f} | max={max_turns}",
            f"Mean Energy={mean_energy:.3e} eV | Emin={Emin:.2e} | Emax={Emax:.2e}",
            f"Alive time(real)={alive_timer_real:.2f} s | {dead_line}",
        ]

        y_text = 10
        for line in info_lines:
            txt = font.render(line, True, TEXT_COLOR)
            screen.blit(txt, (10, y_text))
            y_text += 22

        # -----------------------------
        # Right Dashboard
        # -----------------------------
        hud_x = WIDTH - HUD_W
        pygame.draw.rect(screen, (10, 10, 18), (hud_x, 0, HUD_W, HEIGHT))
        pygame.draw.line(screen, (80, 80, 140), (hud_x, 0), (hud_x, HEIGHT), 2)

        gx = hud_x + HUD_PAD
        gy = 18

        draw_graph(screen, gx, gy, GRAPH_W, GRAPH_H, hist_energy, "Mean Energy", " eV")
        gy += GRAPH_H + 14

        draw_graph(screen, gx, gy, GRAPH_W, GRAPH_H, hist_rmean, "Mean Radius", " m")
        gy += GRAPH_H + 14

        draw_graph(screen, gx, gy, GRAPH_W, GRAPH_H, hist_Bz, "Bz Ramp", " T")
        gy += GRAPH_H + 14

        # Phase Space plots
        xs = [p.x - (RING_RADIUS_M) for p in alive_particles]
        pxs = [p.px for p in alive_particles]

        ys = [p.y for p in alive_particles]
        pys = [p.py for p in alive_particles]

        draw_phase_space(screen, gx, gy, GRAPH_W, PHASE_H, xs, pxs, "x-R", "px")
        gy += PHASE_H + 14

        draw_phase_space(screen, gx, gy, GRAPH_W, PHASE_H, ys, pys, "y", "py")

        pygame.display.flip()


if __name__ == "__main__":
    main()
