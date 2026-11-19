"""v8: flat-top laptop-style deck. Top case (skin + walls + isogrid core + bosses) and bottom cover
(isogrid plate + sloped support rails). Keyboard and trackpad are inserted from below.
Usage: python3 build_v8.py top|cover [res]   -> writes <part>_verts.npy / <part>_faces.npy
"""
import numpy as np, math, sys, time
from skimage.measure import marching_cubes

PART = sys.argv[1] if __name__ == "__main__" else None; RES = float(sys.argv[2]) if __name__ == "__main__" and len(sys.argv) > 2 else 0.4

# ---------------- device data ----------------
kb_w, kb_d, kb_back_h = 298, 112, 16.5          # Joro: back frame height (no keycaps)
kb_angle = 4.6                                  # Joro typing angle (review data)
t_kb = math.tan(math.radians(kb_angle))
kb_front_h = kb_back_h - kb_d * t_kb            # ~7.5
kf_inset = (6, 6, 6, 6)                         # key field inset from Joro outline: left, right, front, back (MEASURE)
key_clr = 0.5
tp_w0, tp_d0, tp_front_h, tp_back_h, tp_r = 160, 114.9, 4.9, 10.9, 9
t_tp = (tp_back_h - tp_front_h) / tp_d0

# ---------------- structure ----------------
skin = 1.2; wall = 2.4; cover_t = 1.6; pad = 0.5     # pad = EVA foam between rails and devices
tp_drop = 0.3; tp_clr = 0.3; kb_clr = 0.4
corner_r = 10; e_top = 1.0; e_bot = 0.8; pc = 0.4
front_margin = 4; gap_mid = 14; seam_rib = 3; rear_zone = 13
rib = 1.6; P_top = 24                              # top core isogrid
web = 2.4; P_cov = 18                              # cover isogrid
boss_r = 3.75; insert_r = 2.1; insert_d = 6        # M3 heat-set insert (d4.2 hole)
H = skin + kb_back_h + pad + cover_t               # 19.8

W = kb_w + 2*kb_clr + 2*wall
kb_x0 = wall; kbw = kb_w + 2*kb_clr; kbd = kb_d + 2*kb_clr
tp_x0 = (W - tp_w0)/2 - tp_clr; tp_y0 = front_margin; tpw = tp_w0 + 2*tp_clr; tpd = tp_d0 + 2*tp_clr
tp_end = tp_y0 + tpd
kb_y0 = tp_end + gap_mid; kb_end = kb_y0 + kbd
D = kb_end + rear_zone
ys_seam = kb_y0 - seam_rib/2
y_rear = D - wall - boss_r
palm_x = [(wall, tp_x0 - 1.2), (tp_x0 + tpw + 1.2, W - wall)]
bosses = []
for x in (12, 62, W - 62, W - 12):
    for y in (12, 60, 108):
        bosses.append((x, y))
bosses += [(25, ys_seam), (W/2 - 70, ys_seam), (W/2 + 95, ys_seam), (W - 25, ys_seam),
           (W/2 - 60, y_rear), (W/2 + 60, y_rear), (W - 25, y_rear)]
tp_port_x = 116; kb_port_x = 40
tp_px = tp_x0 + tp_clr + tp_port_x; kb_px = kb_x0 + kb_clr + kb_port_x
sock_y = [(tp_end + kb_y0 - seam_rib)/2, (kb_end + 1.2 + D - wall)/2]   # USB-C sockets on LEFT side
sock_z = (cover_t + H - skin)/2
kb_rails = [kb_x0 + v for v in (12, 80, 149, 218, 286)]
tp_rails = [tp_x0 + v for v in (14, 80.3, 146.6)]
kb_bot = lambda y: (H - skin) - (kb_front_h + t_kb*(y - (kb_y0 + kb_clr)))     # Joro bottom height (top level)
tp_bot = lambda y: (H - tp_drop) - (tp_front_h + t_tp*(y - (tp_y0 + tp_clr)))  # trackpad bottom height
print(f"W={W:.1f} D={D:.1f} H={H:.1f}; kb bottom front {kb_bot(kb_y0+kb_clr):.2f} back {kb_bot(kb_end-kb_clr):.2f}; "
      f"tp bottom front {tp_bot(tp_y0+tp_clr):.2f} back {tp_bot(tp_end-tp_clr):.2f}")

S2 = math.sqrt(2)
def rr2(X, Y, x0, y0, w, d, r):
    qx = np.abs(X - (x0 + w/2)) - (w/2 - r); qy = np.abs(Y - (y0 + d/2)) - (d/2 - r)
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
def circ(X, Y, cx, cy, r): return np.hypot(X - cx, Y - cy) - r
def lattice(X, Y, P):
    m = None
    for k in range(3):
        a = math.radians(60*k); s = X*math.cos(a) + Y*math.sin(a)
        d = np.abs(s - P*np.round(s/P)); m = d if m is None else np.minimum(m, d)
    return m
def rim(d2, Z, top): return np.maximum((d2 - (Z - top + pc))/S2, (top - pc) - Z)

def top_case(X, Y, Z):
    outer = rr2(X, Y, 0, 0, W, D, corner_r)
    shell = np.maximum.reduce([outer, Z - H, -Z, (outer + Z - H + e_top)/S2, (outer - Z + e_bot)/S2])
    inner = rr2(X, Y, wall, wall, W - 2*wall, D - 2*wall, corner_r - wall)
    zc = np.maximum(cover_t - Z, Z - (H - skin + 0.2))          # vertical extent of internal structure
    cav = np.maximum(inner, Z - (H - skin))
    tp_in = rr2(X, Y, tp_x0, tp_y0, tpw, tpd, tp_r + tp_clr)
    st = []
    # isogrid core under palm rests
    zone = np.minimum.reduce([rr2(X, Y, a, wall, b - a, tp_end - wall, 0.01) for a, b in palm_x])
    st.append(np.maximum.reduce([lattice(X, Y, P_top) - rib/2, zone, zc]))
    # trackpad pocket wall (open at the back for the plug)
    st.append(np.maximum.reduce([tp_in - 1.2, -tp_in, Y - (tp_end - 12), zc]))
    # seam rib in front of keyboard, keyboard back wall with plug slot
    st.append(np.maximum.reduce([np.abs(Y - ys_seam) - seam_rib/2, zc]))
    st.append(np.maximum.reduce([np.abs(Y - (kb_end + 0.6)) - 0.6, -(np.abs(X - kb_px) - 8), zc]))
    # screw bosses
    st.append(np.maximum(np.minimum.reduce([circ(X, Y, bx, by, boss_r) for bx, by in bosses]), zc))
    inner_struct = np.maximum(np.minimum.reduce(st), inner + 0.01)
    solid = np.minimum(np.maximum(shell, -cav), inner_struct)
    solid = np.maximum(solid, shell)
    cuts = [
        np.maximum(rr2(X, Y, kb_x0, kb_y0, kbw, kbd, 4.4), Z - (H - skin)),        # keyboard bay
        tp_in, rim(tp_in, Z, H),                                                   # trackpad opening
    ]
    kf = rr2(X, Y, kb_x0 + kb_clr + kf_inset[0] - key_clr, kb_y0 + kb_clr + kf_inset[2] - key_clr,
             kb_w - kf_inset[0] - kf_inset[1] + 2*key_clr, kb_d - kf_inset[2] - kf_inset[3] + 2*key_clr, 2)
    cuts += [kf, rim(kf, Z, H)]
    cuts.append(np.maximum(np.minimum.reduce([circ(X, Y, bx, by, insert_r) for bx, by in bosses]), Z - (cover_t + insert_d)))
    for sy in sock_y:   # USB-C socket openings in left wall (9.6 x 3.9 stadium)
        q = np.hypot(np.maximum(np.abs(Y - sy) - (9.6 - 3.9)/2, 0), Z - sock_z) - 3.9/2
        cuts.append(np.maximum(q, X - (wall + 1)))
    return np.maximum(solid, -np.minimum.reduce(cuts))

def cover(X, Y, Z):
    c2 = rr2(X, Y, wall + 0.2, wall + 0.2, W - 2*wall - 0.4, D - 2*wall - 0.4, corner_r - wall - 0.2)
    plate = np.maximum.reduce([c2, -Z, Z - cover_t])
    keep = [c2 + 6]                                                         # solid band at edge
    keep += [-(circ(X, Y, bx, by, 6)) for bx, by in bosses]
    for x in kb_rails: keep.append(-np.maximum(np.abs(X - x) - 3, np.abs(Y - (kb_y0 + kbd/2)) - kbd/2))
    for x in tp_rails: keep.append(-np.maximum(np.abs(X - x) - 3, np.abs(Y - (tp_y0 + tpd/2)) - tpd/2))
    for fx in (20, W - 20):
        for fy in (20, D - 20): keep.append(-circ(X, Y, fx, fy, 7))
    hole = np.maximum.reduce([web/2 - lattice(X, Y, P_cov)] + keep)
    plate = np.maximum(plate, -hole)
    rails = []
    for x in kb_rails:
        rails.append(np.maximum.reduce([np.abs(X - x) - 1.0, np.abs(Y - (kb_y0 + kbd/2)) - (kbd/2 - 3),
                                        Z - (kb_bot(Y) - pad), cover_t - 0.2 - Z]))
    for x in tp_rails:
        rails.append(np.maximum.reduce([np.abs(X - x) - 1.0, np.abs(Y - (tp_y0 + tpd/2)) - (tpd/2 - 4),
                                        Z - (tp_bot(Y) - pad), cover_t - 0.2 - Z]))
    solid = np.minimum(plate, np.minimum.reduce(rails))
    cuts = []
    for bx, by in bosses:
        d = np.hypot(X - bx, Y - by)
        cuts.append(np.minimum(d - 1.7, (d - (3.1 - Z))/S2))                 # M3 countersunk
    for fx in (20, W - 20):
        for fy in (20, D - 20): cuts.append(np.maximum(circ(X, Y, fx, fy, 5.25), Z - 0.6))  # rubber feet
    return np.maximum(solid, -np.minimum.reduce(cuts))

if __name__ == "__main__":
    f, ztop = (top_case, H) if PART == "top" else (cover, max(kb_bot(kb_y0), tp_bot(tp_y0)))
    t0 = time.time()
    xs = np.arange(-1.0, W + 1.0, RES, dtype=np.float32)
    ys = np.arange(-1.0, D + 1.0, RES, dtype=np.float32)
    zz = np.arange(-1.0, ztop + 1.0, RES, dtype=np.float32)
    vol = np.empty((len(xs), len(ys), len(zz)), np.float32)
    Yg, Zg = np.meshgrid(ys, zz, indexing="ij")
    for i, x in enumerate(xs):
        vol[i] = f(np.full_like(Yg, x), Yg, Zg)
    print("grid", vol.shape, f"{time.time()-t0:.0f}s", flush=True)
    v, fc, _, _ = marching_cubes(vol, 0.0, spacing=(RES, RES, RES))
    v += np.array([xs[0], ys[0], zz[0]])
    print("mc", len(v), len(fc), f"{time.time()-t0:.0f}s")
    np.save(PART + "_verts.npy", v); np.save(PART + "_faces.npy", fc)
