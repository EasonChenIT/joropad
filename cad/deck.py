"""Deck geometry on a real B-rep kernel (build123d / OpenCascade).

top_case()  : panel + walls + palm isogrid + trackpad pocket + ribs + bosses
              (fdm: + socket cradles, screw holes; service/LID: + trackpad rails, magnet pockets, pin holes,
               hook grooves, finger notch - the whole top case lifts off)
cover()     : fdm: inset bottom plate with countersunk screws and socket keepers
              service/LID: full-footprint solid tray with keyboard rails, magnet pads, alignment pins, back hooks
keyboard(), keycaps(), trackpad() : simplified device envelopes for interference checks and renders
All solids are in assembly coordinates (see params.py).
"""
import math
from functools import lru_cache
from build123d import (Align, Axis, Box, Circle, Cone, Cylinder, Kind, Plane, Polygon, Pos, Rectangle,
                       RectangleRounded, Rot, Sketch, chamfer, extrude, offset)
import params as P

MIN = (Align.MIN, Align.MIN, Align.MIN)


# ------------------------------------------------------------------ helpers
def rrect(x0, y0, x1, y1, r):
    r = min(r, (x1 - x0) / 2 - 1e-3, (y1 - y0) / 2 - 1e-3)
    if r <= 0.01:
        return Pos((x0 + x1) / 2, (y0 + y1) / 2) * Rectangle(x1 - x0, y1 - y0)
    return Pos((x0 + x1) / 2, (y0 + y1) / 2) * RectangleRounded(x1 - x0, y1 - y0, r)


def rect(x0, y0, x1, y1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2) * Rectangle(x1 - x0, y1 - y0)


def prism(sk, z0, z1):
    return Pos(0, 0, z0) * extrude(sk, z1 - z0)


def box(x0, x1, y0, y1, z0, z1):
    return Pos(x0, y0, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=MIN)


def fuse(base, parts):
    parts = [p for p in parts if p is not None]
    return base.fuse(*parts).clean() if parts else base


def cut(base, parts):
    parts = [p for p in parts if p is not None]
    return base.cut(*parts).clean() if parts else base


def lattice_lines(region_bbox, period, width, x_anchor):
    """Three families of parallel strips (60 deg apart) covering region_bbox = (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = region_bbox
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    half = math.hypot(x1 - x0, y1 - y0) / 2 + period
    strips = []
    for k in range(3):
        a = math.radians(60 * k)
        nx, ny = math.cos(a), math.sin(a)
        s_c = (cx - x_anchor) * nx + cy * ny
        n0, n1 = math.floor((s_c - half) / period), math.ceil((s_c + half) / period)
        for n in range(n0, n1 + 1):
            s = n * period
            # point on the line closest to the region centre
            d = s - s_c
            px, py = cx + d * nx, cy + d * ny
            strips.append(Pos(px, py) * Rot(0, 0, 60 * k) * Rectangle(width, 2 * half))
    return strips


def sk_union(faces):
    sk = faces[0]
    if len(faces) > 1:
        sk = sk.fuse(*faces[1:]).clean()
    return Sketch() + sk.faces()


# ------------------------------------------------------------------ devices
def _wedge(w, d, h_front, h_back, r, tilt):
    side = Polygon((0, 0), (d, 0), (d, h_back), (0, h_front), align=None)
    body = extrude(Plane.YZ * side, w)                     # Plane.YZ: local (u, v) = (y, z), extrude +x
    foot = prism(rrect(0, 0, w, d, r), -1, max(h_front, h_back) + 1)
    return Rot(-math.degrees(tilt), 0, 0) * (body & foot)


@lru_cache(None)
def keyboard():
    k = _wedge(P.KB_W, P.KB_D, P.KB_FRONT_H, P.KB_BACK_H, P.KB_R, P.ka)
    return Pos(P.kb_x0 + P.KB_CLR, P.kb_fy, P.z_kb_top - P.KB_FRONT_H * math.cos(P.ka)) * k


@lru_cache(None)
def keycaps():
    """Key field as one block, KEYCAP_H tall, sitting on the top plate."""
    sk = rrect(P.kf_x0 + P.KEY_CLR, P.kf_y0 + P.KEY_CLR, P.kf_x1 - P.KEY_CLR, P.kf_y1 - P.KEY_CLR,
               max(P.KF_R - P.KEY_CLR, 0.3))
    return prism(sk, P.z_kb_top, P.z_kb_top + P.KEYCAP_H)


@lru_cache(None)
def trackpad():
    t = _wedge(P.TP_W, P.TP_D, P.TP_FRONT_H, P.TP_BACK_H, P.TP_R, P.ta)
    return Pos(P.tp_gx0, P.tp_gy0 - P.tp_lean_f, P.z_tp_top - P.TP_FRONT_H * math.cos(P.ta)) * t


# ------------------------------------------------------------------ outlines shared by both parts
def outline():
    return rrect(0, 0, P.W, P.D, P.CORNER_R)


def inner_outline(grow=0.0):
    return rrect(P.WALL - grow, P.WALL - grow, P.W - P.WALL + grow, P.D - P.WALL + grow, P.CORNER_R - P.WALL + grow)


def tp_off(o):
    """Trackpad glass outline offset by o."""
    return rrect(P.tp_gx0 - o, P.tp_gy0 - o, P.tp_gx1 + o, P.tp_gy1 + o, P.TP_R + o)


def bay():
    return rrect(P.kb_x0, P.kb_y0, P.W - P.WALL, P.kb_end, P.KB_R + min(P.KB_CLR, P.KB_CLR_F, P.KB_CLR_B))


def ring(e=0.0):
    """Trackpad pocket outline: glass outline offset by TP_RING = (left, right, front, back), grown by e."""
    L, R, F, B = P.TP_RING
    return rrect(P.tp_gx0 - L - e, P.tp_gy0 - F - e, P.tp_gx1 + R + e, P.tp_gy1 + B + e, P.TP_R + min(P.TP_RING) + e)


def socket_frame(s):
    """Socket body box (in the cradle) for socket dict s: x0..x1, y0..y1, z0..z1."""
    bw, bh, bl = P.sock_w, P.sock_h, P.SOCK_BODY[2]
    return (P.SOCK_WALL, P.SOCK_WALL + bl, s["y"] - bw / 2, s["y"] + bw / 2, s["z"] - bh / 2, s["z"] + bh / 2)


def socket_bodies():
    out = []
    for s in P.sockets:
        x0, x1, y0, y1, z0, z1 = socket_frame(s)
        sh_w, sh_h = (8.94, 3.26) if P.SOCK_ORIENT == "h" else (3.26, 8.94)
        shell = _stadium_x(s["y"], s["z"], sh_w, sh_h, 0.0, x0 + 0.01)       # receptacle shell (USB-C is a stadium)
        out.append(box(x0, x1, y0, y1, z0, z1).fuse(shell))
    return out


# ------------------------------------------------------------------ top case
CRUSH_R = 0.8


def crush_ribs():
    if P.CRUSH <= 0:
        return []
    z_hi = P.z_in_top - 0.3
    z_lo = P.z_tp_top - 0.9 * P.TP_FRONT_H * math.cos(P.ta)
    lead = 1.0
    z_mid = (z_lo + z_hi) / 2
    lean = (P.z_tp_top - z_mid) * math.tan(P.ta)          # tilted faces are shifted forward by this much
    cx = (P.tp_gx0 + P.tp_gx1) / 2
    pts = []  # (x, y) of rib axis
    for y in (P.tp_gy0 + 25, P.tp_gy1 - 25):
        pts.append((P.tp_gx0 + P.CRUSH - CRUSH_R, y))
        pts.append((P.tp_gx1 - P.CRUSH + CRUSH_R, y))
    for x in (cx - 45, cx + 45):
        pts.append((x, P.tp_gy0 - lean + P.CRUSH - CRUSH_R))
    for x in (cx - 45, P.tp_gx1 - 20):
        pts.append((x, P.tp_gy1 - lean - P.CRUSH + CRUSH_R))
    ribs = []
    for x, y in pts:
        cyl = Pos(x, y, z_lo + lead) * Cylinder(CRUSH_R, z_hi - z_lo - lead, align=(Align.CENTER, Align.CENTER, Align.MIN))
        cone = Pos(x, y, z_lo) * Cone(0.05, CRUSH_R, lead, align=(Align.CENTER, Align.CENTER, Align.MIN))
        ribs.append(cyl.fuse(cone))
    return ribs


def palm_isogrid():
    zone = rect(P.WALL - 0.2, P.WALL - 0.2, P.W - P.WALL + 0.2, P.cf - P.RING_T + 0.2) - ring(P.RING_T - 0.2)
    bb = (P.WALL, P.WALL, P.W - P.WALL, P.cf)
    strips = lattice_lines(bb, P.P_TOP, P.RIB, P.W / 2)
    g = sk_union(strips)
    return g & zone


def structure_sketch():
    """All full-height internal walls as one 2D sketch (extruded from the cover to the panel)."""
    sk = [palm_isogrid()]
    sk.append(ring(P.RING_T))                                                        # pocket wall (solid; cavity cut later)
    sk.append(rect(P.tp_gx0 - P.TP_RING[0] - P.RING_T, P.WALL - 0.2, P.tp_gx1 + P.TP_RING[1] + P.RING_T, P.tp_gy0))   # merge with front wall
    sk.append(rect(P.WALL - 0.2, P.cf - P.RING_T, P.W - P.WALL + 0.2, P.cf))         # channel front wall
    sk.append(rect(P.WALL - 0.2, P.ys - P.SEAM_RIB / 2, P.W - P.WALL + 0.2, P.ys + P.SEAM_RIB / 2))   # seam rib
    if P.BACK_WALL > 0:
        sk.append(rect(P.WALL - 0.2, P.kb_end, P.W - P.WALL + 0.2, P.bw1))           # keyboard back wall
    for bx, by in P.bosses:
        sk.append(Pos(bx, by) * Circle(P.MAG_BOSS_R if (bx, by) in P.MAG_POS else P.BOSS_R))
    s = sk_union(sk)
    if P.PORTS:
        sw = P.PLUG_W / 2 + 4.0                                                        # plug head + room to turn
        slots = [rect(P.tp_port - sw, P.cf - P.RING_T - 0.5, P.tp_port + sw, P.cf + 0.5),      # trackpad plug
                 rect(P.kb_port - sw, P.kb_end - 0.5, P.kb_port + sw, P.bw1 + 0.5)]            # keyboard plug
        for sl in slots:
            s = s - sl
    return s & inner_outline(0.6)


def socket_cradles():
    """Wall slot + wall pocket (cuts) and cheeks + ceiling (adds) for every socket."""
    adds, cuts = [], []
    bl = P.SOCK_BODY[2]
    c = P.SOCK_CLR
    x_stop = P.SOCK_WALL + bl + c + 2.0 + 0.3            # room for the keeper fin that comes with the cover
    for s in P.sockets:
        x0, x1, y0, y1, z0, z1 = socket_frame(s)
        cuts.append(_slot(s))
        cuts.append(box(P.SOCK_WALL, P.WALL + 0.5, y0 - c, y1 + c, z0 - c, z1 + c))
        t = 1.6
        adds.append(box(P.WALL - 0.2, x_stop, y0 - c - t, y0 - c, P.COVER_T, P.z_in_top + 0.05))   # cheek
        adds.append(box(P.WALL - 0.2, x_stop, y1 + c, y1 + c + t, P.COVER_T, P.z_in_top + 0.05))   # cheek
        adds.append(box(P.WALL - 0.2, x_stop, y0 - c - t, y1 + c + t, z1 + c, z1 + c + 1.2))         # ceiling
    return adds, cuts


def _stadium_x(yc, zc, w, h, x0, x1):
    """Stadium prism along x: extent w along y and h along z, fully rounded ends."""
    r = min(w, h) / 2
    cyl = lambda dy, dz: Pos(x0, yc + dy, zc + dz) * Rot(0, 90, 0) * Cylinder(
        r, x1 - x0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    if w >= h:
        core = box(x0, x1, yc - (w / 2 - r), yc + (w / 2 - r), zc - r, zc + r)
        return core.fuse(cyl(-(w / 2 - r), 0), cyl(w / 2 - r, 0))
    core = box(x0, x1, yc - r, yc + r, zc - (h / 2 - r), zc + (h / 2 - r))
    return core.fuse(cyl(0, -(h / 2 - r)), cyl(0, h / 2 - r))


def _slot(s):
    """Stadium hole through the left wall."""
    return _stadium_x(s["y"], s["z"], P.slot_w, P.slot_h, -2.0, P.WALL + 1.0)


@lru_cache(None)
def top_case():
    z0 = P.COVER_T if P.LID else 0.0              # the lid sits on the tray; the fdm case wraps the inset cover
    body = prism(outline(), z0, P.H)
    body = chamfer(body.edges().group_by(Axis.Z)[-1], P.E_TOP)
    body = chamfer(body.edges().group_by(Axis.Z)[0], P.PART_CH if P.LID else P.E_BOT)
    body = cut(body, [prism(inner_outline(), -1, P.z_in_top)])
    # through openings in the panel, chamfered on top
    body = cut(body, [prism(tp_off(P.TP_CLR), -1, P.H + 1),
                      prism(rrect(P.kf_x0, P.kf_y0, P.kf_x1, P.kf_y1, P.KF_R), -1, P.H + 1)])
    top = body.faces().sort_by(Axis.Z)[-1]
    body = chamfer([e for w in top.inner_wires() for e in w.edges()], P.PC)
    # internal walls
    walls = prism(structure_sketch(), P.COVER_T, P.z_in_top + 0.05)
    adds, cuts = socket_cradles()
    for b in P.bulkheads:                                       # centre-seam bulkheads (straight seams)
        x0, x1 = P.W / 2 - P.BULKHEAD_T / 2, P.W / 2 + P.BULKHEAD_T / 2
        adds.append(box(x0, x1, b["y0"], b["y1"], P.COVER_T, P.z_in_top + 0.05))
        cuts.append(box(x0 - 1, x1 + 1, b["notch"][0], b["notch"][1], P.COVER_T - 1, P.COVER_T + P.NOTCH_H))
    body = fuse(body, [walls] + adds)
    # keep the device spaces clear
    z_pocket = (P.H - P.LIP_T) if P.TP_LIP > 0 else P.z_in_top      # pocket reaches up to the lip underside
    body = cut(body, [prism(bay(), -1, P.z_kb_top), prism(ring(), -1, z_pocket),
                      prism(tp_off(P.TP_CLR), P.z_in_top - 0.2, P.H + 1)])   # walls overlap the panel by 0.05
    body = fuse(body, crush_ribs() + (holders() if P.LID else []))
    if P.LID:
        cuts += lid_cuts()
    else:
        cuts += [Pos(bx, by, P.COVER_T - 1) * Cylinder(P.INSERT_R, P.INSERT_D + 1, align=(Align.CENTER, Align.CENTER, Align.MIN))
                 for bx, by in P.bosses]
    body = cut(body, cuts)
    return body


# ------------------------------------------------------------------ lid closure (service)
CYL = (Align.CENTER, Align.CENTER, Align.MIN)


def _mag_pocket_r():
    return (P.MAG_D + P.MAG_POCKET_CLR) / 2


def lid_cuts():
    """Top-case cuts: room for the tray's magnet pads, magnet pockets, pin holes, hook grooves, finger notch."""
    c = []
    z_face = P.COVER_T + P.MAG_PAD_H + 0.1                       # boss face, 0.1 above the tray pad
    for x, y in P.MAG_POS:
        c.append(Pos(x, y, P.COVER_T - 1) * Cylinder(P.MAG_BOSS_R + 0.6, z_face - P.COVER_T + 1, align=CYL))
        c.append(Pos(x, y, z_face - 0.01) * Cylinder(_mag_pocket_r(), P.MAG_H + 0.21, align=CYL))
    for x, y in P.PIN_POS:
        c.append(Pos(x, y, P.COVER_T - 1) * Cylinder(P.PIN_R0 + P.PIN_CLR, P.PIN_H + 1.5, align=CYL))
    yw = P.D - P.WALL                                            # inner face of the back wall
    for x in P.HOOK_X:
        # groove open to the bottom: only its upper lip (0.5 above the tooth) holds the lid down, so the
        # lid can swing up about its back edge without the wall below the groove sweeping into the tooth
        c.append(box(x - P.HOOK_W / 2 - 1, x + P.HOOK_W / 2 + 1, yw - 0.6, yw + P.HOOK_TOOTH + 0.4,
                     P.COVER_T - 1, P.COVER_T + P.HOOK_H - 0.4 + 0.5))
    c.append(box(P.W / 2 - P.PRY_W / 2, P.W / 2 + P.PRY_W / 2, -1, P.WALL + 1.6, P.COVER_T - 1, P.COVER_T + P.PRY_H))
    return c + snap_lid_cuts()


# ------------------------------------------------------------------ printed holders (service): no foam
LEAD = 1.5          # lead-in height on the entry end of every spring / pad


def _place(shape, origin, u, n_in):
    """Map a part built in a canonical frame (x along the wall, y into the cavity, z up) onto a wall."""
    from build123d import Location, Plane as _Pl, mirror
    ux, uy = u
    nx, ny = n_in
    if ux * ny - uy * nx < 0:            # canonical y = +90 deg from x; mirror if the wall normal is the other way
        shape = mirror(shape, about=_Pl.XZ)
    return Location((origin[0], origin[1], 0), (0, 0, math.degrees(math.atan2(uy, ux)))) * shape


def _lead_wedge(reach, z0, z1, length, entry_low):
    """Wedge that bevels the entry end of a finger / pad (canonical frame)."""
    a, b = 0.3, reach + 1.0
    if entry_low:
        poly = Polygon((a, z0 - 1), (b, z0 - 1), (b, z0 + LEAD * (b - a) / max(reach - a, 0.1)), (a, z0), align=None)
    else:
        poly = Polygon((a, z1 + 1), (b, z1 + 1), (b, z1 - LEAD * (b - a) / max(reach - a, 0.1)), (a, z1), align=None)
    return Pos(-3, 0, 0) * extrude(Plane.YZ * poly, length + 6)


def spring(origin, u, n_in, reach, z0, z1, entry_low=True):
    """Printed leaf spring: a 1 mm PA12 finger growing out of a wall at a shallow angle, round tip.
    reach = how far the tip stands off the wall face (gap to the device + preload)."""
    t, L = P.SPRING_T, P.SPRING_L
    th = math.degrees(math.asin(min((reach - t / 2) / L, 0.9)))
    tip = (L * math.cos(math.radians(th)), L * math.sin(math.radians(th)))
    sk = (Rot(0, 0, th) * Pos(L / 2, 0) * Rectangle(L, t)) + (Pos(*tip) * Circle(t / 2)) + rect(-1.0, -0.6, 2.0, 0.35)
    f = prism(Sketch() + sk.faces(), z0, z1) - _lead_wedge(reach, z0, z1, L, entry_low)
    return _place(f, origin, u, n_in)


def datum_pad(origin, u, n_in, thick, z0, z1, entry_low=True, width=8.0):
    """Rigid pad whose face is the datum the springs push the device against."""
    f = box(-width / 2, width / 2, -0.6, thick, z0, z1) - _lead_wedge(thick, z0, z1, width, entry_low)
    return _place(Pos(width / 2, 0, 0) * f, origin, u, n_in)


def holder_specs():
    """(kind, device, origin, u, n_in, reach, z0, z1, entry_low) of every printed spring in the lid.
    Opposing springs centre each device, so the bureau's scale error splits evenly between both sides.
    The Joro's front edge rests on the seam rib (a short span, so a one-sided datum is fine there)."""
    s = []
    pre = P.SPRING_PRELOAD
    tana_k, tana_t = math.tan(P.ka), math.tan(P.ta)
    L_ = P.SPRING_L
    # --- Joro (pressed in from below with the lid upside down: lead-in at the low end)
    z0k, z1k = 12.5, P.z_kb_top - 0.8
    for yc in (P.kb_fy + 20.0, P.kb_fy + 80.0):
        s.append(("spring", "kb", (P.WALL, yc - L_ / 2), (0, 1), (1, 0), P.KB_CLR + pre, z0k, z1k, True))
        s.append(("spring", "kb", (P.W - P.WALL, yc - L_ / 2), (0, 1), (-1, 0), P.KB_CLR + pre, z0k, z1k, True))
    kb_tb = P.kb_fy + P.kb_plan_d
    zb0, zb1 = 10.0, P.z_kb_top - 1.0
    gap_b = (P.D - P.WALL) - (kb_tb - (P.z_kb_top - zb1) * tana_k)
    for xc in (80.0, P.W / 2, P.W - 80.0):
        s.append(("spring", "kb", (xc - L_ / 2, P.D - P.WALL), (1, 0), (0, -1), gap_b + pre, zb0, zb1, True))
    # --- trackpad (pushed in from below, glass first, onto the lip: lead-in at the low end)
    L, R, F, B = P.TP_RING
    z1t = min(P.z_in_top - 0.2, P.z_tp_top - 1.5)         # stay below the glass layer
    cx = (P.tp_gx0 + P.tp_gx1) / 2
    for yc in (P.tp_gy0 + 30.0, P.tp_gy1 - 30.0):
        z0 = P.tp_bottom(yc - L_ / 2) + 0.5                 # bottom of the side face is highest at the front end
        s.append(("spring", "tp", (P.tp_gx0 - L, yc - L_ / 2), (0, 1), (1, 0), L + pre, z0, z1t, True))
        s.append(("spring", "tp", (P.tp_gx1 + R, yc - L_ / 2), (0, 1), (-1, 0), R + pre, z0, z1t, True))
    z0f = P.tp_bottom(P.tp_gy0 - P.tp_lean_f) + 0.5
    lean_lo = (P.z_tp_top - z0f) * tana_t                  # front face sticks out most at its bottom
    z0b = P.tp_bottom(P.tp_gy1) + 0.5
    lean_hi = (P.z_tp_top - z1t) * tana_t                  # back face sticks out most at its top
    for xc in (cx - 45.0, cx + 45.0):
        s.append(("spring", "tp", (xc - L_ / 2, P.tp_gy0 - F), (1, 0), (0, 1), F - lean_lo + pre, z0f, z1t, True))
        s.append(("spring", "tp", (xc - L_ / 2, P.tp_gy1 + B), (1, 0), (0, -1), B + lean_hi + pre, z0b, z1t, True))
    return s


@lru_cache(None)
def _holders():
    out = []
    for kind, dev, o, u, n, r, z0, z1, low in holder_specs():
        out.append(spring(o, u, n, r, z0, z1, low) if kind == "spring" else datum_pad(o, u, n, r, z0, z1, low))
    return tuple(out)


def holders():
    return list(_holders())


def springs_only():
    return [h for h, spec in zip(_holders(), holder_specs()) if spec[0] == "spring"]


# ------------------------------------------------------------------ snap clips (service): no magnets
def _snap_zt():
    return P.COVER_T + P.SNAP_L


def snap_teeth():
    """The hook teeth on the tray's snap arms (they deflect when the lid closes)."""
    out = []
    yaf, zt = P.WALL + P.SNAP_GAP, _snap_zt()
    poly = Polygon((yaf + 0.01, zt), (yaf - P.SNAP_TOOTH, zt - 1.6), (yaf - P.SNAP_TOOTH, zt - 2.0), (yaf + 0.01, zt - 3.0), align=None)
    for sx in P.SNAP_X:
        out.append(Pos(sx - P.SNAP_W / 2 + 1, 0, 0) * extrude(Plane.YZ * poly, P.SNAP_W - 2))
    return out


def snap_arms():
    yaf = P.WALL + P.SNAP_GAP
    return [box(sx - P.SNAP_W / 2, sx + P.SNAP_W / 2, yaf, yaf + P.SNAP_T, P.COVER_T - 0.2, _snap_zt()) for sx in P.SNAP_X]


def snap_lid_cuts():
    """Grooves in the lid's front wall for the teeth, and free space behind the arms so they can flex."""
    c = []
    zt = _snap_zt()
    engage = P.SNAP_TOOTH - P.SNAP_GAP                       # how far the tooth reaches into the wall
    for sx in P.SNAP_X:
        c.append(box(sx - P.SNAP_W / 2, sx + P.SNAP_W / 2, P.WALL - engage - 0.3, P.WALL + 0.5, zt - 3.15, zt + 0.0))
        c.append(box(sx - P.SNAP_W / 2 - 1.5, sx + P.SNAP_W / 2 + 1.5, P.WALL, P.WALL + P.SNAP_GAP + P.SNAP_T + 2.0,
                     P.COVER_T - 1, zt + 1.0))
    return c


def tray_features():
    """Tray adds: magnet pads, alignment pins, back hooks (tab + tooth). Returns (adds, cuts)."""
    adds, cuts = [], []
    zb = P.COVER_T - 0.2
    for x, y in P.MAG_POS:
        top = P.COVER_T + P.MAG_PAD_H
        adds.append(Pos(x, y, zb) * Cylinder(P.MAG_BOSS_R, top - zb, align=CYL))
        cuts.append(Pos(x, y, top - P.MAG_H - 0.2) * Cylinder(_mag_pocket_r(), P.MAG_H + 1, align=CYL))
    for x, y in P.PIN_POS:
        adds.append(Pos(x, y, zb) * Cone(P.PIN_R0, P.PIN_R1, P.PIN_H, align=CYL))
    yw = P.D - P.WALL
    for x in P.HOOK_X:
        adds.append(box(x - P.HOOK_W / 2, x + P.HOOK_W / 2, yw - 0.3 - P.HOOK_T, yw - 0.3, zb, P.COVER_T + P.HOOK_H))
        adds.append(box(x - P.HOOK_W / 2 + 1, x + P.HOOK_W / 2 - 1, yw - 0.35, yw - 0.3 + P.HOOK_TOOTH,
                        P.COVER_T + P.HOOK_H - 1.8, P.COVER_T + P.HOOK_H - 0.4))
    adds += snap_arms() + snap_teeth()
    return adds, cuts


# ------------------------------------------------------------------ cover
def cover_outline():
    return inner_outline(-P.COVER_GAP)


def rail(x, y0, y1, ztop, width=2.0, zb=None):
    """Rail along y whose top follows ztop(y) (linear); trimmed where it would be lower than the plate."""
    zb = P.COVER_T - 0.4 if zb is None else zb
    lo = P.COVER_T + 0.3
    if ztop(y0) < lo and ztop(y1) < lo:
        return None
    # trim the end that dips into the plate
    if ztop(y1) < lo:
        y1 = y0 + (y1 - y0) * (ztop(y0) - lo) / (ztop(y0) - ztop(y1))
    if ztop(y0) < lo:
        y0 = y1 - (y1 - y0) * (ztop(y1) - lo) / (ztop(y1) - ztop(y0))
    prof = Polygon((y0, zb), (y1, zb), (y1, ztop(y1)), (y0, ztop(y0)), align=None)
    return Pos(x - width / 2, 0, 0) * extrude(Plane.YZ * prof, width)


def kb_rail_solids():
    r = [rail(x, P.kb_fy + 3, P.kb_end - 3, lambda y: P.kb_bottom(y) - P.KB_PAD) for x in P.kb_rails]
    return [q for q in r if q is not None]


@lru_cache(None)
def _tp_rails():
    """Trackpad rails, carried by the cover / tray (wider on the service tray: they take the clicks)."""
    w = 3.0 if P.SVC else 2.0
    r = [rail(x, P.tp_gy0 + 4, P.tp_gy1 - 4, lambda y: P.tp_bottom(y) - P.TP_PAD, width=w) for x in P.tp_rails]
    return tuple(q for q in r if q is not None)


def tp_rail_solids():
    return list(_tp_rails())


def rails():
    """Rails carried by the cover/tray."""
    return kb_rail_solids() + tp_rail_solids()


def keepers():
    """Socket keepers on the cover: a pad under each socket body and a forked fin behind it."""
    out = []
    for s in P.sockets:
        x0, x1, y0, y1, z0, z1 = socket_frame(s)
        zb = P.COVER_T - 0.4
        out.append(box(P.WALL + 0.6, x1 - 0.5, y0 + 0.5, y1 - 0.5, zb, z0 - P.SOCK_PAD))
        fx0 = x1 + P.SOCK_CLR
        cg = min(6.0, P.sock_w - 2.0)                      # U-slot for the cable leaving the body
        fin = box(fx0, fx0 + 2.0, y0, y1, zb, z1 - 0.3)
        out.append(fin - box(fx0 - 1, fx0 + 3, s["y"] - cg / 2, s["y"] + cg / 2, s["z"] - 2.5, z1 + 1))
    return out


def seam_lines_cover():
    """(kind, coordinate, from, to) of cover seams, used for keep-out bands."""
    return [("x", P.X_COVER, 0, P.D), ("y", P.Y_COVER_L, 0, P.X_COVER), ("y", P.Y_COVER_R, P.X_COVER, P.W)]


def cover_keep(g=0.0):
    """Solid (unperforated) regions of the cover, each grown by g."""
    k = [inner_outline(-P.COVER_GAP) - inner_outline(-P.COVER_GAP - 6.0 - g)]   # edge band
    k += [Pos(bx, by) * Circle(6.0 + g) for bx, by in P.bosses]
    for x in P.kb_rails:
        k.append(rect(x - 3 - g, P.kb_fy - g, x + 3 + g, P.kb_end + g))
    for x in P.tp_rails:
        k.append(rect(x - 3 - g, P.tp_gy0 - g, x + 3 + g, P.tp_gy1 + g))
    k += [Pos(fx, fy) * Circle(7.5 + g) for fx, fy in P.feet]
    for s in P.sockets:
        x0, x1, y0, y1, z0, z1 = socket_frame(s)
        k.append(rect(0, y0 - 3 - g, x1 + 6 + g, y1 + 3 + g))
    band = P.TAB["depth"] + 3.0 + g
    for kind, c, a, b in seam_lines_cover():
        k.append(rect(c - band, a, c + band, b) if kind == "x" else rect(a, c - band, b, c + band))
    return sk_union(k)


def cover_holes():
    """Isogrid triangles with rounded corners, clipped to the perforable region."""
    region = cover_outline() - cover_keep(P.HOLE_FILLET)
    per = P.P_COV
    side = 2 * per / math.sqrt(3)
    A = (per, per / math.sqrt(3))
    B = (0.0, side)
    shrink = P.WEB / 2 + P.HOLE_FILLET
    r_in = per / 3
    if r_in - shrink < 0.8:
        return []
    s = (r_in - shrink) / r_in
    x_anchor = P.W / 2
    holes = []
    rb = region.bounding_box()
    imax = int(P.W / per) + 3
    jmax = int(P.D / side) + 3
    for i in range(-imax, imax + 1):
        for j in range(-jmax - imax, jmax + imax + 1):
            p0 = (x_anchor + i * A[0] + j * B[0], i * A[1] + j * B[1])
            p1 = (p0[0] + A[0], p0[1] + A[1])
            p2 = (p0[0] + B[0], p0[1] + B[1])
            p3 = (p0[0] + A[0] + B[0], p0[1] + A[1] + B[1])
            for tri in ((p0, p1, p2), (p1, p3, p2)):
                cx = sum(p[0] for p in tri) / 3
                cy = sum(p[1] for p in tri) / 3
                if not (rb.min.X - side < cx < rb.max.X + side and rb.min.Y - side < cy < rb.max.Y + side):
                    continue
                pts = [(cx + (px - cx) * s, cy + (py - cy) * s) for px, py in tri]
                holes.append(Polygon(*pts, align=None))
    tri_all = Sketch() + [f for h in holes for f in h.faces()]
    clipped = tri_all & region
    out = []
    for f in clipped.faces():
        if f.area < 6.0:
            continue
        try:                                   # drop slivers narrower than ~1 mm (before rounding)
            if not offset(f, -0.5, kind=Kind.INTERSECTION).faces():
                continue
        except Exception:
            continue
        g = offset(f, P.HOLE_FILLET, kind=Kind.ARC)
        out.extend(g.faces() if hasattr(g, "faces") else [g])
    return out


@lru_cache(None)
def cover():
    if P.LID:
        return tray()
    plate = prism(cover_outline(), 0, P.COVER_T)
    holes = cover_holes() if P.COVER_HOLES else []
    if holes:
        plate = cut(plate, [prism(Sketch() + holes, -1, P.COVER_T + 1)])
    plate = fuse(plate, rails() + keepers())
    cuts = []
    for bx, by in P.bosses:
        cone_h = (P.CSK_D / 2 - P.SCREW_R)
        cuts.append(Pos(bx, by, -0.001) * Cone(P.CSK_D / 2, P.SCREW_R, cone_h, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        cuts.append(Pos(bx, by, -1) * Cylinder(P.SCREW_R, P.COVER_T + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    for fx, fy in P.feet:
        cuts.append(Pos(fx, fy, -1) * Cylinder(P.FOOT_R, 1 + P.FOOT_DEPTH, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    return cut(plate, cuts)


def tray():
    """Full-footprint solid tray: the lid (top case) sits on it."""
    plate = prism(outline(), 0, P.COVER_T)
    plate = chamfer(plate.edges().group_by(Axis.Z)[0], P.E_BOT)
    plate = chamfer(plate.edges().group_by(Axis.Z)[-1], P.PART_CH)
    adds, cuts = tray_features()
    plate = fuse(plate, rails() + adds)
    cuts += [Pos(fx, fy, -1) * Cylinder(P.FOOT_R, 1 + P.FOOT_DEPTH, align=CYL) for fx, fy in P.feet]
    return cut(plate, cuts)


# ------------------------------------------------------------------ fit-test pieces (print these first)
def fit_keyboard():
    """Panel strip around the key field + a 4 mm rim on the bay outline. Lay it on the Joro (sitting on the
    desk): the keys must stand up through the opening with an even gap and still clear the panel when pressed;
    the rim must slide over the Joro outline. Returned as (left half, right half)."""
    bay_o = rrect(P.kb_x0 - 3, P.kb_y0 - 3, P.W - P.WALL + 3, P.kb_end + 3, P.KB_R + P.KB_CLR + 3)
    plate = prism(bay_o, P.z_kb_top, P.H)
    plate = chamfer(plate.edges().group_by(Axis.Z)[-1], P.E_TOP)
    plate = cut(plate, [prism(rrect(P.kf_x0, P.kf_y0, P.kf_x1, P.kf_y1, P.KF_R), P.z_kb_top - 1, P.H + 1)])
    top = plate.faces().sort_by(Axis.Z)[-1]
    plate = chamfer([e for w in top.inner_wires() for e in w.edges()], P.PC)
    rim = prism(rrect(P.kb_x0 - 1.6, P.kb_y0 - 1.6, P.W - P.WALL + 1.6, P.kb_end + 1.6, P.KB_R + P.KB_CLR + 1.6) - bay(),
                P.z_kb_top - 4.0, P.z_kb_top + 0.05)
    g = plate.fuse(rim).clean()
    left = g & box(-10, P.W / 2, -10, P.D + 10, -10, 40)
    right = g & box(P.W / 2, P.W + 10, -10, P.D + 10, -10, 40)
    return left, right


def fit_trackpad():
    """Trackpad opening + pocket wall with the crush ribs, 5 mm deep. Push the trackpad in from below:
    it should grip, sit centred with an even gap, and the glass should be 0.3 below the plate top when the
    plate is flat on the desk upside down with a 0.3 mm shim under the glass."""
    o = max(P.TP_RING) + P.RING_T + 4.0
    plate = prism(tp_off(o), P.z_in_top, P.H)
    plate = chamfer(plate.edges().group_by(Axis.Z)[-1], P.E_TOP)
    plate = cut(plate, [prism(tp_off(P.TP_CLR), P.z_in_top - 1, P.H + 1)])
    top = plate.faces().sort_by(Axis.Z)[-1]
    plate = chamfer([e for w in top.inner_wires() for e in w.edges()], P.PC)
    wall = prism(ring(P.RING_T) - ring(), P.z_in_top - 5.0, P.z_in_top + 0.05)
    return fuse(plate.fuse(wall), crush_ribs())


def fit_socket():
    """The trackpad socket corner of the real top case (wall slot, wall pocket, cheeks, ceiling)."""
    s = P.sockets[0]
    return top_case() & box(-1, P.SOCK_WALL + P.SOCK_BODY[2] + 8, s["y"] - 10, s["y"] + 10, -1, P.H + 1)
