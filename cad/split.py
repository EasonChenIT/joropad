"""Cut the top case and the cover into bed-sized tiles.

Every seam is a vertical extrusion of a 2D curve, so tiles go together by sliding straight down and every
joint face prints without overhang.
  top case : SEAM_STYLE "straight" -> x = W/2 (front and back) + y on the seam rib, hidden by the openings
             SEAM_STYLE "dovetail" -> front seam in the left palm rest, dovetails + boss lugs, staggered
  cover    : always dovetailed; x-seam at X_COVER (full depth), y-seams at Y_COVER_L / Y_COVER_R (T-junctions)
"""
from functools import lru_cache
from build123d import Kind, Polygon, Pos, Rot, Sketch, fillet, offset
import params as P
import deck as Dk

BIG = 400.0


def _curve(axis, base, a, b, feats, sign):
    """Seam polyline. axis 'x': line x=base running along y from a to b; 'y': line y=base along x.
    feats: list of (t, kind) with kind 'dove' | 'lug'; features stick out toward +sign."""
    tn = [(a, 0.0)]
    for t, kind in sorted(feats):
        if kind == "dove":
            n, h, d = P.TAB["neck"], P.TAB["head"], P.TAB["depth"]
            tn += [(t - n / 2, 0), (t - h / 2, d), (t + h / 2, d), (t + n / 2, 0)]
        else:
            w, d = P.LUG["width"], P.LUG["depth"]
            tn += [(t - w / 2, 0), (t - w / 2, d), (t + w / 2, d), (t + w / 2, 0)]
    tn.append((b, 0.0))
    if axis == "x":
        return [(base + sign * n, t) for t, n in tn]
    return [(t, base + sign * n) for t, n in tn]


def male_region(axis, base, feats, sign):
    """Region on the -sign side of the seam, including the features that stick out across it."""
    pts = _curve(axis, base, -BIG, BIG, feats, sign)
    if axis == "x":
        pts += [(base - sign * BIG, BIG), (base - sign * BIG, -BIG)]
    else:
        pts += [(BIG, base - sign * BIG), (-BIG, base - sign * BIG)]
    poly = Polygon(*pts, align=None)
    corners = [v for v in poly.vertices() if abs(v.X) < BIG / 2 and abs(v.Y) < BIG / 2]
    if feats:
        try:
            poly = fillet(corners, 0.8)
        except Exception:
            pass
    return Sketch() + poly.faces()


def everything():
    return Pos(P.W / 2, P.D / 2) * Polygon((-BIG, -BIG), (BIG, -BIG), (BIG, BIG), (-BIG, BIG), align=None)


# ------------------------------------------------------------------ seam definitions
def top_regions():
    # y-seam: the rear tiles reach forward into the channel with lugs (each carries a screw boss) and dovetails
    dove = P.SEAM_STYLE == "dovetail"
    y_feats = [(x, "lug") for x in P.SEAM_LUG_X] + [(x, "dove") for x in (85.0, 215.0, 288.0)] if dove else []
    rear = male_region("y", P.ys, y_feats, -1)
    front = everything() - rear
    xf = male_region("x", P.X_FRONT, [(36.0, "dove"), (84.0, "dove")] if dove else [], +1)
    y_rz = (P.bw1 + P.D - P.WALL) / 2 + 2.0
    xr = male_region("x", P.X_REAR, [(y_rz, "dove")] if dove else [], +1)
    return {
        "top_FL": front & xf,
        "top_FR": front - xf,
        "top_RL": rear & xr,
        "top_RR": rear - xr,
    }


def cover_regions():
    xc = male_region("x", P.X_COVER, [(y, "dove") for y in (14.0, 60.0, 128.0, 170.0, 212.0, 250.0)], +1)
    yl = male_region("y", P.Y_COVER_L, [(x, "dove") for x in (28.0, 120.0, 178.0)], -1)
    yr = male_region("y", P.Y_COVER_R, [(x, "dove") for x in (258.0, 284.0)], -1)
    right = everything() - xc
    return {
        "cover_FL": xc - yl,
        "cover_RL": xc & yl,
        "cover_FR": right - yr,
        "cover_RR": right & yr,
    }


def _shrink(sk):
    try:
        return Sketch() + offset(sk, -P.GAP / 2, kind=Kind.INTERSECTION).faces()
    except Exception:
        out = []
        for f in sk.faces():
            out += offset(f, -P.GAP / 2, kind=Kind.INTERSECTION).faces()
        return Sketch() + out


def _cut(part, regions, z0, z1):
    tiles = {}
    for name, sk in regions.items():
        tool = Dk.prism(_shrink(sk), z0, z1)
        t = part & tool
        tiles[name] = t
    return tiles


@lru_cache(None)
def top_tiles():
    return _cut(Dk.top_case(), top_regions(), -5, P.H + 5)


@lru_cache(None)
def cover_tiles():
    return _cut(Dk.cover(), cover_regions(), -5, P.H + 5)


def print_pose(name, shape):
    """Top tiles print upside down (the visible top face on the bed); cover tiles print as modelled."""
    if name.startswith("top"):
        shape = Rot(180, 0, 0) * shape
    bb = shape.bounding_box()
    return Pos(-bb.min.X, -bb.min.Y, -bb.min.Z) * shape
