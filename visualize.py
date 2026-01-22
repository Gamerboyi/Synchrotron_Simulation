import pygame
import sys
import numpy as np
import datetime

from constants import PROTON_MASS, PROTON_CHARGE, C
from particle import Particle
from physics import derivatives_particle
from integrators import rk4_step_particle

# ============================================================
# WINDOW / LAYOUT
# ============================================================
WIDTH, HEIGHT = 1280, 760
FPS           = 60

HUD_W   = 500
DASH_H  = 215          # slightly taller to fit shortcut hints
HUD_PAD = 14
GRAPH_W = HUD_W - 2 * HUD_PAD
GRAPH_H = 100
HISTORY_LEN = 300

SIM_W = WIDTH - HUD_W
SIM_H = HEIGHT - DASH_H

# ============================================================
# COLORS
# ============================================================
BACKGROUND      = (8,   10,  12)
RING_COLOR      = (60,  140, 95)
TRAIL_CURR      = (230, 230, 230)
TRAIL_PREV      = (80,  255, 150)
HEAD_COLOR      = (255, 50,  50)
HEAD_GLOW_COLOR = (255, 70,  70)
PARTICLE_COLOR  = (100, 235, 150)
LOST_COLOR      = (255, 70,  70)
TEXT_COLOR      = (0,   210, 125)
GRAPH_BG        = (8,   11,  10)
GRAPH_GRID      = (25,  45,  35)
GRAPH_BORDER    = (0,   155, 90)
GRAPH_LINE      = (50,  255, 160)
GRAPH_FILL      = (0,   100, 60)

DASH_BG         = (10,  15,  12)
DASH_BORDER     = (0,   170, 100)

BTN_ON_BG       = (0,   130, 75)
BTN_ON_HOVER    = (0,   175, 100)
BTN_ON_TXT      = (210, 255, 215)
BTN_OFF_BG      = (38,  48,  42)
BTN_OFF_HOVER   = (55,  75,  60)
BTN_OFF_TXT     = (120, 145, 130)
BTN_ACT_BG      = (20,  55,  95)
BTN_ACT_HOVER   = (30,  85,  145)
BTN_ACT_TXT     = (170, 215, 255)
BTN_STEP_BG     = (28,  38,  32)
BTN_STEP_HOVER  = (48,  68,  52)
BTN_STEP_TXT    = (190, 225, 205)
BTN_BORDER_COL  = (0,   190, 110)
BTN_FLASH_COL   = (255, 255, 100)
KEY_HINT_COL    = (60,  130, 80)

# ============================================================
# PHYSICS CONSTANTS
# ============================================================
RING_RADIUS_M = 5.0
DT            = 1e-9
Bz0           = 0.8
Bz_max        = 6.0
B_GAIN        = 2.0
GAP_HALFWIDTH = 0.10
OMEGA         = 2 * np.pi * 2e7
RF_PHI        = 0.0
LOSS_LOW      = 0.92
LOSS_HIGH     = 1.08

MAX_POINTS_PER_LAP    = 400
TRAIL_ADD_EVERY_STEPS = 6
TRAIL_FADE_SPEED      = 1

GLOW_RADIUS = 5
GLOW_LAYERS = 4
GLOW_ALPHA  = 90

NUM_PARTICLES = 40
SIGMA_POS     = 0.02
SIGMA_VEL     = 2e4

# ============================================================
# SIM STATE
# NOTE: enable_focusing = False by default so individual
#       particle orbits are visible from the start.
# ============================================================
class SimState:
    def __init__(self):
        self.enable_rf_kick     = True
        self.enable_focusing    = False   # <-- OFF: shows individual orbits
        self.relativistic       = True
        self.enable_b_ramp      = True
        self.draw_trails        = True
        self.enable_glow        = True
        self.enable_spiral_wipe = True
        self.paused             = False
        self.steps_per_frame    = 1200
        self.scale              = 80.0
        self.E0                 = 5e4
        self.k_focus            = 5e7
        self.trail_thickness    = 1

sim = SimState()

# ============================================================
# KEYBOARD SHORTCUT MAP
# Every button action is bound here so both keyboard and
# mouse click call the exact same function.
# ============================================================
#  Key            Action description
#  ─────────────────────────────────────────────────────────
#  SPACE          Pause / Run
#  R              Reset
#  G              Toggle RF Kick
#  F              Toggle Focusing
#  T              Toggle Relativity
#  B              Toggle B-Ramp
#  L              Toggle Trails
#  O              Toggle Glow
#  UP / DOWN      Steps/frame  +100 / -100
#  = / -          Zoom  +5 / -5
#  [ / ]          Bz manual  -0.05 / +0.05
#  , / .          RF E0  -5kV / +5kV
#  ; / '          Focus K  -5MN / +5MN
#  9 / 0          Trail thickness  -1 / +1
#  K              Kill All particles
#  N              Respawn beam
#  S              Screenshot

# ============================================================
# HELPERS
# ============================================================
def clamp(x, a, b):
    return max(a, min(b, x))

def world_to_screen(x, y, cx, cy, scale):
    return int(cx + x * scale), int(cy - y * scale)

def update_revolution_counter(p):
    theta  = np.arctan2(p.y, p.x)
    dtheta = theta - p.theta_prev
    if dtheta >  np.pi: dtheta -= 2 * np.pi
    if dtheta < -np.pi: dtheta += 2 * np.pi
    p.theta_accum += dtheta
    turns = int(abs(p.theta_accum) / (2 * np.pi))
    p.just_completed_lap = (turns != p.turns)
    p.turns      = turns
    p.theta_prev = theta

def draw_glow(surface, x, y, color):
    if not sim.enable_glow:
        return
    r  = GLOW_RADIUS
    s  = pygame.Surface((r * 6, r * 6), pygame.SRCALPHA)
    cc = r * 3
    for i in range(GLOW_LAYERS, 0, -1):
        pygame.draw.circle(s, (*color, int(GLOW_ALPHA * i / GLOW_LAYERS)),
                           (cc, cc), int(r * i / GLOW_LAYERS))
    surface.blit(s, (x - cc, y - cc))

def draw_graph(surface, x, y, w, h, values, label, font_lbl, font_val):
    pygame.draw.rect(surface, GRAPH_BG, (x, y, w, h), border_radius=8)
    pygame.draw.rect(surface, GRAPH_BORDER, (x, y, w, h), 2, border_radius=8)
    for i in range(1, 5):
        gx = x + int(i * w / 5)
        pygame.draw.line(surface, GRAPH_GRID, (gx, y+6), (gx, y+h-6), 1)
    for i in range(1, 3):
        gy = y + int(i * h / 3)
        pygame.draw.line(surface, GRAPH_GRID, (x+6, gy), (x+w-6, gy), 1)
    surface.blit(font_lbl.render(label, True, TEXT_COLOR), (x+8, y+4))
    if len(values) < 2:
        return
    vmin = float(min(values))
    vmax = float(max(values))
    span = vmax - vmin
    if span < 1e-12:
        span = max(abs(vmin) * 0.001, 1e-6)
        vmax = vmin + span
    pts = []
    for i, v in enumerate(values):
        px   = x + 8 + int(i / (len(values)-1) * (w-16))
        norm = (v - vmin) / span
        py   = y + h - 8 - int(norm * (h-16))
        pts.append((px, clamp(py, y+4, y+h-4)))
    if len(pts) >= 2:
        poly = [pts[0]] + pts + [(pts[-1][0], y+h-4), (pts[0][0], y+h-4)]
        fs   = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.polygon(fs, (*GRAPH_FILL, 60), [(p[0]-x, p[1]-y) for p in poly])
        surface.blit(fs, (x, y))
    pygame.draw.lines(surface, GRAPH_LINE, False, pts, 2)
    surface.blit(font_val.render(f"{values[-1]:.4g}", True, (220,255,220)), (x+w-82, y+4))
    surface.blit(font_val.render(f"▲{vmax:.4g}", True, (100,180,120)), (x+8,  y+18))
    surface.blit(font_val.render(f"▼{vmin:.4g}", True, (80, 140,100)), (x+8,  y+h-18))

# ============================================================
# CREATE BEAM
# ============================================================
def create_beam():
    beam = []
    v0   = 0.05 * C
    for _ in range(NUM_PARTICLES):
        theta  = np.random.normal(0, 0.06)
        r      = RING_RADIUS_M + np.random.normal(0, SIGMA_POS)
        x, y   = r * np.cos(theta), r * np.sin(theta)
        tx, ty = -np.sin(theta), np.cos(theta)
        speed  = v0 + np.random.normal(0, SIGMA_VEL)
        p = Particle(x, y, speed*tx, speed*ty, PROTON_CHARGE, PROTON_MASS)
        p.update_energy(relativistic=sim.relativistic)
        p.theta_prev          = np.arctan2(y, x)
        p.theta_accum         = 0.0
        p.turns               = 0
        p.just_completed_lap  = False
        p.trail_current       = [(x, y)]
        p.trail_prev          = []
        p.trail_prev_alpha    = 0
        p.trail_counter       = 0
        p.prev_lap_wipe_angle = 0.0
        beam.append(p)
    return beam

# ============================================================
# BUTTON CLASS
# ============================================================
class Button:
    """
    kind: 'toggle' | 'action' | 'step'
    kw for toggle : attr (str on sim), prefix (str), shortcut (str, shown as hint)
    kw for action : label (str), callback (fn(**ctx)), shortcut (str)
    kw for step   : delta_fn (fn()|None), label_fn (fn()->str), shortcut_minus/plus (str)
    """
    def __init__(self, rect, kind, **kw):
        self.rect   = pygame.Rect(rect)
        self.kind   = kind
        self.kw     = kw
        self._flash = 0

    def label(self):
        if self.kind == 'toggle':
            val = getattr(sim, self.kw['attr'])
            return f"{self.kw['prefix']}: {'ON' if val else 'OFF'}"
        if self.kind == 'action':
            return self.kw['label']
        if self.kind == 'step':
            return self.kw['label_fn']()
        return ''

    def shortcut_hint(self):
        return self.kw.get('shortcut', '')

    def is_on(self):
        if self.kind == 'toggle':
            return bool(getattr(sim, self.kw['attr']))
        return True

    def activate(self, **ctx):
        self._flash = 6
        if self.kind == 'toggle':
            setattr(sim, self.kw['attr'], not getattr(sim, self.kw['attr']))
        elif self.kind == 'action':
            self.kw['callback'](**ctx)
        elif self.kind == 'step':
            fn = self.kw['delta_fn']
            if fn is not None:
                fn()

    def handle_event(self, event, **ctx):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.activate(**ctx)
                return True
        return False

    def draw(self, surface, mouse_pos, font, font_hint):
        hover = self.rect.collidepoint(mouse_pos)
        if self._flash > 0:
            bg, tc = BTN_FLASH_COL, (20, 20, 20)
            self._flash -= 1
        elif self.kind == 'toggle':
            bg = (BTN_ON_HOVER if hover else BTN_ON_BG) if self.is_on() \
              else (BTN_OFF_HOVER if hover else BTN_OFF_BG)
            tc = BTN_ON_TXT if self.is_on() else BTN_OFF_TXT
        elif self.kind == 'action':
            bg = BTN_ACT_HOVER if hover else BTN_ACT_BG
            tc = BTN_ACT_TXT
        else:
            bg = BTN_STEP_HOVER if hover else BTN_STEP_BG
            tc = BTN_STEP_TXT

        pygame.draw.rect(surface, bg, self.rect, border_radius=6)
        pygame.draw.rect(surface, BTN_BORDER_COL, self.rect, 1, border_radius=6)

        # Main label — centered vertically (shift up a bit if hint below)
        hint = self.shortcut_hint()
        if hint:
            ts  = font.render(self.label(), True, tc)
            tr  = ts.get_rect(centerx=self.rect.centerx,
                              centery=self.rect.centery - 5)
            surface.blit(ts, tr)
            hs  = font_hint.render(f"[{hint}]", True, KEY_HINT_COL)
            hr  = hs.get_rect(centerx=self.rect.centerx,
                              top=tr.bottom + 1)
            surface.blit(hs, hr)
        else:
            ts = font.render(self.label(), True, tc)
            surface.blit(ts, ts.get_rect(center=self.rect.center))

# ============================================================
# BUILD BUTTONS
# ============================================================
def build_buttons(beam_ref, Bz_ref, loss_ref, hist_refs):
    PAD = 8
    BH  = 42    # taller to fit hint text
    BSM = 34
    buttons = []

    # ── ROW 1: toggles ──────────────────────────────────────
    R1Y = SIM_H + 8
    toggles = [
        ('enable_rf_kick',  'RF Kick',    'G'),
        ('enable_focusing', 'Focusing',   'F'),
        ('relativistic',    'Relativity', 'T'),
        ('enable_b_ramp',   'B-Ramp',     'B'),
        ('draw_trails',     'Trails',     'L'),
        ('enable_glow',     'Glow',       'O'),
    ]
    NT = len(toggles)
    TW = (SIM_W - (NT+1)*PAD) // NT
    for i, (attr, prefix, sc) in enumerate(toggles):
        x = PAD + i*(TW+PAD)
        buttons.append(Button(
            (x, R1Y, TW, BH), 'toggle',
            attr=attr, prefix=prefix, shortcut=sc))

    # ── ROW 2: steppers ─────────────────────────────────────
    R2Y = SIM_H + 60
    SW, VW = 28, 88
    GW = SW + VW + SW + 4

    steppers = [
        ("Steps/frame", "UP/DN",
         lambda: setattr(sim,'steps_per_frame', max(100,  sim.steps_per_frame-100)),
         lambda: setattr(sim,'steps_per_frame', min(3000, sim.steps_per_frame+100)),
         lambda: f"{sim.steps_per_frame}"),
        ("Zoom", "= / -",
         lambda: setattr(sim,'scale', max(20.0,  sim.scale-5.0)),
         lambda: setattr(sim,'scale', min(200.0, sim.scale+5.0)),
         lambda: f"{sim.scale:.0f}x"),
        ("Bz manual", "[ / ]",
         lambda: Bz_ref.__setitem__(0, clamp(Bz_ref[0]-0.05, Bz0, Bz_max)),
         lambda: Bz_ref.__setitem__(0, clamp(Bz_ref[0]+0.05, Bz0, Bz_max)),
         lambda: f"{Bz_ref[0]:.3f}T"),
        ("RF  E0", ", / .",
         lambda: setattr(sim,'E0', max(1e3,  sim.E0-5000)),
         lambda: setattr(sim,'E0', min(5e5,  sim.E0+5000)),
         lambda: f"{sim.E0/1e3:.0f}kV"),
        ("Focus K", "; / '",
         lambda: setattr(sim,'k_focus', max(1e6, sim.k_focus-5e6)),
         lambda: setattr(sim,'k_focus', min(5e8, sim.k_focus+5e6)),
         lambda: f"{sim.k_focus/1e6:.0f}MN"),
        ("Trail px", "9 / 0",
         lambda: setattr(sim,'trail_thickness', max(1, sim.trail_thickness-1)),
         lambda: setattr(sim,'trail_thickness', min(4, sim.trail_thickness+1)),
         lambda: f"{sim.trail_thickness}px"),
    ]
    NG = len(steppers)
    SP = max(4, (SIM_W - NG*GW - 2*PAD) // max(NG-1, 1))

    for i, (hdr, sc, minus_fn, plus_fn, label_fn) in enumerate(steppers):
        gx  = PAD + i*(GW+SP)
        _lf = label_fn
        buttons.append(Button((gx,             R2Y, SW,  BSM), 'step',
            delta_fn=minus_fn, label_fn=lambda: '−'))
        buttons.append(Button((gx+SW+2,         R2Y, VW,  BSM), 'step',
            delta_fn=None, label_fn=_lf))
        buttons.append(Button((gx+SW+2+VW+2,    R2Y, SW,  BSM), 'step',
            delta_fn=plus_fn, label_fn=lambda: '+'))

    # ── ROW 3: actions ──────────────────────────────────────
    R3Y = SIM_H + 164

    def do_pause(**ctx):      sim.paused = not sim.paused
    def do_reset(**ctx):
        beam_ref[0] = create_beam(); Bz_ref[0] = Bz0
        loss_ref.clear(); [h.clear() for h in hist_refs]; sim.paused = False
    def do_kill(**ctx):
        for p in beam_ref[0]: p.alive = False
    def do_respawn(**ctx):
        beam_ref[0] = create_beam(); Bz_ref[0] = Bz0
    def do_screenshot(**ctx):
        ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"ring_accel_{ts}.png"
        pygame.image.save(ctx['screen'], name)
        print(f"[Screenshot] → {name}")

    actions = [
        ('Pause / Run',  do_pause,      'SPACE'),
        ('Reset',        do_reset,      'R'),
        ('Kill All',     do_kill,       'K'),
        ('Respawn Beam', do_respawn,    'N'),
        ('Screenshot',   do_screenshot, 'S'),
    ]
    NA = len(actions)
    AW = (SIM_W - (NA+1)*PAD) // NA
    for i, (lbl, cb, sc) in enumerate(actions):
        x = PAD + i*(AW+PAD)
        buttons.append(Button((x, R3Y, AW, BH), 'action',
            label=lbl, callback=cb, shortcut=sc))

    # return steppers metadata for header drawing
    return buttons, [(s[0], s[1]) for s in steppers], GW, SP

# ============================================================
# MAIN
# ============================================================
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Ring Accelerator — Control Dashboard")
    clock  = pygame.time.Clock()

    font       = pygame.font.SysFont("consolas", 15)
    font_small = pygame.font.SysFont("consolas", 14)
    font_graph = pygame.font.SysFont("consolas", 13)
    font_val   = pygame.font.SysFont("consolas", 12)
    font_hdr   = pygame.font.SysFont("consolas", 12)
    font_hint  = pygame.font.SysFont("consolas", 11)

    cx = SIM_W // 2
    cy = SIM_H // 2

    beam_ref  = [create_beam()]
    Bz_ref    = [Bz0]
    loss_fl   = []
    hist_E, hist_r, hist_Bz, hist_p = [], [], [], []
    hist_refs = [hist_E, hist_r, hist_Bz, hist_p]

    buttons, step_meta, GW, SP = build_buttons(beam_ref, Bz_ref, loss_fl, hist_refs)
    PAD = 8
    t   = 0.0

    # ── Keyboard action map (same functions as buttons) ──────
    # We define lambdas that mirror every button action so
    # keyboard shortcuts and buttons are perfectly in sync.
    def kb_reset():
        beam_ref[0] = create_beam(); Bz_ref[0] = Bz0
        loss_fl.clear(); [h.clear() for h in hist_refs]; sim.paused = False
    def kb_kill():
        for p in beam_ref[0]: p.alive = False
    def kb_respawn():
        beam_ref[0] = create_beam(); Bz_ref[0] = Bz0
    def kb_screenshot():
        ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"ring_accel_{ts}.png"
        pygame.image.save(screen, name)
        print(f"[Screenshot] → {name}")

    KEYMAP = {
        pygame.K_SPACE:      lambda: setattr(sim, 'paused', not sim.paused),
        pygame.K_r:          kb_reset,
        pygame.K_g:          lambda: setattr(sim,'enable_rf_kick',  not sim.enable_rf_kick),
        pygame.K_f:          lambda: setattr(sim,'enable_focusing', not sim.enable_focusing),
        pygame.K_t:          lambda: setattr(sim,'relativistic',    not sim.relativistic),
        pygame.K_b:          lambda: setattr(sim,'enable_b_ramp',   not sim.enable_b_ramp),
        pygame.K_l:          lambda: setattr(sim,'draw_trails',     not sim.draw_trails),
        pygame.K_o:          lambda: setattr(sim,'enable_glow',     not sim.enable_glow),
        # steps/frame
        pygame.K_UP:         lambda: setattr(sim,'steps_per_frame', min(3000, sim.steps_per_frame+100)),
        pygame.K_DOWN:       lambda: setattr(sim,'steps_per_frame', max(100,  sim.steps_per_frame-100)),
        # zoom
        pygame.K_EQUALS:     lambda: setattr(sim,'scale', min(200.0, sim.scale+5.0)),
        pygame.K_MINUS:      lambda: setattr(sim,'scale', max(20.0,  sim.scale-5.0)),
        # Bz manual
        pygame.K_LEFTBRACKET:  lambda: Bz_ref.__setitem__(0, clamp(Bz_ref[0]-0.05, Bz0, Bz_max)),
        pygame.K_RIGHTBRACKET: lambda: Bz_ref.__setitem__(0, clamp(Bz_ref[0]+0.05, Bz0, Bz_max)),
        # RF E0
        pygame.K_COMMA:      lambda: setattr(sim,'E0', max(1e3, sim.E0-5000)),
        pygame.K_PERIOD:     lambda: setattr(sim,'E0', min(5e5, sim.E0+5000)),
        # Focus K
        pygame.K_SEMICOLON:  lambda: setattr(sim,'k_focus', max(1e6, sim.k_focus-5e6)),
        pygame.K_QUOTE:      lambda: setattr(sim,'k_focus', min(5e8, sim.k_focus+5e6)),
        # trail thickness
        pygame.K_9:          lambda: setattr(sim,'trail_thickness', max(1, sim.trail_thickness-1)),
        pygame.K_0:          lambda: setattr(sim,'trail_thickness', min(4, sim.trail_thickness+1)),
        # actions
        pygame.K_k:          kb_kill,
        pygame.K_n:          kb_respawn,
        pygame.K_s:          kb_screenshot,
    }

    while True:
        clock.tick(FPS)
        beam      = beam_ref[0]
        Bz        = Bz_ref[0]
        mouse_pos = pygame.mouse.get_pos()

        # ── EVENTS ──────────────────────────────────────────
        ctx = dict(beam_ref=beam_ref, Bz_ref=Bz_ref,
                   loss_ref=loss_fl, hist_refs=hist_refs, screen=screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                fn = KEYMAP.get(event.key)
                if fn:
                    fn()
            for btn in buttons:
                btn.handle_event(event, **ctx)

        beam = beam_ref[0]
        Bz   = Bz_ref[0]

        # ── UPDATE ──────────────────────────────────────────
        if not sim.paused:
            alive = [p for p in beam if p.alive]

            if sim.enable_b_ramp and alive:
                mean_r = float(np.mean([np.hypot(p.x, p.y) for p in alive]))
                r_err  = (mean_r - RING_RADIUS_M) / RING_RADIUS_M
                Bz    += B_GAIN * r_err * Bz * DT * sim.steps_per_frame
                Bz     = clamp(Bz, Bz0, Bz_max)
                Bz_ref[0] = Bz

            for _ in range(sim.steps_per_frame):
                t += DT
                for p in beam:
                    if not p.alive:
                        continue
                    rk4_step_particle(
                        p, DT, derivatives_particle,
                        Bz=Bz, relativistic=sim.relativistic,
                        ring_radius=RING_RADIUS_M,
                        enable_rf_kick=sim.enable_rf_kick,
                        gap_halfwidth=GAP_HALFWIDTH,
                        E0=sim.E0, omega=OMEGA, t=t, rf_phi=RF_PHI,
                        enable_focusing=sim.enable_focusing,
                        k_focus=sim.k_focus,
                    )
                    p.update_energy(relativistic=sim.relativistic)
                    update_revolution_counter(p)

                    if p.just_completed_lap:
                        p.trail_prev       = p.trail_current[:]
                        p.trail_prev_alpha = 220
                        p.trail_current    = [(p.x, p.y)]

                    r = np.hypot(p.x, p.y)
                    if r < LOSS_LOW*RING_RADIUS_M or r > LOSS_HIGH*RING_RADIUS_M:
                        p.alive = False
                        sx, sy  = world_to_screen(p.x, p.y, cx, cy, sim.scale)
                        loss_fl.append([sx, sy, 18])

                    p.trail_counter += 1
                    if p.trail_counter >= TRAIL_ADD_EVERY_STEPS:
                        p.trail_counter = 0
                        p.trail_current.append((p.x, p.y))
                        if len(p.trail_current) > MAX_POINTS_PER_LAP:
                            p.trail_current.pop(0)

            for p in beam:
                if p.trail_prev_alpha > 0:
                    p.trail_prev_alpha = max(0, p.trail_prev_alpha - TRAIL_FADE_SPEED)
                    if p.trail_prev_alpha == 0:
                        p.trail_prev = []

            loss_fl[:] = [[x, y, f-1] for x, y, f in loss_fl if f > 1]

        # ── DRAW ────────────────────────────────────────────
        screen.fill(BACKGROUND)
        screen.set_clip(pygame.Rect(0, 0, SIM_W, SIM_H))

        # Ring
        ring_px = int(RING_RADIUS_M * sim.scale)
        pygame.draw.circle(screen, RING_COLOR, (cx, cy), ring_px, 2)

        # Gap marker
        gsx, gsy = world_to_screen(RING_RADIUS_M, 0, cx, cy, sim.scale)
        pygame.draw.circle(screen, (200, 255, 80), (gsx, gsy), 5)

        # Trails
        if sim.draw_trails:
            tl = pygame.Surface((SIM_W, SIM_H), pygame.SRCALPHA)
            tt = sim.trail_thickness
            for p in beam:
                if p.trail_prev and p.trail_prev_alpha > 0 and len(p.trail_prev) > 1:
                    pts = [world_to_screen(x, y, cx, cy, sim.scale)
                           for x, y in p.trail_prev]
                    pygame.draw.lines(tl, (*TRAIL_PREV, p.trail_prev_alpha),
                                      False, pts, 1)
                if len(p.trail_current) > 1:
                    pts = [world_to_screen(x, y, cx, cy, sim.scale)
                           for x, y in p.trail_current]
                    pygame.draw.lines(tl, (*TRAIL_CURR, 230),
                                      False, pts, tt)
            screen.blit(tl, (0, 0))

        # Loss flashes
        for fx, fy, ff in loss_fl:
            fs = pygame.Surface((22, 22), pygame.SRCALPHA)
            pygame.draw.circle(fs, (*LOST_COLOR, int(255*ff/18)), (11, 11), 10)
            screen.blit(fs, (fx-11, fy-11))

        # Particles
        alive = [p for p in beam if p.alive]
        if alive:
            hd = alive[0]
            hx, hy = world_to_screen(hd.x, hd.y, cx, cy, sim.scale)
            draw_glow(screen, hx, hy, HEAD_GLOW_COLOR)
            pygame.draw.circle(screen, HEAD_COLOR, (hx, hy), 6)
        for p in alive[1:]:
            sx, sy = world_to_screen(p.x, p.y, cx, cy, sim.scale)
            pygame.draw.circle(screen, PARTICLE_COLOR, (sx, sy), 4)
        for p in beam:
            if not p.alive:
                sx, sy = world_to_screen(p.x, p.y, cx, cy, sim.scale)
                pygame.draw.circle(screen, (120, 30, 30), (sx, sy), 3)

        if sim.paused:
            ov = font.render("⏸  PAUSED — SPACE or [Pause / Run] to continue",
                             True, (255, 210, 60))
            screen.blit(ov, (cx - ov.get_width()//2, cy - 12))

        screen.set_clip(None)

        # ── HUD: right panel ─────────────────────────────────
        hx0 = SIM_W
        pygame.draw.rect(screen, (9, 13, 11), (hx0, 0, HUD_W, SIM_H))
        pygame.draw.line(screen, GRAPH_BORDER, (hx0, 0), (hx0, SIM_H), 2)

        energies = [np.log10(p.energy_ev + 1.0) for p in alive]
        radii    = [np.hypot(p.x, p.y)          for p in alive]
        pmags    = [np.hypot(p.px, p.py)         for p in alive]

        meanE = float(np.mean(energies)) if energies else 0.0
        meanR = float(np.mean(radii))    if radii    else 0.0
        meanP = float(np.mean(pmags))    if pmags    else 0.0

        hist_E.append(meanE);    hist_r.append(meanR)
        hist_Bz.append(float(Bz)); hist_p.append(meanP)
        for h in hist_refs:
            if len(h) > HISTORY_LEN: h.pop(0)

        gx, gy = hx0 + HUD_PAD, 12
        draw_graph(screen, gx, gy, GRAPH_W, GRAPH_H,
                   hist_E,  "Energy (log10 eV)", font_graph, font_val)
        gy += GRAPH_H + 9
        draw_graph(screen, gx, gy, GRAPH_W, GRAPH_H,
                   hist_r,  "Mean Radius (m)",   font_graph, font_val)
        gy += GRAPH_H + 9
        draw_graph(screen, gx, gy, GRAPH_W, GRAPH_H,
                   hist_Bz, "Bz (Tesla)",        font_graph, font_val)
        gy += GRAPH_H + 9
        draw_graph(screen, gx, gy, GRAPH_W, GRAPH_H,
                   hist_p,  "Mean |p| (kg·m/s)", font_graph, font_val)

        gy += GRAPH_H + 12
        stats = [
            f"Alive : {len(alive)} / {len(beam)}",
            f"Bz    : {Bz:.4f} T",
            f"r     : {meanR:.4f} m",
            f"Steps : {sim.steps_per_frame}",
            f"Zoom  : {sim.scale:.0f}x",
            f"E0    : {sim.E0/1e3:.1f} kV/m",
            f"K_foc : {sim.k_focus/1e6:.1f} MN/m",
            f"t     : {t:.3e} s",
        ]
        for ln in stats:
            if gy + 17 > SIM_H: break
            screen.blit(font_small.render(ln, True, TEXT_COLOR), (hx0+HUD_PAD, gy))
            gy += 17

        # ── DASHBOARD ────────────────────────────────────────
        dy = SIM_H
        pygame.draw.rect(screen, DASH_BG, (0, dy, WIDTH, DASH_H))
        pygame.draw.line(screen, DASH_BORDER, (0, dy), (WIDTH, dy), 2)
        pygame.draw.line(screen, (30,55,40), (0, dy+56),  (SIM_W, dy+56),  1)
        pygame.draw.line(screen, (30,55,40), (0, dy+144), (SIM_W, dy+144), 1)

        screen.blit(font_hdr.render("▸ TOGGLES",  True, (70,150,90)), (5, dy+1))
        screen.blit(font_hdr.render("▸ CONTROLS", True, (70,150,90)), (5, dy+59))
        screen.blit(font_hdr.render("▸ ACTIONS",  True, (70,150,90)), (5, dy+147))

        # Stepper column headers with shortcut hint
        for i, (hdr, sc) in enumerate(step_meta):
            gx_h = PAD + i*(GW+SP)
            screen.blit(font_hdr.render(hdr, True, (100,185,130)), (gx_h, dy+60))
            screen.blit(font_hint.render(f"[{sc}]", True, KEY_HINT_COL), (gx_h, dy+73))

        for btn in buttons:
            btn.draw(screen, mouse_pos, font, font_hint)

        pygame.display.flip()

if __name__ == "__main__":
    main()