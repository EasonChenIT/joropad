"""Joro + Magic Trackpad deck: every parameter and the derived layout.

Units mm. Axes as in v8: x to the right, y toward the back (y=0 is the edge nearest the user),
z up (z=0 is the desk). Device dimensions come from measurements.json (IDs match docs/measure_sheet.md).
Everything below the "derived" line is computed; edit only the inputs above it.

PROFILE "service": one-piece parts for a print bureau (JLC3DP MJF PA12). Generous clearances, foam
                   centring and self-tapping screws, so the first print fits even with +/-0.3% bureau tolerance.
PROFILE "fdm"    : v9 - eight tiles for a 256 mm home printer (PETG), tight fits, heat-set inserts.
"""
import json as _json, math, os as _os

PROFILE = _os.environ.get("DECK_PROFILE", "service")

# ======================================================================================
# Devices (from measurements.json)
# ======================================================================================
_MPATH = _os.environ.get("DECK_MEASUREMENTS", _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "measurements.json"))
M = _json.load(open(_MPATH, encoding="utf-8"))
MEASURED = bool(M.get("confirmed"))
_R = lambda d: d / (math.sqrt(2) - 1)        # corner radius from the corner-to-arc distance along the diagonal

KB_W, KB_D = M["K1_joro_width"], M["K2_joro_depth_bottom"]
KB_BACK_H = M["K3_joro_back_height"]
KB_FRONT_H = M["K4_joro_front_height"]
KB_R = _R(M["K5_joro_corner_d"])
KF_INSET = (M["K6_keys_inset_left"], M["K7_keys_inset_right"], M["K8_keys_inset_front"], M["K9_keys_inset_back"])
KEYCAP_H = M["K10_keycap_above_plate"]
KEY_TRAVEL = M["K10_keycap_above_plate"] - M["K11_keycap_above_plate_pressed"]
KB_PORT_FACE = M["K13_joro_port_face"]
KB_PORT_X = M["K14_joro_port_from_left"]

TP_W, TP_D = M["T1_tp_width"], M["T2_tp_depth_bottom"]
TP_FRONT_H, TP_BACK_H = M["T3_tp_front_height"], M["T4_tp_back_height"]
TP_R = _R(M["T5_tp_corner_d"])
TP_PORT_X = M["T6_tp_port_from_left"]
PLUG_HEAD = M["P1_plug_head_length"]
PLUG_W = M["P2_plug_head_width"]

SVC = PROFILE == "service"
# ======================================================================================
# Shell and structure            (service value if different, else fdm value)
# ======================================================================================
SKIN = 1.5 if SVC else 1.2           # top panel thickness (palm rests and frame)
KB_SKIN = 1.2                        # panel thickness above the keyboard (thin to 0.8 if the key caps stand too low)
WALL = 2.4                           # outer side wall
COVER_T = 1.6                        # bottom cover plate
COVER_GAP = 0.5 if SVC else 0.2      # cover <-> wall gap, per side
KB_PAD = 0.6 if SVC else 0.5         # rail -> Joro gap, filled with 1.0 mm EVA (service) / 0.5 mm EVA (fdm)
TP_PAD = 0.6 if SVC else 0.5         # rail -> trackpad gap, filled with 1.0 mm double-sided foam tape
TP_DROP = 0.3                        # trackpad glass below the deck top
TP_CLR = 0.5 if SVC else 0.3         # visible gap glass <-> top opening
TP_RING_CLR = 1.0 if SVC else 0.5    # pocket wall <-> glass outline (service: 1.5 mm EVA pads centre the trackpad)
RING_T = 1.2                         # trackpad pocket wall
CRUSH = 0.0 if SVC else 0.15         # crush-rib interference; 0 disables the ribs
KB_CLR = 1.0 if SVC else 0.4         # keyboard bay clearance (service: 1.5 mm EVA strips centre the Joro)
KF_R = M["K12_keycap_corner_r"] + (0.8 if SVC else 0.5)
KEY_CLR = 0.8 if SVC else 0.5        # gap between key caps and the opening edge
CORNER_R = 10.0                      # plan corner radius of the deck
E_TOP, E_BOT = 1.0, 0.8              # 45-degree chamfers on the outer top / bottom edges
PC = 0.4                             # chamfer on the top edges of both openings
FRONT_MARGIN = 4.0                   # deck front edge -> trackpad opening
SEAM_RIB = 4.0 if not SVC else 3.0   # full-width rib between trackpad channel and keyboard bay
BACK_WALL = 1.2                      # keyboard back wall
RIB = 1.6                            # palm-rest isogrid rib thickness
P_TOP = 24.0                         # palm-rest isogrid period
WEB = 2.4                            # cover isogrid web
P_COV = 18.0                         # cover isogrid period
HOLE_FILLET = 1.5                    # corner radius of the cover isogrid holes
BOSS_R = 3.75                        # screw boss
INSERT_R = 1.25 if SVC else 2.1      # service: pilot for ST3.0 self-tapping screws; fdm: M3 heat-set insert (d4.2)
INSERT_D = 8.0 if SVC else 6.0
CSK_D = 6.4 if SVC else 6.0          # countersink diameter in the cover
SCREW_R = 1.8 if SVC else 1.7        # screw clearance in the cover
FOOT_R, FOOT_DEPTH = 5.25, 0.6

# ======================================================================================
# USB-C panel sockets (both on the left face) - module dimensions from measurements.json
# ======================================================================================
SOCK_SLOT = (M["U5_socket_shell_width"] + 0.66, M["U6_socket_shell_height"] + 0.64)   # stadium hole in the wall
SOCK_BODY = (M["U1_socket_body_width"], M["U2_socket_body_height"], M["U3_socket_body_depth"])
SOCK_WALL = max(0.8, min(M["U4_socket_shell_protrusion"], WALL))   # wall left in front of the body
SOCK_CLR = 0.5 if SVC else 0.3
SOCK_PAD = 1.0                       # foam between the cover keeper and the socket body
SOCK_ORIENT = "h"                    # "h": slot horizontal (like a laptop). "v": slot vertical, saves ~5 mm of depth

# ======================================================================================
# Printing
# ======================================================================================
SPLIT = not SVC                      # service: one-piece top case and cover; fdm: tiles
BUILD_VOLUME = (370.0, 276.0, 360.0) # JLC3DP MJF PA12 / PA12-HP
SEAM_STYLE = "straight"              # fdm only. "straight": centre line + seam rib, hidden by the two openings,
                                     #   reinforced by bulkheads. "dovetail": interlocking, outline shows on top.
BED = 256.0
BED_MARGIN = 3.0                     # every fdm tile must fit in BED - 2*BED_MARGIN
GAP = 0.25                           # total gap in every puzzle joint (0.125 per side)
TAB = dict(depth=6.0, neck=7.0, head=11.0)     # dovetail
LUG = dict(depth=8.0, width=12.0)              # rectangular lug that carries a screw boss
DENSITY = 1.01 if SVC else 1.27      # MJF PA12 / PETG, g/cm3 (solid)

# ======================================================================================
# Overrides for experiments: DECK_PARAMS='{"KB_SKIN": 0.8, "SEAM_STYLE": "dovetail"}' python build.py
# ======================================================================================
import json as _json, os as _os
for _k, _v in _json.loads(_os.environ.get("DECK_PARAMS", "{}")).items():
    if _k not in globals() or not _k.isupper():
        raise KeyError(f"DECK_PARAMS: unknown parameter {_k}")
    globals()[_k] = tuple(_v) if isinstance(_v, list) else _v

# ======================================================================================
# Derived layout (do not edit below)
# ======================================================================================
ka = math.atan((KB_BACK_H - KB_FRONT_H) / KB_D)          # keyboard tilt (rad)
ta = math.atan((TP_BACK_H - TP_FRONT_H) / TP_D)          # trackpad tilt (rad)
# plan extents of the tilted devices, measured from their front-bottom edge
kb_top_y0 = KB_FRONT_H * math.sin(ka)                    # front top edge sits behind the front bottom edge
kb_plan_d = KB_D * math.cos(ka) + KB_BACK_H * math.sin(ka)   # front-bottom edge -> back-top edge
kb_top_len = KB_D / math.cos(ka)
kb_vext = KB_FRONT_H * math.cos(ka) + KB_D * math.sin(ka)    # vertical extent once the top is level
tp_lean_f = TP_FRONT_H * math.sin(ta)                    # front-bottom edge sticks out ahead of the glass edge
tp_top_len = TP_D / math.cos(ta)
tp_vext = TP_FRONT_H * math.cos(ta) + TP_D * math.sin(ta)

H = KB_SKIN + kb_vext + KB_PAD + COVER_T
W = KB_W + 2 * KB_CLR + 2 * WALL
z_kb_top = H - KB_SKIN               # aluminium top plate of the Joro
z_tp_top = H - TP_DROP               # trackpad glass
z_in_top = H - SKIN                  # underside of the panel (palm area)

# --- trackpad, channel, seam rib --------------------------------------------------------
tp_gx0 = (W - TP_W) / 2              # glass outline
tp_gx1 = tp_gx0 + TP_W
tp_gy0 = FRONT_MARGIN + TP_CLR
tp_gy1 = tp_gy0 + tp_top_len
tp_ring_in = TP_RING_CLR             # offsets of the pocket wall from the glass outline
tp_ring_out = TP_RING_CLR + RING_T
cf = tp_gy1 + tp_ring_out            # front face of the trackpad cable channel
sock_w, sock_h = (SOCK_BODY[0], SOCK_BODY[1]) if SOCK_ORIENT == "h" else (SOCK_BODY[1], SOCK_BODY[0])
slot_w, slot_h = SOCK_SLOT if SOCK_ORIENT == "h" else SOCK_SLOT[::-1]
CW = max(PLUG_HEAD + 0.5 - tp_ring_out, sock_w + 2 * SOCK_CLR)      # channel width
ys = cf + CW + SEAM_RIB / 2          # y of the seam rib centre line
kb_y0 = cf + CW + SEAM_RIB           # keyboard bay front
kb_x0 = WALL                         # keyboard bay left
kb_fy = kb_y0 + KB_CLR               # Joro front-bottom edge
kb_ty0 = kb_fy + kb_top_y0           # Joro top plate front edge (plan)
kb_ty1 = kb_ty0 + kb_top_len
kb_end = kb_fy + kb_plan_d + KB_CLR  # keyboard bay back
bw1 = kb_end + BACK_WALL             # back face of the keyboard back wall
# rear zone: 90-degree plug head, and the second socket on the flat part of the left face
rz_plug = KB_CLR + PLUG_HEAD + 1.0 - BACK_WALL
rz_sock = (sock_w + 2 * SOCK_CLR) + CORNER_R - WALL
D = bw1 + max(rz_plug, rz_sock) + WALL
z_sock = (COVER_T + z_in_top) / 2
sockets = [
    dict(name="trackpad", y=cf + CW / 2, z=z_sock),
    dict(name="keyboard", y=bw1 + SOCK_CLR + sock_w / 2, z=z_sock),
]
kb_port = kb_x0 + KB_CLR + KB_PORT_X
tp_port = tp_gx0 + TP_PORT_X

# key field (plan), on the Joro top plate
kf_x0 = kb_x0 + KB_CLR + KF_INSET[0] - KEY_CLR
kf_x1 = kb_x0 + KB_CLR + KB_W - KF_INSET[1] + KEY_CLR
kf_y0 = kb_ty0 + KF_INSET[2] - KEY_CLR
kf_y1 = kb_ty1 - KF_INSET[3] + KEY_CLR

# palm-rest isogrid zones (inside the outer wall, outside the trackpad pocket, in front of the channel)
palm_zones = [(WALL, tp_gx0 - tp_ring_out), (tp_gx1 + tp_ring_out, W - WALL)]

# --- seams of the top case (each tile <= BED - 2*BED_MARGIN) -----------------------------
if SEAM_STYLE == "straight":
    X_FRONT = X_REAR = W / 2         # through the trackpad opening and the key field: only short stubs show
else:
    X_FRONT = 56.0                   # in the left palm rest, clear of the trackpad opening
    X_REAR = W / 2                   # through the keyboard frame (staggered against X_FRONT)
# --- seams of the cover (staggered against the top seams, T-junctions only) ---------------
X_COVER = W / 2 + 45.0
Y_COVER_L = 36.0                     # between the boss rows y=12 and y=60
Y_COVER_R = 84.0                     # between the boss rows y=60 and y=108

# --- screw bosses (M3 inserts; the cover screws into all of them) -------------------------
y_rz_boss = bw1 + BOSS_R - 0.2       # rear-zone bosses hug the keyboard back wall
bosses = []
if SEAM_STYLE == "straight":
    seam_boss_y = ys - 0.3 - BOSS_R  # on the front face of the seam rib, wholly in the front tiles
    for x in (12.0, 62.0, W - 62.0, W - 12.0):
        for y in (12.0, 60.0, 108.0):
            bosses.append((x, y))
    bosses += [(37.0, 12.0), (W - 37.0, 12.0)]
    SEAM_LUG_X = []
    bosses += [(x, seam_boss_y) for x in (30.0, W / 2 - 14.0, W / 2 + 14.0, W - 30.0)]
    bosses += [(x, y_rz_boss) for x in (60.0, 105.0, W / 2 - 14.0, W / 2 + 14.0, W - 60.0, W - 14.0)]
    # full-height bulkheads on the centre seam (glue faces), with a cable notch at the bottom
    bulkheads = [] if not SPLIT else [dict(y0=cf - 0.2, y1=ys, notch=(cf + 0.8, cf + 8.0)),
                 dict(y0=bw1 - 0.2, y1=D - WALL + 0.2, notch=(y_rz_boss + BOSS_R + 0.5, D - WALL - 1.0))]
else:
    seam_boss_y = kb_y0 - BOSS_R - 0.4   # inside the lugs of the rear tiles, entirely in front of the bay
    for x in (12.0, X_FRONT - 10.0, X_FRONT + 9.0, W - 64.0, W - 12.0):
        for y in (12.0, 60.0, 108.0):
            bosses.append((x, y))
    SEAM_LUG_X = [40.0, 118.0, W / 2 + 15.0, W - 40.0]      # lugs of the rear tiles reaching into the channel
    bosses += [(x, seam_boss_y) for x in SEAM_LUG_X]
    bosses += [(x, y_rz_boss) for x in (60.0, X_REAR - 14.0, X_REAR + 14.0, W - 60.0, W - 14.0)]
    bulkheads = []
BULKHEAD_T = 4.0
NOTCH_H = 6.0

# --- cover support rails ------------------------------------------------------------------
kb_rails = [kb_x0 + KB_CLR + v for v in (12.0, 80.0, 149.0, 218.0, 286.0)]
tp_rails = [tp_gx0 + v for v in (14.0, 80.0, 146.0)]
feet = [(20.0, 20.0), (W - 20.0, 20.0), (20.0, D - 20.0), (W - 20.0, D - 20.0)]


def kb_bottom(y):
    """z of the Joro's (tilted) bottom face at plan position y."""
    return z_kb_top - KB_FRONT_H * math.cos(ka) - (y - kb_fy) * math.tan(ka)


def tp_bottom(y):
    tp_fy = tp_gy0 - tp_lean_f
    return z_tp_top - TP_FRONT_H * math.cos(ta) - (y - tp_fy) * math.tan(ta)


def summary():
    rows = [
        ("deck W x D x H", f"{W:.1f} x {D:.1f} x {H:.2f}"),
        ("keyboard tilt / front height", f"{math.degrees(ka):.2f} deg / {KB_FRONT_H:.2f}"),
        ("Joro plan depth (tilted)", f"{kb_plan_d:.2f}  (footprint {KB_D})"),
        ("Joro bottom front / back z", f"{kb_bottom(kb_fy):.2f} / {kb_bottom(kb_fy + KB_D * math.cos(ka)):.2f}"),
        ("trackpad tilt", f"{math.degrees(ta):.2f} deg, glass plan depth {tp_top_len:.2f}"),
        ("trackpad bottom front / back z", f"{tp_bottom(tp_gy0 - tp_lean_f):.2f} / {tp_bottom(tp_gy0 - tp_lean_f + TP_D * math.cos(ta)):.2f}"),
        ("channel width", f"{CW:.2f}"),
        ("seam rib centre ys / bay", f"{ys:.2f} / {kb_y0:.2f}..{kb_end:.2f}"),
        ("rear zone (bay -> outside)", f"{D - kb_end:.2f}"),
        ("key cap proud of the deck", f"{KEYCAP_H - KB_SKIN:.2f} (pressed: {KEYCAP_H - KB_SKIN - KEY_TRAVEL:.2f})"),
        ("profile", PROFILE + ("" if MEASURED else "  (measurements NOT confirmed: estimates)")),
        ("seam style", SEAM_STYLE if SPLIT else "one piece"),
        ("bosses / M3 screws", f"{len(bosses)}"),
    ]
    return "\n".join(f"  {k:32s} {v}" for k, v in rows)


if __name__ == "__main__":
    print(summary())
