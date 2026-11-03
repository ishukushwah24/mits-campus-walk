"""MITS Gwalior - Campus Walk (HQ version, smooth roads + 4 manzil building)

Zaroorat:  pip install pygame numpy
Controls:  W/S/A/D ya arrows = chalo | Left/Right = ghumo | Shift = tez | ESC = band
Quality:   neeche FLOOR_SCALE = 1 karo to floor sabse sharp (par thoda slow).
"""
import os
import math
import random

try:
    import numpy as np
except ImportError:
    raise SystemExit("numpy chahiye:  pip install numpy")
import pygame

pygame.init()
W, H = 1200, 800
HALF = H // 2
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("MITS Gwalior - Campus Walk")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 40)
small = pygame.font.SysFont(None, 22)


def loading(msg):
    screen.fill((18, 28, 24))
    t = font.render(msg, True, (230, 230, 230))
    screen.blit(t, (W // 2 - t.get_width() // 2, H // 2 - 20))
    pygame.display.flip()
    pygame.event.pump()


loading("MITS Gwalior - map ban raha hai...")

# ---------- SETTINGS ----------
FLOOR_SCALE = 2          # 1 = sabse sharp, 2 = tez (recommended), 3 = aur tez
RAYS = 300               # wall columns (W ka divisor: 150, 225, 300, 450)
FOV = math.pi / 3
SPEED, RUN, TURN = 0.07, 0.14, 0.045
BOUND_H = 0.45
MAXD = 45

# ---------- MAP ----------
# 0 = road, 1 = ghaas, 4 = boundary wall, 5 = footpath
S = 10                    # image ke 10 pixel = 1 cell
Y0 = 405                  # image mein map ka top (ab wahi jahan purani top road thi)
K = 3                     # campus ka scale: 1 = original, 3 = lambai-chaudai 3 guna (roads ki chaudai wahi rehti hai)
X0 = 28                   # image ke itne pixel left se kaat diye (left ki khali ghaas hatane ke liye)
FOOTW = 0.5               # footpath ki chaudai (cells), road ke kinare se
EXTRA_COLS = 60         # map ki chaudai (width) itne cell badhao - roads ki jagah / chaudai wahi rehti hai
COLS, ROWS = int(round(K * (70 - X0 / S))) + 1 + EXTRA_COLS, int(round(K * 102)) + 1
TOP = 1                   # upar ki boundary wall map ke bilkul top par
grid = [["1"] * COLS for _ in range(ROWS)]
ROADS = []                # (points, w1, w2) - smooth road / SDF / lane markings ke liye


def chaikin(pts, it=4):
    """Corner cutting: kone gol ho jaate hain, pehla aur aakhri point wahi rehta hai."""
    pts = [(float(a), float(b)) for a, b in pts]
    if len(pts) < 3:
        return pts
    for _ in range(it):
        q = [pts[0]]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            q.append((0.75 * ax + 0.25 * bx, 0.75 * ay + 0.25 * by))
            q.append((0.25 * ax + 0.75 * bx, 0.25 * ay + 0.75 * by))
        q.append(pts[-1])
        pts = q
    return pts


def road(pts, w1, w2=None, smooth=True):
    """pts = image ke (x, y) points, w1/w2 = road ki chaudai (pixel).
    3+ points do to beech ke kone automatically smooth curve ban jaate hain.
    smooth=False karo to kone seedhe (sharp turn) rehte hain."""
    if w2 is None:
        w2 = w1
    if smooth:
        pts = chaikin(pts)
    else:
        pts = [(float(a), float(b)) for a, b in pts]
    ROADS.append((pts, w1, w2))
    segs = list(zip(pts, pts[1:]))
    total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs) or 1
    done = 0
    for (ax, ay), (bx, by) in segs:
        L = math.hypot(bx - ax, by - ay)
        n = max(1, int(L / 3))
        for i in range(n + 1):
            t = i / n
            px = ax + (bx - ax) * t
            py = ay + (by - ay) * t
            w = w1 + (w2 - w1) * ((done + L * t) / total)
            hw = max(1.0, w / S / 2)             # kam se kam 2 cell chaudi
            cc, rr = (px - X0) * K / S, (py - Y0) * K / S
            for r in range(math.floor(rr - hw), math.floor(rr + hw) + 2):
                for c in range(math.floor(cc - hw), math.floor(cc + hw) + 2):
                    if 0 <= r < ROWS and 0 <= c < COLS:
                        if (r + 0.5 - rr) ** 2 + (c + 0.5 - cc) ** 2 <= hw * hw:
                            grid[r][c] = "0"
        done += L


# ----- roads -----
# (top lambi horizontal road hata di gayi - ab wahan boundary wall hai)
LEFT_ROAD = [(58, 405), (100, 1425)]
LEFT_W = 30
road(LEFT_ROAD, LEFT_W)                         # left ki badi tirchi road (normal campus road chaudai)
road([(630, 410), (630, 905)], 22)                          # beech ki vertical road (ab wall tak)
road([(68, 520), (630, 520)], 20)                           # left badi road ko vertical road se jodne wali road
road([(79, 905), (900, 905)], 22)                          # beech ki horizontal road
road([(630, 610), (750, 610), (750, 635)], 20, smooth=False)# chhoti side road (seedha turn, curve nahi)

# ----- boundary (chaaron taraf) -----
for c in range(COLS):
    grid[0][c] = "4"
    grid[ROWS - 1][c] = "4"
for r in range(ROWS):
    grid[r][0] = "4"
    grid[r][COLS - 1] = "4"

# ----- footpath: road ke dono kinaron par (minimap / ped-placement ke liye) -----
FOOT = 1
base = [row[:] for row in grid]
for r in range(ROWS):
    for c in range(COLS):
        if base[r][c] != "1":
            continue
        near = False
        for rr in range(max(0, r - FOOT), min(ROWS, r + FOOT + 1)):
            for cc in range(max(0, c - FOOT), min(COLS, c + FOOT + 1)):
                if base[rr][cc] == "0":
                    near = True
        if near:
            grid[r][c] = "5"

# ----- left ki tirchi boundary wall: left badi road ke saath-saath -----
_p = [((px - X0) * K / S, (py - Y0) * K / S) for px, py in LEFT_ROAD]
_dx, _dy = _p[-1][0] - _p[0][0], _p[-1][1] - _p[0][1]
_L = math.hypot(_dx, _dy)
LW_NX, LW_NY = _dy / _L, -_dx / _L          # wall ka normal (andar ki taraf)
LW_GAP = 1                                 # footpath aur wall ke beech ki jagah (cells), yahan ped lagte hain
LW_C = LW_NX * _p[0][0] + LW_NY * _p[0][1] - (LEFT_W / S / 2 + FOOTW + LW_GAP)   # wall line: LW_NX*x + LW_NY*y = LW_C


def lw_x(yy):
    """row yy par left tirchi wall ka x"""
    return (LW_C - LW_NY * yy) / LW_NX


for r in range(ROWS):                        # wall ke neeche ki mitti ki patti (minimap par bhi dikhegi)
    for c in range(COLS):
        if abs(LW_NX * (c + 0.5) + LW_NY * (r + 0.5) - LW_C) <= 0.6 and grid[r][c] == "1":
            grid[r][c] = "4"

MAP = ["".join(row) for row in grid]

# ---------- BUILDING (4 manzil) - sirf size / jagah ke numbers ----------
BAY_W = 3.0               # facade ke ek bay ki chaudai (cells)
STOREYS = 4               # manzil
STOREY_H = 1.2            # ek manzil ki unchai (cells)
PARAPET = 0.3             # chhat ki mundér
BLD_HT = STOREYS * STOREY_H + PARAPET
# beech ki horizontal road (image y=905 -> cell y~150) ke UPAR, left road aur vertical road ke beech:
BLD_W, BLD_D = 40.0, 13.0        # chaudai 40, gehrai 13
BLD_X1 = 165.0                   # building ka right edge: vertical road se 1.5 cell pehle
BLD_Y1 = 144.0                  # building ka neeche wala edge: bottom road se 1.5 cell pehle
BLD_X0 = BLD_X1 - BLD_W
BLD_Y0 = BLD_Y1 - BLD_D 

# ---------- colours ----------
FOG = (190, 215, 235)
FOGARR = np.array(FOG, np.float32)
PAL = np.array([(52, 52, 56),        # 0 road
                (78, 150, 66),       # 1 ghaas
                (196, 188, 174),     # 2 footpath
                (112, 92, 68)],      # 3 wall ke neeche mitti
               np.float32)
TINT = np.array([(0, 0, 0), (18, 8, -14), (0, 0, 0), (0, 0, 0)], np.float32)


def mix(c1, c2, t):
    return tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3))


# ---------- GROUND TEXTURE (ek baar bake) ----------
PPC = 10                  # texture pixels per cell
PAD = 30                  # map ke bahar ghaas ke cells
LOF = 5                   # far-distance (mip) texture factor
GH = (ROWS + 2 * PAD) * PPC
GW = (COLS + 2 * PAD) * PPC
EDGE_W = 0.12             # road-edge line / kerb ki motai (cells)


def box1d(a, r, axis):
    n = a.shape[axis]
    pad = [(0, 0), (0, 0)]
    pad[axis] = (r + 1, r)
    c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis, dtype=np.float64)
    hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
    lo = np.take(c, np.arange(0, n), axis=axis)
    return ((hi - lo) / (2 * r + 1)).astype(np.float32)


def smooth_noise(rng, k, blur):
    a = rng.random((GH // k + 1, GW // k + 1), dtype=np.float32)
    a = np.repeat(np.repeat(a, k, 0), k, 1)[:GH, :GW]
    return box1d(box1d(a, blur, 0), blur, 1)


def bake_ground():
    rng = np.random.default_rng(3)
    T = np.ones((ROWS + 2 * PAD, COLS + 2 * PAD), np.uint8)
    for r in range(ROWS):
        for c in range(COLS):
            if MAP[r][c] == "4":
                T[r + PAD, c + PAD] = 3
    Tp = np.repeat(np.repeat(T, PPC, 0), PPC, 1)

    L1 = smooth_noise(rng, 40, 18)
    L2 = smooth_noise(rng, 10, 4)
    L1 = (L1 - L1.min()) / (np.ptp(L1) + 1e-6)
    L2 = (L2 - L2.min()) / (np.ptp(L2) + 1e-6)

    lum_g = 0.80 + 0.32 * L1 + 0.14 * (L2 - 0.5)
    lum_f = 0.94 + 0.10 * (L2 - 0.5) + 0.06 * (L1 - 0.5)
    lum_r = 0.92 + 0.12 * (L1 - 0.5) + 0.08 * (L2 - 0.5)

    # channels: 0-2 = ghaas/mitti colour, 3 = road ki luminance, 4 = footpath ki luminance
    tex = np.empty((GH, GW, 5), np.uint8)
    gi = np.where(Tp == 3, 3, 1)
    cg = PAL[gi] * lum_g[..., None].astype(np.float32) + (L1 - 0.5)[..., None] * TINT[gi]
    tex[..., :3] = np.clip(cg, 0, 255).astype(np.uint8)
    tex[..., 3] = np.clip(lum_r * 128, 0, 255).astype(np.uint8)
    tex[..., 4] = np.clip(lum_f * 128, 0, 255).astype(np.uint8)
    lo = tex.reshape(GH // LOF, LOF, GW // LOF, LOF, 5).mean(axis=(1, 3)).astype(np.uint8)
    return tex, lo


def bake_sdf():
    """Road ka signed distance (cells, road ke kinare se; andar negative) + dash coverage.
    Texture resolution par ek baar bakta hai, runtime par bilinear sample hota hai."""
    sd = np.full((GH, GW), 9.0, np.float32)
    dash = np.zeros((GH, GW), np.float32)
    for pts, w1, w2 in ROADS:
        P = [((px - X0) * K / S, (py - Y0) * K / S) for px, py in pts]
        segL = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(P, P[1:])]
        tot = sum(segL) or 1.0
        has_dash = False        # beech ki dashed line band (single lane road); True karo to wapas aa jayegi
        done = 0.0
        for a, b, L in zip(P, P[1:], segL):
            if L > 1e-6:
                h0 = max(1.0, (w1 + (w2 - w1) * done / tot) / S / 2)
                h1 = max(1.0, (w1 + (w2 - w1) * (done + L) / tot) / S / 2)
                m = max(h0, h1) + FOOTW + 3.5
                x0 = max(0, int((min(a[0], b[0]) - m + PAD) * PPC))
                x1 = min(GW, int((max(a[0], b[0]) + m + PAD) * PPC) + 1)
                y0 = max(0, int((min(a[1], b[1]) - m + PAD) * PPC))
                y1 = min(GH, int((max(a[1], b[1]) + m + PAD) * PPC) + 1)
                if x1 > x0 and y1 > y0:
                    xs = ((np.arange(x0, x1, dtype=np.float32) + 0.5) / PPC - PAD)[None, :]
                    ys = ((np.arange(y0, y1, dtype=np.float32) + 0.5) / PPC - PAD)[:, None]
                    vx, vy = b[0] - a[0], b[1] - a[1]
                    t = np.clip(((xs - a[0]) * vx + (ys - a[1]) * vy) / (L * L), 0.0, 1.0)
                    dist = np.hypot(xs - (a[0] + t * vx), ys - (a[1] + t * vy))
                    sv = sd[y0:y1, x0:x1]
                    np.minimum(sv, dist - (h0 + (h1 - h0) * t), out=sv)
                    if has_dash:
                        u = np.mod(done + t * L, 1.8)
                        along = np.clip(np.minimum(u, 0.9 - u) / 0.08, 0, 1)
                        lat = np.clip((0.07 - dist) / 0.05 + 0.5, 0, 1)
                        dv = dash[y0:y1, x0:x1]
                        np.maximum(dv, along * lat, out=dv)
            done += L
    # map ke andar (boundary wall ke face tak) hi road/footpath
    ok = np.zeros((GH, GW), bool)
    ok[(1 + PAD) * PPC:(ROWS - 1 + PAD) * PPC, (1 + PAD) * PPC:(COLS - 1 + PAD) * PPC] = True
    sd[~ok] = 9.0
    dash[~ok] = 0.0
    return np.stack([sd, dash], axis=-1)


TEX, TEX_LO = bake_ground()
SDF = bake_sdf()
loading("MITS Gwalior - sky aur textures...")

# ---------- SKY (360 degree panorama, ek baar bake) ----------
PANO_W = int(W * 2 * math.pi / FOV)
rng_sky = np.random.default_rng(5)
pano = pygame.Surface((PANO_W, HALF)).convert()
for yy in range(HALF):
    t = yy / (HALF - 1)
    if t < 0.6:
        c = mix((56, 110, 205), (122, 180, 238), t / 0.6)
    else:
        c = mix((122, 180, 238), FOG, (t - 0.6) / 0.4)
    pygame.draw.line(pano, c, (0, yy), (PANO_W, yy))

# sooraj + glow
SUN_AZ, SUN_Y, G = 0.30, 85, 520
gy, gx = np.mgrid[0:G, 0:G].astype(np.float32)
gd = np.hypot(gx - G / 2, gy - G / 2)
ga = np.clip(0.55 * np.exp(-(gd / 90) ** 2) + 0.28 * np.exp(-(gd / 230) ** 1.3), 0, 1)
ga = np.maximum(ga, np.clip((32 - gd) / 6, 0, 1))
ga = ga * np.clip((G / 2 - gd) / 70, 0, 1)          # kinare par zero tak fade (seam nahi)
glow = np.zeros((G, G, 4), np.uint8)
glow[..., 0], glow[..., 1], glow[..., 2] = 255, 246, 215
glow[..., 3] = (ga * 255).astype(np.uint8)
glow_s = pygame.image.frombuffer(glow.tobytes(), (G, G), "RGBA").convert_alpha()
sun_px = int(SUN_AZ / (2 * math.pi) * PANO_W)
pano.blit(glow_s, (sun_px - G // 2, SUN_Y - G // 2))
pano.blit(glow_s, (sun_px - G // 2 + PANO_W, SUN_Y - G // 2))   # wrap ke liye

# badal
for _ in range(11):
    cw, ch = int(rng_sky.integers(260, 430)), int(rng_sky.integers(70, 120))
    Y, X = np.mgrid[0:ch, 0:cw].astype(np.float32)
    field = np.zeros((ch, cw), np.float32)
    for _b in range(7):
        cx = rng_sky.uniform(0.2, 0.8) * cw
        cy = rng_sky.uniform(0.45, 0.7) * ch
        sx_, sy_ = rng_sky.uniform(28, 62), rng_sky.uniform(12, 28)
        field += np.exp(-(((X - cx) / sx_) ** 2 + ((Y - cy) / sy_) ** 2))
    alpha = np.clip((field - 0.35) * 1.5, 0, 1) * 0.92
    shade = 1 - 0.13 * (Y / ch)
    cl = np.zeros((ch, cw, 4), np.uint8)
    cl[..., 0] = np.clip(255 * shade, 0, 255)
    cl[..., 1] = np.clip(255 * shade, 0, 255)
    cl[..., 2] = np.clip(252 * shade, 0, 255)
    cl[..., 3] = (alpha * 255).astype(np.uint8)
    cs = pygame.image.frombuffer(cl.tobytes(), (cw, ch), "RGBA").convert_alpha()
    px_ = int(rng_sky.integers(0, PANO_W))
    py_ = int(rng_sky.integers(10, 150))
    pano.blit(cs, (px_, py_))
    if px_ + cw > PANO_W:
        pano.blit(cs, (px_ - PANO_W, py_))

# door ki pahadiyan (2 parat)
for layer, (hh, amp, fog_t, col0) in enumerate(((30, 11, 0.62, (92, 128, 150)),
                                                 (14, 6, 0.38, (68, 108, 92)))):
    colr = mix(col0, FOG, fog_t)
    for xx in range(PANO_W):
        u = 2 * math.pi * xx / PANO_W
        h_ = hh + amp * math.sin(u * 3 + layer) + 0.55 * amp * math.sin(u * 7 + 2 * layer) \
            + 0.3 * amp * math.sin(u * 19 + layer)
        pygame.draw.line(pano, colr, (xx, HALF - int(h_)), (xx, HALF))


def draw_sky():
    off = int(((angle - FOV / 2) / (2 * math.pi)) % 1.0 * PANO_W)
    screen.blit(pano, (-off, 0))
    if off > PANO_W - W:
        screen.blit(pano, (PANO_W - off, 0))


# ---------- FLOOR (numpy, per-pixel) ----------
SC = FLOOR_SCALE
RW, RH = W // SC, HALF // SC
FLOOR_BUF = np.empty((RH, RW, 3), np.uint8)
FLOOR_BUF[:] = FOG
yrows = HALF + (np.arange(RH) + 0.5) * SC
dist_row = HALF / (yrows - HALF)
R0 = int(np.argmax(dist_row <= MAXD))
dr = dist_row[R0:]
REL_F = FOV * ((np.arange(RW) + 0.5) / RW - 0.5)
DR = dr[:, None] / np.cos(REL_F)[None, :]                       # (n, RW) float64
MIX_R = np.clip((dr - 5) / 12, 0, 1).astype(np.float32)[:, None, None]
FOG_R = np.clip((dr / MAXD) ** 1.4, 0, 1).astype(np.float32)[:, None, None]
DET1 = np.clip(1 - (dr - 2) / 10, 0, 1)[:, None]
DET2 = np.clip(1 - (dr - 1) / 4, 0, 1)[:, None]
LINEF = np.clip(1 - (dr - 3) / 9, 0, 1)[:, None]
AMP1 = np.array([0.05, 0.12, 0.04, 0.12])
AMP2 = np.array([0.10, 0.16, 0.06, 0.16])
AA_R = (0.03 + 0.25 * SC * dr ** 2 / HALF).astype(np.float32)[:, None]   # door par edge thoda soft (mip jaisa)
EDGEF = np.clip(1 - (dr - 6) / 14, 0, 1).astype(np.float32)[:, None]
DASHF = np.clip(1 - (dr - 8) / 14, 0, 1).astype(np.float32)[:, None]
ROAD_K = (PAL[0] / 128).astype(np.float32)
FOOT_K = (PAL[2] / 128).astype(np.float32)
EDGE_ADD = np.array((120, 120, 116), np.float32)
KERB_ADD = np.array((60, 58, 55), np.float32)
DASH_ADD = np.array((236, 200, 70), np.float32) * 0.75


def hnoise(a, b):
    s = np.sin(a * 12.9898 + b * 78.233) * 43758.5453
    return s - np.floor(s)


def draw_floor():
    ca = np.cos(angle + REL_F)[None, :]
    sa = np.sin(angle + REL_F)[None, :]
    wx = x + ca * DR
    wy = y + sa * DR
    fx = (wx + PAD) * PPC
    fy = (wy + PAD) * PPC
    ix = np.clip(fx, 0, GW - 1).astype(np.int32)
    iy = np.clip(fy, 0, GH - 1).astype(np.int32)

    # road SDF: bilinear sample -> edges kisi bhi zoom par smooth
    bx = np.clip(fx - 0.5, 0, GW - 1.001)
    by = np.clip(fy - 0.5, 0, GH - 1.001)
    sx0 = bx.astype(np.int32)
    sy0 = by.astype(np.int32)
    tx = (bx - sx0).astype(np.float32)[..., None]
    ty = (by - sy0).astype(np.float32)[..., None]
    s00 = SDF[sy0, sx0]
    s01 = SDF[sy0, sx0 + 1]
    s10 = SDF[sy0 + 1, sx0]
    s11 = SDF[sy0 + 1, sx0 + 1]
    s00 += (s01 - s00) * tx
    s10 += (s11 - s10) * tx
    s00 += (s10 - s00) * ty
    sd, dsh = s00[..., 0], s00[..., 1]

    rc = np.clip(0.5 - sd / AA_R, 0, 1)                    # road coverage
    fc = np.clip(0.5 - (sd - FOOTW) / AA_R, 0, 1)          # road + footpath coverage
    wr, wf, wg = rc, fc - rc, 1 - fc
    eb = rc * (1 - np.clip(0.5 - (sd + EDGE_W) / AA_R, 0, 1)) * EDGEF
    kb = np.clip(np.clip(0.5 - (sd - EDGE_W) / AA_R, 0, 1) - rc, 0, 1) * EDGEF
    db = dsh * rc * DASHF

    # paas ki detail (door jaate hi fade)
    n1 = hnoise(np.floor(wx * 30), np.floor(wy * 30))
    n2 = hnoise(np.floor(wx * 90), np.floor(wy * 90))
    det = ((n1 - 0.5) * (AMP1[1] * wg + AMP1[0] * wr + AMP1[2] * wf) * DET1
           + (n2 - 0.5) * (AMP2[1] * wg + AMP2[0] * wr + AMP2[2] * wf) * DET2)
    s2x, s2y = wx * 2, wy * 2
    slab = hnoise(np.floor(s2x), np.floor(s2y))
    det += wf * (slab - 0.5) * 0.10
    uu, vv = s2x - np.floor(s2x), s2y - np.floor(s2y)
    det -= wf * ((uu < 0.03) | (vv < 0.03)) * 0.22 * LINEF

    hi = TEX[iy, ix].astype(np.float32)
    hi *= (1 + det).astype(np.float32)[..., None]
    lo = TEX_LO[iy // LOF, ix // LOF].astype(np.float32)
    lay = hi * (1 - MIX_R) + lo * MIX_R

    col = (lay[..., :3] * wg[..., None]
           + lay[..., 3:4] * ROAD_K * wr[..., None]
           + lay[..., 4:5] * FOOT_K * wf[..., None])
    e3, k3, d3 = eb[..., None], kb[..., None], db[..., None]
    col = col * (1 - 0.55 * e3) + EDGE_ADD * e3            # road ke kinare ki halki line
    col = col * (1 - 0.22 * k3) + KERB_ADD * k3            # footpath kerb
    col = col * (1 - 0.75 * d3) + DASH_ADD * d3            # beech ki peeli dashed line

    col += (FOGARR - col) * FOG_R
    FLOOR_BUF[R0:] = np.clip(col, 0, 255).astype(np.uint8)
    surf = pygame.image.frombuffer(FLOOR_BUF, (RW, RH), "RGB")
    screen.blit(pygame.transform.smoothscale(surf, (W, HALF)), (0, HALF))


# ---------- WALL (brick texture, pehle se fog/shade ke saath) ----------
def make_brick():
    TWd, THt = 128, 60
    rnd = np.random.default_rng(11)
    a = np.zeros((THt, TWd, 3), np.float32)
    a[:] = (172, 150, 124)                      # mortar
    a[0:8] = (234, 228, 216)                    # upar ka pathar (coping)
    a[8:10] = (190, 182, 170)
    for row in range(6):
        y0 = 10 + row * 8
        off = 0 if row % 2 == 0 else 16
        for bx in range(-1, 5):
            x0 = bx * 32 + off
            b = np.array((208, 178, 140), np.float32) + rnd.uniform(-14, 10, 3) * np.array((1, 1, .8))
            xs0, xs1 = max(0, x0 + 1), min(TWd, x0 + 31)
            if xs1 > xs0:
                a[y0 + 1:y0 + 7, xs0:xs1] = b
    a[58:60] = (140, 122, 100)
    a += rnd.normal(0, 4, (THt, TWd, 1)).astype(np.float32)
    a *= np.linspace(1.0, 0.86, THt, dtype=np.float32)[:, None, None]
    a = np.clip(a, 0, 255).astype(np.uint8)
    return pygame.image.frombuffer(np.ascontiguousarray(a).tobytes(), (TWd, THt), "RGB").convert(), TWd, THt


BRICK, BR_W, BR_H = make_brick()
LEVELS = 16
WALL_STRIPS = []                                 # [side*LEVELS + level][tx]
for side in (0, 1):
    for lvl in range(LEVELS):
        f = lvl / (LEVELS - 1)
        sh = 0.84 if side == 1 else 1.0
        s_ = BRICK.copy()
        m = int(255 * (1 - f) * sh)
        s_.fill((m, m, m), special_flags=pygame.BLEND_RGB_MULT)
        s_.fill((int(FOG[0] * f), int(FOG[1] * f), int(FOG[2] * f)), special_flags=pygame.BLEND_RGB_ADD)
        WALL_STRIPS.append([s_.subsurface((i, 0, 1, BR_H)) for i in range(BR_W)])

COL = W // RAYS
RAY_REL = FOV * ((np.arange(RAYS) + 0.5) / RAYS - 0.5)
COS_REL = np.cos(RAY_REL)


def draw_walls():
    a = angle + RAY_REL
    ca, sa = np.cos(a), np.sin(a)
    with np.errstate(divide="ignore", invalid="ignore"):
        nd = LW_NX * ca + LW_NY * sa                                               # ray aur left tirchi wall ka angle
        tx = np.where(nd < 0, (LW_C - (LW_NX * x + LW_NY * y)) / nd, 1e9)          # left tirchi wall
        tx = np.minimum(tx, np.where(ca > 0, (COLS - 1 - x) / ca, 1e9))           # right wall
        ty = np.where(sa < 0, (TOP - y) / sa, (ROWS - 1 - y) / sa)   # upar ki wall TOP par
    tx = np.where(np.isfinite(tx), tx, 1e9)
    ty = np.where(np.isfinite(ty), ty, 1e9)
    t = np.minimum(tx, ty)
    side = (ty < tx).astype(np.int32)
    hx, hy = x + t * ca, y + t * sa
    u = np.where(side == 1, hx, hy) % 1.0
    d = np.maximum(0.05, t * COS_REL)
    full = H / d
    lvl = np.clip(((d / MAXD) ** 1.4) * (LEVELS - 1), 0, LEVELS - 1).astype(np.int32)
    tx_pix = (u * BR_W).astype(np.int32) % BR_W
    hs = np.minimum(4000, (full * BOUND_H)).astype(np.int32)
    bottoms = (HALF + full / 2).astype(np.int32)
    idx = side * LEVELS + lvl
    scale = pygame.transform.scale
    blit = screen.blit
    for i, (h, b, k, tpx) in enumerate(zip(hs.tolist(), bottoms.tolist(), idx.tolist(), tx_pix.tolist())):
        if h < 1:
            continue
        blit(scale(WALL_STRIPS[k][tpx], (COL, h)), (i * COL, b - h))


# ---------- BUILDING (4 manzil): facade texture + ray-box drawing ----------
def make_facade():
    PXU = 80                                     # texture pixels per cell
    SH = int(STOREY_H * PXU)
    PAR = int(PARAPET * PXU)
    TWd = int(BAY_W * PXU)
    THt = SH * STOREYS + PAR
    rnd = np.random.default_rng(21)
    a = np.zeros((THt, TWd, 3), np.float32)
    a[:] = (226, 214, 190)
    a += rnd.normal(0, 3, (THt, TWd, 1)).astype(np.float32)
    a[0:PAR] = (240, 236, 226)                   # parapet
    a[PAR - 6:PAR] = (190, 182, 168)             # cornice ki chhaaya
    c1 = np.array((96, 150, 200), np.float32)
    c2 = np.array((50, 90, 140), np.float32)
    for s in range(STOREYS):
        y0 = PAR + s * SH
        a[y0 + SH - 8:y0 + SH] = (178, 168, 150)             # slab
        for wx in (28, 142):
            wy0, wy1 = y0 + 20, y0 + 72
            a[wy0 - 3:wy1 + 3, wx - 3:wx + 73] = (120, 112, 100)    # frame
            g = np.linspace(0, 1, wy1 - wy0, dtype=np.float32)[:, None, None]
            a[wy0:wy1, wx:wx + 70] = c1 * (1 - g) + c2 * g          # sheesha
            a[wy0:wy1, wx + 34:wx + 36] = (120, 112, 100)           # beech ka mullion
    a[PAR:, 0:6] = (200, 188, 164)               # bay ke kinare ke column
    a[PAR:, TWd - 6:] = (200, 188, 164)
    a[THt - 10:] = (130, 120, 108)               # neeche ki plinth
    a = np.clip(a, 0, 255).astype(np.uint8)
    surf = pygame.image.frombuffer(np.ascontiguousarray(a).tobytes(), (TWd, THt), "RGB").convert()
    return surf, TWd, THt


FACADE, FA_W, FA_H = make_facade()
FACADE_LV = []                                   # [side*LEVELS + level]
for _side in (0, 1):
    for _lvl in range(LEVELS):
        _f = _lvl / (LEVELS - 1)
        _sh = 0.84 if _side == 1 else 1.0
        _s = FACADE.copy()
        _m = int(255 * (1 - _f) * _sh)
        _s.fill((_m, _m, _m), special_flags=pygame.BLEND_RGB_MULT)
        _s.fill((int(FOG[0] * _f), int(FOG[1] * _f), int(FOG[2] * _f)), special_flags=pygame.BLEND_RGB_ADD)
        FACADE_LV.append(_s)

BLD_BD = np.full(RAYS, 1e9)                      # har ray par building ki depth (trees ki sorting ke liye)
BLD_HIT = None


def building_cast():
    global BLD_BD, BLD_HIT
    a = angle + RAY_REL
    ca, sa = np.cos(a), np.sin(a)
    ca = np.where(np.abs(ca) < 1e-9, 1e-9, ca)
    sa = np.where(np.abs(sa) < 1e-9, 1e-9, sa)
    t1, t2 = (BLD_X0 - x) / ca, (BLD_X1 - x) / ca
    t3, t4 = (BLD_Y0 - y) / sa, (BLD_Y1 - y) / sa
    tnx, tfx = np.minimum(t1, t2), np.maximum(t1, t2)
    tny, tfy = np.minimum(t3, t4), np.maximum(t3, t4)
    tmin, tmax = np.maximum(tnx, tny), np.minimum(tfx, tfy)
    hit = (tmax > tmin) & (tmin > 0.05) & (tmin < MAXD)
    side = (tny > tnx).astype(np.int32)          # 1 = y wali face
    u = np.where(side == 1, x + tmin * ca, y + tmin * sa)
    BLD_BD = np.where(hit, tmin * COS_REL, 1e9)
    BLD_HIT = (hit, side, u, tmin)


def draw_building():
    hit, side, u, t = BLD_HIT
    if not hit.any():
        return
    d = np.maximum(0.05, t * COS_REL)
    full = H / d
    lvl = np.clip(((d / MAXD) ** 1.4) * (LEVELS - 1), 0, LEVELS - 1).astype(np.int32)
    tx_pix = (((u / BAY_W) % 1.0) * FA_W).astype(np.int32) % FA_W
    bottoms = (HALF + full / 2).astype(np.int32)
    hs = (full * BLD_HT).astype(np.int32)
    idx = side * LEVELS + lvl
    scale = pygame.transform.scale
    for i, (ok, h, b, k, tpx) in enumerate(zip(hit.tolist(), hs.tolist(), bottoms.tolist(),
                                                 idx.tolist(), tx_pix.tolist())):
        if not ok or h < 1:
            continue
        top = b - h
        vy0, vy1 = max(top, 0), min(b, H)
        if vy1 <= vy0:
            continue
        sy0 = int((vy0 - top) * FA_H / h)
        sy1 = min(FA_H, max(int(math.ceil((vy1 - top) * FA_H / h)), sy0 + 1))
        strip = FACADE_LV[k].subsurface((tpx, sy0, 1, sy1 - sy0))
        screen.blit(scale(strip, (COL, vy1 - vy0)), (i * COL, vy0))


# ---------- TREES (baked sprites) ----------
SPW, SPH, BASE_Y = 200, 280, 252


def make_tree(seed):
    rnd = random.Random(seed)
    s = pygame.Surface((SPW, SPH), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (0, 0, 0, 70), (28, BASE_Y - 14, 144, 30))
    pygame.draw.polygon(s, (86, 58, 38), [(88, BASE_Y), (112, BASE_Y), (106, 150), (94, 150)])
    pygame.draw.polygon(s, (116, 84, 54), [(88, BASE_Y), (99, BASE_Y), (98, 150), (94, 150)])
    pygame.draw.line(s, (86, 58, 38), (100, 175), (68, 132), 6)
    pygame.draw.line(s, (86, 58, 38), (100, 165), (136, 124), 6)
    hue = [(36, 108, 46), (54, 130, 50), (30, 94, 58)][seed % 3]
    blobs = []
    for _ in range(26):
        ang = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(0, 1) ** 0.6
        blobs.append((100 + math.cos(ang) * rr * 62, 98 + math.sin(ang) * rr * 46, rnd.uniform(26, 40)))
    for f, dx, dy, k in ((0.62, 4, 7, 1.0), (0.86, 0, 0, 0.92), (1.14, -5, -7, 0.70)):
        c = tuple(min(255, int(v * f)) for v in hue)
        for bx, by, r in blobs:
            pygame.draw.circle(s, c, (int(bx + dx), int(by + dy)), int(r * k))
    for _ in range(240):
        bx, by, r = rnd.choice(blobs)
        px = bx + rnd.uniform(-r, r) * 0.8
        py = by + rnd.uniform(-r, r) * 0.8
        f = rnd.choice((0.7, 1.25, 1.35))
        pygame.draw.circle(s, tuple(min(255, int(v * f)) for v in hue), (int(px), int(py)), rnd.randint(2, 4))
    return s


TREE_SPR = [make_tree(i) for i in range(3)]
_tree_cache = {}


def tree_surface(v, wpx):
    wq = max(4, min(1400, int(wpx) // 4 * 4))
    key = (v, wq)
    s = _tree_cache.get(key)
    if s is None:
        if len(_tree_cache) > 500:
            _tree_cache.clear()
        s = pygame.transform.smoothscale(TREE_SPR[v], (wq, int(wq * SPH / SPW)))
        _tree_cache[key] = s
    return s


random.seed(7)
TIN, TOUT = [], []
for r in range(TOP + 3, ROWS - 3):                             # andar ke ped (TOP wall ke neeche)
    for c in range(3, COLS - 3):
        if random.random() > 0.035:
            continue
        if c > lw_x(r) + 2 and all(MAP[rr][cc] == "1" for rr in range(r - 2, r + 3) for cc in range(c - 2, c + 3)):
            TIN.append((c + random.uniform(0.2, 0.8), r + random.uniform(0.2, 0.8),
                        random.uniform(0.85, 1.25), random.randint(0, 2)))
for r in range(-16, ROWS + 16):                                # boundary ke bahar ka jungle
    for c in range(-16, COLS + 16):
        if (r < TOP - 2 or r > ROWS + 1 or c > COLS + 1) and c > lw_x(r) and random.random() < 0.07:
            TOUT.append((c + random.uniform(0.1, 0.9), r + random.uniform(0.1, 0.9),
                         random.uniform(1.0, 1.6), random.randint(0, 2)))
# footpath aur left wall ke beech ki patti mein sirf 5-6 random ped
TREE_N = random.randint(5, 6)                                      # kitne ped
for _i in range(TREE_N):
    _ty = TOP + 3 + (_i + random.random()) * (ROWS - TOP - 6) / TREE_N
    _cx = _p[0][0] + (_ty - _p[0][1]) * _dx / _dy
    _d = LEFT_W / S / 2 + FOOTW + random.uniform(0.7, LW_GAP - 0.7)
    TIN.append((_cx - LW_NX * _d, _ty - LW_NY * _d, random.uniform(0.85, 1.25), random.randint(0, 2)))
# building ke andar / bilkul paas koi ped nahi
TIN = [t for t in TIN if not (BLD_X0 - 2 < t[0] < BLD_X1 + 2 and BLD_Y0 - 2 < t[1] < BLD_Y1 + 2)]
TIN = np.array(TIN, np.float64)
TOUT = np.array(TOUT, np.float64)


def draw_trees(arr, which=None):
    """which = None: sab ped | "behind": building ke peeche wale | "front": building ke aage wale"""
    if len(arr) == 0:
        return
    dx, dy = arr[:, 0] - x, arr[:, 1] - y
    ang = (np.arctan2(dy, dx) - angle + math.pi) % (2 * math.pi) - math.pi
    d = np.hypot(dx, dy) * np.cos(ang)
    m = (np.abs(ang) < FOV / 2 + 0.3) & (d > 0.5) & (d < MAXD)
    idx = np.nonzero(m)[0]
    idx = idx[np.argsort(-d[idx])]
    for i in idx.tolist():
        di = float(d[i])
        sc = float(arr[i, 2])
        v = int(arr[i, 3])
        sx = W * (float(ang[i]) / FOV + 0.5)
        if which is not None:
            ci = min(RAYS - 1, max(0, int(sx / COL)))
            if (which == "behind") != (BLD_BD[ci] < di):
                continue
        hpx = H / di * sc * 2.0
        wpx = hpx * SPW / SPH
        if wpx < 4 or sx + wpx / 2 < 0 or sx - wpx / 2 > W:
            continue
        spr = tree_surface(v, wpx)
        sw, sh = spr.get_size()
        ground = HALF + H / (2 * di)
        f = min(1.0, (di / MAXD) ** 1.4)
        if f > 0.02:
            spr = spr.copy()
            mm = int(255 * (1 - f))
            spr.fill((mm, mm, mm, 255), special_flags=pygame.BLEND_RGB_MULT)
            spr.fill((int(FOG[0] * f), int(FOG[1] * f), int(FOG[2] * f), 0), special_flags=pygame.BLEND_RGB_ADD)
        screen.blit(spr, (int(sx - sw / 2), int(ground - sh * BASE_Y / SPH)))


# ---------- vignette + minimap ----------
yy_, xx_ = np.mgrid[0:H, 0:W].astype(np.float32)
dd = np.sqrt(((xx_ - W / 2) / (W / 2)) ** 2 + ((yy_ - H / 2) / (H / 2)) ** 2)
va = np.zeros((H, W, 4), np.uint8)
va[..., 3] = (np.clip((dd - 0.55) / 0.9, 0, 1) ** 1.8 * 120).astype(np.uint8)
VIG = pygame.image.frombuffer(va.tobytes(), (W, H), "RGBA").convert_alpha()

CELL = 1
MINI_COL = {"0": (40, 40, 44), "1": (50, 110, 50), "4": (200, 185, 150), "5": (185, 175, 160)}
mini = pygame.Surface((COLS * CELL, ROWS * CELL))
for r in range(ROWS):
    for c in range(COLS):
        pygame.draw.rect(mini, MINI_COL[MAP[r][c]], (c * CELL, r * CELL, CELL, CELL))
pygame.draw.rect(mini, (150, 110, 190), (int(BLD_X0 * CELL), int(BLD_Y0 * CELL),
                                          int((BLD_X1 - BLD_X0) * CELL), int((BLD_Y1 - BLD_Y0) * CELL)))
mini = mini.convert()
mini.set_alpha(215)
MX, MY = W - COLS * CELL - 14, 14


def text(msg, pos, f=font, col=(255, 255, 255)):
    screen.blit(f.render(msg, True, (0, 0, 0)), (pos[0] + 2, pos[1] + 2))
    screen.blit(f.render(msg, True, col), pos)


def can_walk(px, py, r=0.18):
    # collision ab wahi smooth road-SDF use karta hai jo floor dikhata hai
    for ox, oy in ((-r, -r), (r, -r), (-r, r), (r, r)):
        ix = int((px + ox + PAD) * PPC)
        iy = int((py + oy + PAD) * PPC)
        if not (0 <= ix < GW and 0 <= iy < GH) or SDF[iy, ix, 0] >= FOOTW:
            return False
    return True


# ---------- main loop ----------
START_NEAR_BUILDING = True      # False karo to purani jagah (top par) se start hoga
if START_NEAR_BUILDING:
    x, y, angle = 70.0, 150.0, -math.pi / 2     # horizontal road par, north ki taraf (building ki taraf) dekhta hua
else:
    x, y, angle = 6.3 * K - X0 * K / S, 7.0 * K, math.pi / 2   # left ki badi road par, neeche ki taraf dekhta hua
SHOT = os.environ.get("MITS_SHOT")
frame = 0
running = True
while running:
    dt = min(2.5, clock.get_time() / 16.67) or 1.0
    for e in pygame.event.get():
        if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        angle -= TURN * dt
    if keys[pygame.K_RIGHT]:
        angle += TURN * dt
    spd = (RUN if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) else SPEED) * dt
    move = strafe = 0.0
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        move = spd
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        move = -spd
    if keys[pygame.K_d]:
        strafe = spd * 0.7
    if keys[pygame.K_a]:
        strafe = -spd * 0.7
    nx = x + math.cos(angle) * move + math.cos(angle + math.pi / 2) * strafe
    ny = y + math.sin(angle) * move + math.sin(angle + math.pi / 2) * strafe
    if can_walk(nx, y):
        x = nx
    if can_walk(x, ny):
        y = ny

    draw_sky()
    draw_floor()
    draw_trees(TOUT)                 # boundary ke bahar (wall ke peeche)
    draw_walls()
    building_cast()
    draw_trees(TIN, "behind")        # building ke peeche wale ped
    draw_building()
    draw_trees(TIN, "front")         # building ke aage wale ped
    screen.blit(VIG, (0, 0))

    screen.blit(mini, (MX, MY))
    pygame.draw.rect(screen, (255, 255, 255), (MX - 1, MY - 1, COLS * CELL + 2, ROWS * CELL + 2), 1)
    px, py = MX + x * CELL, MY + y * CELL
    for da in (-FOV / 2, FOV / 2):
        pygame.draw.line(screen, (255, 255, 120), (px, py),
                         (px + math.cos(angle + da) * 14, py + math.sin(angle + da) * 14), 1)
    pygame.draw.circle(screen, (255, 60, 60), (int(px), int(py)), 3)

    bearing = (math.degrees(angle) + 90) % 360
    compass = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")[int((bearing + 22.5) // 45) % 8]
    text("MITS GWALIOR", (20, 18))
    text("%s  %d\u00b0   |   FPS %d" % (compass, bearing, clock.get_fps()), (22, 54), small)
    text("W/S/A/D chalo  |  <- -> ghumo  |  Shift tez  |  Esc band", (22, H - 28), small)
    pygame.display.flip()
    clock.tick(60)

    frame += 1
    if SHOT and frame == 8:
        pygame.image.save(screen, SHOT)
        running = False

pygame.quit()