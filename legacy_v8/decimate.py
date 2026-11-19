"""Planar-region decimation: collapse vertices whose incident faces are all coplanar."""
import numpy as np, sys, time, struct

PRE = sys.argv[1]
V = np.load(PRE + "_verts.npy").astype(np.float64)
F = np.load(PRE + "_faces.npy").astype(np.int64)
OUT = sys.argv[2]
TOL = 0.99995

# orient outward (marching_cubes on sdf<0 inside): check signed volume
def signed_vol(V, F):
    a, b, c = V[F[:,0]], V[F[:,1]], V[F[:,2]]
    return np.einsum('ij,ij->i', a, np.cross(b, c)).sum() / 6
if signed_vol(V, F) < 0:
    F = F[:, [0, 2, 1]]
print("volume cm3", signed_vol(V, F)/1000)

def fnormal(a, b, c):
    n = np.cross(V[b] - V[a], V[c] - V[a]); l = np.linalg.norm(n)
    return n / l if l > 0 else n, l

# merge coincident vertices, drop faces that collapse to a line through repeated indices
key = np.round(V / 1e-5).astype(np.int64)
_, inv = np.unique(key, axis=0, return_inverse=True)
inv = inv.ravel(); rep = np.zeros(inv.max() + 1, np.int64); rep[inv] = np.arange(len(V))
F = rep[inv[F]]
F = F[(F[:,0] != F[:,1]) & (F[:,1] != F[:,2]) & (F[:,0] != F[:,2])]
cr = np.cross(V[F[:,1]] - V[F[:,0]], V[F[:,2]] - V[F[:,0]])
area = np.linalg.norm(cr, axis=1)
N = np.where(area[:, None] > 1e-12, cr / np.maximum(area, 1e-30)[:, None], 0.0)   # zero-area faces: never 'flat'
e = np.sort(np.concatenate([F[:,[0,1]], F[:,[1,2]], F[:,[2,0]]]), axis=1)
_, c = np.unique(e, axis=0, return_counts=True); print("after merge: edge counts", np.bincount(c))
faces = F.tolist(); alive = [True]*len(faces); fn = N.tolist()
vf = [set() for _ in range(len(V))]
for i, (a, b, c) in enumerate(faces):
    vf[a].add(i); vf[b].add(i); vf[c].add(i)
valive = [True]*len(V)
vv = [set() for _ in range(len(V))]
for a, b, c in faces:
    vv[a].update((b, c)); vv[b].update((a, c)); vv[c].update((a, b))
MAXDEG = 40

def try_collapse(v, touched):
    fs = vf[v]
    if len(fs) < 3: return False
    it = iter(fs); n0 = fn[next(it)]
    for f in it:
        n = fn[f]
        if n0[0]*n[0] + n0[1]*n[1] + n0[2]*n[2] < TOL: return False
    nv = vv[v]
    for u in sorted(nv, key=lambda x: len(vv[x])):
        if u in touched: continue
        if len(vv[u] | nv) - 2 > MAXDEG: continue
        shared = [f for f in fs if u in faces[f]]
        if len(shared) != 2: continue
        opp = set()
        for f in shared: opp.update(faces[f])
        opp -= {u, v}
        if (vv[u] & nv) != opp: continue
        ok = True; newn = []
        for f in fs:
            if f in shared: continue
            tri = [u if x == v else x for x in faces[f]]
            n, l = fnormal(*tri)
            if l < 1e-9 or n @ n0 < TOL: ok = False; break
            newn.append((f, n.tolist()))
        if not ok: continue
        for f, n in newn: fn[f] = n
        for f in shared:
            alive[f] = False
            for x in faces[f]: vf[x].discard(f)
        for f in list(vf[v]):
            faces[f] = [u if x == v else x for x in faces[f]]
            vf[u].add(f)
        for w in nv:
            vv[w].discard(v)
            if w != u: vv[w].add(u); vv[u].add(w)
        vv[u].discard(u); vv[v] = set()
        vf[v] = set(); valive[v] = False
        touched.add(u); touched.update(nv)
        return True
    return False

t0 = time.time()
rng = np.random.default_rng(1)
for p in range(40):
    cnt = 0; touched = set()
    for v in rng.permutation(len(V)).tolist():
        if valive[v] and v not in touched and try_collapse(v, touched): cnt += 1
    nf = sum(alive)
    print(f"pass {p}: collapsed {cnt}, faces {nf}, {time.time()-t0:.0f}s", flush=True)
    if cnt < 100: break

Fo = np.array([faces[i] for i in range(len(faces)) if alive[i]])
print("final faces", len(Fo), "volume cm3", signed_vol(V, Fo)/1000)
e = np.sort(np.concatenate([Fo[:,[0,1]], Fo[:,[1,2]], Fo[:,[2,0]]]), axis=1)
_, c = np.unique(e, axis=0, return_counts=True); print("final edge counts", np.bincount(c))
# binary STL
tri = V[Fo]
n = np.cross(tri[:,1] - tri[:,0], tri[:,2] - tri[:,0]); n /= np.linalg.norm(n, axis=1)[:, None] + 1e-30
with open(OUT, "wb") as f:
    f.write(b"Joro + Magic Trackpad deck v8, units mm".ljust(80, b" "))
    f.write(struct.pack("<I", len(Fo)))
    rec = np.zeros(len(Fo), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"] = n; rec["v"] = tri
    f.write(rec.tobytes())

print("wrote", OUT)
