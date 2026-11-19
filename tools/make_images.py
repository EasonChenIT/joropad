"""Render the documentation images into docs/img (needs node, playwright, and `npm install three` in RENDER_DIR)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cad"))
sys.path.insert(0, HERE)
from build123d import Pos
import params as P
import deck as Dk
import split as S
from render import render

IMG = os.path.join(HERE, "..", "docs", "img")
PFX = "svc_" if P.SVC else ""          # service-profile images get their own names
os.makedirs(IMG, exist_ok=True)
CASE, COVER, KB, CAPS, TP, SOCK = "#c9ccd1", "#8fa9c2", "#2f3033", "#4a4b50", "#efefef", "#d08030"
TILE_COLS = ["#d98c8c", "#8cc28c", "#8c9fd9", "#d9c78c"]
cx, cy = P.W / 2, P.D / 2


def main(which=None):
    top, cov = Dk.top_case(), Dk.cover()
    kb, caps, tp = Dk.keyboard(), Dk.keycaps(), Dk.trackpad()
    socks = Dk.socket_bodies()
    jobs = {}

    jobs["hero"] = lambda: render(
        [(top, CASE), (kb, KB), (caps, CAPS), (tp, TP)], os.path.join(IMG, PFX + "hero.png"),
        dict(pos=(cx - 230, cy - 400, 300), target=(cx, cy - 10, 0), fov=30))

    def exploded():
        lift = lambda s, dz: Pos(0, 0, dz) * s
        render([(lift(top, 70), CASE), (lift(kb, 35), KB), (lift(caps, 35), CAPS), (lift(tp, 35), TP)]
               + [(lift(b, 35), SOCK) for b in socks] + [(cov, COVER)],
               os.path.join(IMG, PFX + "exploded.png"), dict(pos=(cx + 330, cy - 420, -120), target=(cx, cy, 40), fov=30))
    jobs["exploded"] = exploded

    jobs["underside"] = lambda: render(
        [(top, CASE)] + [(b, SOCK) for b in socks], os.path.join(IMG, PFX + "underside.png"),
        dict(pos=(cx - 60, cy - 330, -420), target=(cx, cy, 0), fov=30))

    def section():
        xc = P.W / 2 + 0.6                                     # through the centre rails
        half = Dk.box(-10, xc, -10, P.D + 10, -10, 60)
        parts = [(top & half, CASE), (cov & half, COVER), (kb & half, KB), (caps & half, CAPS), (tp & half, TP)]
        render(parts, os.path.join(IMG, PFX + "section.png"),
               dict(pos=(xc + 500, P.D / 2, 10), target=(xc, P.D / 2, 10), ortho=34, up=(0, 0, 1)), size=(2400, 300))
    jobs["section"] = section

    def tiles():
        tt = list(S.top_tiles().values())
        render([(t, TILE_COLS[i]) for i, t in enumerate(tt)], os.path.join(IMG, "tiles_top.png"),
               dict(pos=(cx, cy, 600), target=(cx, cy, 0), ortho=290, up=(0, 1, 0)))
        ct = list(S.cover_tiles().values())
        render([(t, TILE_COLS[i]) for i, t in enumerate(ct)], os.path.join(IMG, "tiles_cover.png"),
               dict(pos=(cx, cy, 600), target=(cx, cy, 0), ortho=290, up=(0, 1, 0)))
    if P.SPLIT:
        jobs["tiles"] = tiles

    def cover_views():
        render([(cov, COVER)], os.path.join(IMG, PFX + "cover_bottom.png"),
               dict(pos=(cx, cy, -600), target=(cx, cy, 0), ortho=290, up=(0, 1, 0)))
        render([(cov, COVER)], os.path.join(IMG, PFX + "cover_inside.png"),
               dict(pos=(cx - 160, cy - 420, 300), target=(cx, cy, 0), fov=30))
    jobs["cover"] = cover_views

    def lid_open():
        from build123d import Axis
        hinge = Axis((0, P.D, P.COVER_T), (1, 0, 0))
        ang = -62
        lid = top.rotate(hinge, ang)
        parts = [(cov, COVER), (kb, KB), (caps, CAPS), (lid, CASE), (tp.rotate(hinge, ang), TP)]
        render(parts, os.path.join(IMG, PFX + "lid_open.png"), dict(pos=(cx - 330, -330, 260), target=(cx, cy, 30), fov=32))
        render([(cov, COVER)], os.path.join(IMG, PFX + "tray.png"), dict(pos=(cx - 160, -300, 280), target=(cx, cy, 0), fov=32))
    def details():
        # lid seen from below, Joro and trackpad in place: the spring fingers around both
        crop = Dk.box(-1, 125, 60, 175, -1, 25)
        render([(top & crop, CASE)] + [(h & crop, "#d08030") for h in Dk.springs_only()],
               os.path.join(IMG, PFX + "springs.png"), dict(pos=(130, 40, -110), target=(55, 120, 12), fov=30))
        # snap clip: section through the left clip
        sx = P.SNAP_X[0]
        cut_ = Dk.box(sx - 0.1, sx + 30, -2, 30, -1, 25)
        render([(top & cut_, CASE), (cov & cut_, COVER)], os.path.join(IMG, PFX + "snap.png"),
               dict(pos=(sx - 120, 12, 10), target=(sx, 8, 8), ortho=26, up=(0, 0, 1)), size=(1200, 900))
    def lip():
        xs = P.tp_gx0 + 40.0                                    # section through the front edge of the trackpad
        half = Dk.box(xs - 40, xs, -2, 30, -1, 25)
        render([(top & half, CASE), (cov & half, COVER), (tp & half, TP)], os.path.join(IMG, PFX + "lip.png"),
               dict(pos=(xs + 300, 12, 14), target=(xs, 12, 14), ortho=16, up=(0, 0, 1)), size=(1400, 900))
    if P.LID:
        jobs["lid"] = lid_open
        jobs["details"] = details
        if P.TP_LIP > 0:
            jobs["lip"] = lip

    def fits():
        kl, kr = Dk.fit_keyboard()
        ftp, fs = Dk.fit_trackpad(), Dk.fit_socket()
        parts = [(Pos(0, 40, 0) * kl, TILE_COLS[0]), (Pos(20, 40, 0) * kr, TILE_COLS[1]),
                 (Pos(0, -10, 0) * ftp, TILE_COLS[2]), (Pos(-30, -10, 0) * fs, TILE_COLS[3])]
        render(parts, os.path.join(IMG, PFX + "fit_tests.png"), dict(pos=(cx - 120, -330, 330), target=(cx, 130, 0), fov=30))
    if P.sockets:
        jobs["fits"] = fits

    for k, f in jobs.items():
        if which and k not in which:
            continue
        print("render", k, flush=True)
        f()


if __name__ == "__main__":
    main(sys.argv[1:] or None)
