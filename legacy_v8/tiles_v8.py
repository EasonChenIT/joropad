"""Cut v8 parts into bed-sized tiles via SDF, mesh each, orient for printing.
usage: python3 tiles_v8.py top|cover idx   (idx 0..3)  -> tile_<part>_<idx>_verts/faces.npy
"""
import numpy as np, sys, time
import build_v8 as B
from skimage.measure import marching_cubes

part, idx = sys.argv[1], int(sys.argv[2]); RES = 0.4
W, D, H = B.W, B.D, B.H
if part == "top":
    xs_, ys_ = W/2, B.ys_seam
else:
    xs_, ys_ = W/2 + 45, 70.0
LAP = 6.0; G = 0.1                     # half-lap width / fit gap (cover only)
ix, iy = idx % 2, idx // 2
big = 1e4

def region(X, Y, Z):
    if part == "top":
        rx = (X - xs_) if ix == 0 else (xs_ - X)
        ry = (Y - ys_) if iy == 0 else (ys_ - Y)
        return np.maximum(rx, ry)
    low = Z < B.cover_t/2
    sx = np.where(low, xs_ + LAP, xs_)
    sy = np.where(low, ys_ + LAP, ys_)
    rx = (X - (sx - G)) if ix == 0 else ((sx + G) - X)
    ry = (Y - (sy - G)) if iy == 0 else ((sy + G) - Y)
    return np.maximum(rx, ry)

f = B.top_case if part == "top" else B.cover
ztop = H if part == "top" else max(B.kb_bot(B.kb_y0), B.tp_bot(B.tp_y0))
x0, x1 = (-1, xs_ + LAP + 1) if ix == 0 else (xs_ - 1, W + 1)
y0, y1 = (-1, ys_ + LAP + 1) if iy == 0 else (ys_ - 1, D + 1)
t0 = time.time()
xs = np.arange(x0, x1, RES, dtype=np.float32); ys = np.arange(y0, y1, RES, dtype=np.float32)
zz = np.arange(-1.0, ztop + 1.0, RES, dtype=np.float32)
vol = np.empty((len(xs), len(ys), len(zz)), np.float32)
Yg, Zg = np.meshgrid(ys, zz, indexing="ij")
for i, x in enumerate(xs):
    Xg = np.full_like(Yg, x)
    vol[i] = np.maximum(f(Xg, Yg, Zg), region(Xg, Yg, Zg))
vol[0] = vol[-1] = 1; vol[:, 0] = vol[:, -1] = 1          # close the box
v, fc, _, _ = marching_cubes(vol, 0.0, spacing=(RES, RES, RES))
v += np.array([xs[0], ys[0], zz[0]])
if part == "top":                                          # print upside-down: smooth top face on the bed
    v[:, 1] = -v[:, 1]; v[:, 2] = H - v[:, 2]
v -= v.min(axis=0)
pre = f"tile_{part}_{idx}"
np.save(pre + "_verts.npy", v); np.save(pre + "_faces.npy", fc)
print(pre, "size", np.round(v.max(axis=0), 1), len(fc), f"{time.time()-t0:.0f}s")
