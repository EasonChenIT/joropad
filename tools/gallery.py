"""Product gallery: renders from every side, details, the opening sequence and dimensioned part drawings.

writes docs/gallery/*.png and site/models.json (for the interactive 3D page in site/)
usage: python tools/gallery.py [names...]
"""
import base64, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cad"))
sys.path.insert(0, HERE)
from build123d import Axis, Pos, export_stl
import params as P
import deck as Dk
from render import render

OUT = os.path.join(HERE, "..", "docs", "gallery")
SITE = os.path.join(HERE, "..", "site")
os.makedirs(OUT, exist_ok=True)

BLACK, BLACK2 = "#3b3d42", "#45474d"                  # MJF PA12 dyed black (lightened so details read)
GREY, GREY2 = "#c9ccd1", "#9fb4c7"                    # light study colours
KB, CAPS, TP, SPR = "#26272a", "#3a3b40", "#ececec", "#d08030"
cx, cy = P.W / 2, P.D / 2


def png(name):
    return os.path.join(OUT, name + ".png")


def parts():
    top, tray = Dk.top_case(), Dk.cover()
    kb, caps, tp = Dk.keyboard(), Dk.keycaps(), Dk.trackpad()
    return top, tray, kb, caps, tp


def hinge():
    return Axis((0, P.D, P.COVER_T), (1, 0, 0))


def jobs():
    top, tray, kb, caps, tp = parts()
    dev = [(kb, KB), (caps, CAPS), (tp, TP)]
    J = {}

    # ---------------- whole deck
    J["01_front_left"] = lambda: render([(top, BLACK), (tray, BLACK2)] + dev, png("01_front_left"),
                                        dict(pos=(cx - 260, -300, 260), target=(cx, cy - 20, 0), fov=30))
    J["02_front_low"] = lambda: render([(top, BLACK), (tray, BLACK2)] + dev, png("02_front_low"),
                                       dict(pos=(cx + 60, -420, 70), target=(cx, cy, 5), fov=30))
    J["03_rear_right"] = lambda: render([(top, BLACK), (tray, BLACK2)] + dev, png("03_rear_right"),
                                        dict(pos=(P.W + 260, P.D + 300, 230), target=(cx, cy, 0), fov=30))
    J["04_left_side"] = lambda: render([(top, GREY, 1, True), (tray, GREY2, 1, True)] + dev, png("04_left_side"),
                                       dict(pos=(-500, cy, 10), target=(0, cy, 10), ortho=34, up=(0, 0, 1)), size=(2400, 320))
    J["05_top_plan"] = lambda: render([(top, BLACK), (tray, BLACK2)] + dev, png("05_top_plan"),
                                      dict(pos=(cx, cy, 600), target=(cx, cy, 0), ortho=270, up=(0, 1, 0)))
    J["06_bottom"] = lambda: render([(tray, GREY2, 1, True), (top, GREY, 1, True)], png("06_bottom"),
                                    dict(pos=(cx - 260, -320, -200), target=(cx, cy, 5), fov=30))

    def exploded(name, pos, tgt):
        lift = lambda s, dz: Pos(0, 0, dz) * s
        render([(lift(top, 80), GREY, 1, True), (lift(kb, 40), KB), (lift(caps, 40), CAPS), (lift(tp, 40), TP),
                (tray, GREY2, 1, True)], png(name), dict(pos=pos, target=tgt, fov=30))
    J["07_exploded_above"] = lambda: exploded("07_exploded_above", (cx - 300, -330, 330), (cx, cy, 40))
    J["08_exploded_below"] = lambda: exploded("08_exploded_below", (cx + 330, -380, -170), (cx, cy, 40))

    # ---------------- the two printed parts on their own
    J["09_lid_top"] = lambda: render([(top, GREY, 1, True)], png("09_lid_top"),
                                     dict(pos=(cx - 240, -280, 280), target=(cx, cy, 0), fov=30))
    J["10_lid_underside"] = lambda: render([(top, GREY, 1, True)] + [(h, SPR) for h in Dk.springs_only()],
                                           png("10_lid_underside"),
                                           dict(pos=(cx + 200, -230, -330), target=(cx, cy, 8), fov=30))
    J["11_lid_underside_plan"] = lambda: render([(top, GREY, 1, True)] + [(h, SPR) for h in Dk.springs_only()],
                                                png("11_lid_underside_plan"),
                                                dict(pos=(cx, cy, -600), target=(cx, cy, 0), ortho=270, up=(0, 1, 0)))
    J["12_tray_top"] = lambda: render([(tray, GREY2, 1, True)], png("12_tray_top"),
                                      dict(pos=(cx - 220, -280, 260), target=(cx, cy, 0), fov=30))
    J["13_tray_bottom"] = lambda: render([(tray, GREY2, 1, True)], png("13_tray_bottom"),
                                         dict(pos=(cx, cy, -600), target=(cx, cy, 0), ortho=270, up=(0, 1, 0)))

    # ---------------- opening sequence (both devices stay in the lid, held by the springs)
    def opened(name, ang):
        h = hinge()
        render([(tray, GREY2, 1, True), (top.rotate(h, -ang), GREY, 1, True), (kb.rotate(h, -ang), KB),
                (caps.rotate(h, -ang), CAPS), (tp.rotate(h, -ang), TP)], png(name),
               dict(pos=(cx - 380, -330, 230), target=(cx, cy, 40), fov=32))
    J["14_open_25"] = lambda: opened("14_open_25", 25)
    J["15_open_70"] = lambda: opened("15_open_70", 70)

    # ---------------- details
    def snap_section():
        sx = P.SNAP_X[0]
        c = Dk.box(sx - 0.1, sx + 40, -2, 30, -1, 25)
        render([(top & c, GREY, 1, True), (tray & c, GREY2, 1, True)], png("16_snap_section"),
               dict(pos=(sx - 200, 10, 9), target=(sx, 10, 9), ortho=24, up=(0, 0, 1)), size=(1200, 900))
    J["16_snap_section"] = snap_section

    def hook_section():
        hx = P.HOOK_X[1]
        c = Dk.box(hx - 0.1, hx + 40, P.D - 22, P.D + 2, -1, 25)
        render([(top & c, GREY, 1, True), (tray & c, GREY2, 1, True), (kb & c, KB)], png("17_hook_section"),
               dict(pos=(hx - 200, P.D - 9, 9), target=(hx, P.D - 9, 9), ortho=24, up=(0, 0, 1)), size=(1200, 900))
    J["17_hook_section"] = hook_section

    def kb_springs():
        c = Dk.box(-1, 60, P.kb_y0 - 5, P.D + 1, -1, 25)
        render([(top & c, GREY, 1, True)] + [(h & c, SPR) for h in Dk.springs_only()], png("18_kb_springs"),
               dict(pos=(110, P.kb_y0 - 60, -90), target=(10, P.kb_y0 + 70, 12), fov=32))
    J["18_kb_springs"] = kb_springs

    def tp_springs():
        c = Dk.box(P.tp_gx0 - 15, P.tp_gx0 + 70, -1, P.cf + 6, -1, 25)
        render([(top & c, GREY, 1, True)] + [(h & c, SPR) for h in Dk.springs_only()] + [(tp & c, TP, 0.45)],
               png("19_tp_springs"), dict(pos=(P.tp_gx0 + 120, -40, -80), target=(P.tp_gx0 + 20, 55, 14), fov=32))
    J["19_tp_springs"] = tp_springs

    def pin_section():
        px, py = P.PIN_POS[0]
        c = Dk.box(px - 12, px + 12, py - 0.05, py + 20, -1, 25)
        render([(top & c, GREY, 1, True), (tray & c, GREY2, 1, True)], png("20_pin_section"),
               dict(pos=(px, py - 200, 6), target=(px, py, 6), ortho=16, up=(0, 0, 1)), size=(1200, 900))
    J["20_pin_section"] = pin_section

    J["21_finger_notch"] = lambda: render([(top, BLACK, 1, True), (tray, BLACK2, 1, True)], png("21_finger_notch"),
                                          dict(pos=(cx + 25, -70, -10), target=(cx, 2, 3), fov=30))

    def key_corner():
        render([(top, GREY, 1, True), (kb, KB), (caps, "#55575d")], png("22_key_corner"),
               dict(pos=(P.kf_x0 + 95, P.kf_y0 - 110, 120), target=(P.kf_x0 + 25, P.kf_y0 + 15, P.H), fov=30))
    J["22_key_corner"] = key_corner

    def tp_corner():
        render([(top, BLACK, 1, True), (tp, TP)], png("23_trackpad_corner"),
               dict(pos=(P.tp_gx0 + 45, P.tp_gy0 - 35, 55), target=(P.tp_gx0 + 6, P.tp_gy0 + 8, P.H), fov=30))
    J["23_trackpad_corner"] = tp_corner

    def long_section():
        xc = P.W / 2 + 0.6
        c = Dk.box(-10, xc, -10, P.D + 10, -10, 60)
        render([(top & c, GREY, 1, True), (tray & c, GREY2, 1, True), (kb & c, KB), (caps & c, CAPS), (tp & c, TP)],
               png("24_long_section"), dict(pos=(xc + 500, P.D / 2, 10), target=(xc, P.D / 2, 10), ortho=30,
                                           up=(0, 0, 1)), size=(2400, 300))
    J["24_long_section"] = long_section

    def cross_section():
        yc = P.kb_fy + 50.0
        c = Dk.box(-10, P.W + 10, yc, P.D + 10, -10, 60)
        render([(top & c, GREY, 1, True), (tray & c, GREY2, 1, True), (kb & c, KB), (caps & c, CAPS)]
               + [(h & c, SPR) for h in Dk.springs_only()],
               png("25_cross_section"), dict(pos=(P.W / 2, yc - 500, 10), target=(P.W / 2, yc, 10), ortho=34,
                                            up=(0, 0, 1)), size=(2400, 330))
    J["25_cross_section"] = cross_section

    # ---------------- ortho views for the dimensioned drawings
    S = 4.0                                                # px per mm
    def ortho(name, shapes, pos, tgt, up, w_mm, h_mm):
        render(shapes, png(name), dict(pos=pos, target=tgt, ortho=h_mm, up=up), size=(int(w_mm * S), int(h_mm * S)))
    J["v_lid_top"] = lambda: ortho("v_lid_top", [(top, GREY, 1, True)], (cx, cy, 600), (cx, cy, 0), (0, 1, 0), P.W + 20, P.D + 20)
    J["v_lid_front"] = lambda: ortho("v_lid_front", [(top, GREY, 1, True), (tray, GREY2, 1, True)], (cx, -600, P.H / 2),
                                     (cx, 0, P.H / 2), (0, 0, 1), P.W + 20, 40)
    J["v_lid_side"] = lambda: ortho("v_lid_side", [(top, GREY, 1, True), (tray, GREY2, 1, True)], (P.W + 600, cy, P.H / 2),
                                    (P.W, cy, P.H / 2), (0, 0, 1), P.D + 20, 40)
    J["v_tray_top"] = lambda: ortho("v_tray_top", [(tray, GREY2, 1, True)], (cx, cy, 600), (cx, cy, 0), (0, 1, 0), P.W + 20, P.D + 20)
    return J


# ---------------------------------------------------------------- dimensioned drawings
def sheet(name, title, views, dims, w, h):
    """views: [(png, x, y, w, h, label)]; dims: callables(svg) drawing on top. Renders to docs/gallery/name.png."""
    sys.path.insert(0, HERE)
    from measure_diagrams import Svg
    s = Svg(w, h, title)
    for f, x, y, vw, vh, label in views:
        data = base64.b64encode(open(f, "rb").read()).decode()
        s.add(f'<image href="data:image/png;base64,{data}" x="{x}" y="{y}" width="{vw}" height="{vh}"/>')
        s.text(x, y - 10, label, 17, weight="bold")
    for d in dims:
        d(s)
    s.text(20, h - 16, "单位 mm。尺寸来自当前参数（设备尺寸尚为估计值，实测后会更新）。", 14)
    svg_path = os.path.join(OUT, name + ".svg")
    open(svg_path, "w", encoding="utf-8").write(s.svg())
    js = """
const { chromium } = require('playwright');
(async () => {
  const [svg, out, w, h] = process.argv.slice(-4);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: 2 });
  await p.setContent(`<html><body style="margin:0">${require('fs').readFileSync(svg, 'utf8')}</body></html>`);
  await p.screenshot({ path: out, clip: { x: 0, y: 0, width: +w, height: +h } });
  await b.close();
})();
"""
    subprocess.run(["node", "-e", js, svg_path, png(name), str(w), str(h)], check=True)
    os.remove(svg_path)


def drawings():
    S = 4.0
    f = lambda v: f"{v:.1f}"
    # lid sheet: top view (plan), front view, right side view
    tw, th = (P.W + 20) * S, (P.D + 20) * S
    ox, oy = 60, 90                                        # top view origin on the sheet (top-left of image)
    X = lambda x: ox + tw / 2 + (x - P.W / 2) * S         # model x -> sheet px (top view)
    Y = lambda y: oy + th / 2 - (y - P.D / 2) * S         # model y -> sheet px (top view)
    fy0 = oy + th + 90                                     # front view
    FZ = lambda z: fy0 + 40 * S / 2 - (z - P.H / 2) * S
    kf = (P.kf_x0, P.kf_y0, P.kf_x1, P.kf_y1)
    to = (P.tp_gx0 - P.TP_CLR, P.tp_gy0 - P.TP_CLR, P.tp_gx1 + P.TP_CLR, P.tp_gy1 + P.TP_CLR)

    def lid_dims(s):
        s.dim(X(0), Y(P.D) - 30, X(P.W), Y(P.D) - 30, f"总宽 {f(P.W)}", side=-1)
        s.dim(X(P.W) + 40, Y(P.D), X(P.W) + 40, Y(0), f"总深 {f(P.D)}", side=-1, off=60)
        s.dim(X(to[0]), Y(to[1]) + 34, X(to[2]), Y(to[1]) + 34, f"触控板开口 {f(to[2] - to[0])}", side=1)
        s.dim(X(to[2]) + 30, Y(to[3]), X(to[2]) + 30, Y(to[1]), f"{f(to[3] - to[1])}", side=-1, off=24)
        s.dim(X(to[0]) - 30, Y(0), X(to[0]) - 30, Y(to[1]), f"{f(to[1])}", side=1, off=18)
        s.dim(X(kf[0]), Y(kf[3]) + 40, X(kf[2]), Y(kf[3]) + 40, f"键区开口 {f(kf[2] - kf[0])}", side=1)
        s.dim(X(kf[0]) + 30, Y(kf[3]), X(kf[0]) + 30, Y(kf[1]), f"{f(kf[3] - kf[1])}", side=1, off=24)
        s.dim(X(kf[2]) - 30, Y(kf[1]), X(kf[2]) - 30, Y(to[3]), f"{f(kf[1] - to[3])}", side=1, off=20)
        s.dim(X(P.W) + 60, FZ(0), X(P.W) + 60, FZ(P.H), "", side=-1)
        s.text(X(P.W) + 80, FZ(P.H / 2) + 6, f"总高 {f(P.H)}", 17, "#c0392b", weight="bold")
        s.text(X(P.W) + 80, FZ(0) + 30, f"其中底盘 {f(P.COVER_T)}", 15, "#c0392b")
        s.text(X(0), FZ(0) + 120, f"触控板玻璃比面板低 {P.TP_DROP}，开口四周缝 {P.TP_CLR}；键帽四周缝 {P.KEY_CLR}。"
                                  f"前缘正中是开盖用的手指凹口。", 15)
    views = [(png("v_lid_top"), ox, oy, tw, th, "俯视图（上壳，顶面朝上）"),
             (png("v_lid_front"), ox, fy0, tw, 40 * S, "主视图（从前面看，含底盘）")]
    sheet("D1_lid_drawing", "部件图 1　上壳（MJF PA12，1 件）", views, [lid_dims], int(ox + tw + 300), int(fy0 + 40 * S + 170))

    # tray sheet
    def tray_dims(s):
        s.dim(X(0), Y(P.D) - 30, X(P.W), Y(P.D) - 30, f"总宽 {f(P.W)}", side=-1)
        s.dim(X(P.W) + 40, Y(P.D), X(P.W) + 40, Y(0), f"总深 {f(P.D)}", side=-1, off=60)
        for sx in P.SNAP_X:
            s.text(X(sx), Y(0) + 40, "卡扣", 15, anchor="middle")
        s.dim(X(0), Y(0) + 70, X(P.SNAP_X[0]), Y(0) + 70, f"{f(P.SNAP_X[0])}", side=1)
        for hx in P.HOOK_X:
            s.text(X(hx), Y(P.D) + 50, "挂钩", 15, anchor="middle")
        s.text(X(P.kb_rails[1]) + 10, Y((P.kb_fy + P.kb_end) / 2), "键盘支撑条（5 条）", 15)
        for px, py in P.PIN_POS:
            s.text(X(px) + 14, Y(py) + 5, "定位销", 14)
        s.text(X(0), Y(0) + 120, f"底板厚 {P.COVER_T}；触控板的支撑条在上壳里；卡扣臂 {P.SNAP_T} × {P.SNAP_W} × {P.SNAP_L}"
                                  f"（厚 × 宽 × 高）。", 15)
    views = [(png("v_tray_top"), ox, oy, tw, th, "俯视图（底盘，内侧朝上）")]
    sheet("D2_tray_drawing", "部件图 2　底盘（MJF PA12，1 件）", views, [tray_dims], int(ox + tw + 300), int(oy + th + 160))


def models():
    """site/models.json for the interactive page: each mesh as base64 float32 xyz triples (3 per triangle)."""
    import struct, tempfile
    top, tray, kb, caps, tp = parts()
    out = {}
    with tempfile.TemporaryDirectory() as tmp:
        for name, shp in (("lid", top), ("tray", tray), ("keyboard", kb.fuse(caps)), ("trackpad", tp)):
            f = os.path.join(tmp, name + ".stl")
            export_stl(shp, f, tolerance=0.05, angular_tolerance=0.3)
            d = open(f, "rb").read()
            n = struct.unpack("<I", d[80:84])[0]
            pos = b"".join(d[84 + i * 50 + 12:84 + i * 50 + 48] for i in range(n))
            out[name] = base64.b64encode(pos).decode()
    out["meta"] = dict(W=P.W, D=P.D, H=P.H, cover_t=P.COVER_T, tp_drop=P.TP_DROP, measured=P.MEASURED)
    os.makedirs(SITE, exist_ok=True)
    open(os.path.join(SITE, "models.json"), "w").write(json.dumps(out))


if __name__ == "__main__":
    want = sys.argv[1:]
    J = jobs()
    for k, fn in J.items():
        if want and not any(k.startswith(w) for w in want):
            continue
        print("render", k, flush=True)
        fn()
    if not want or "drawings" in want:
        drawings()
    if not want or "models" in want:
        models()
    import glob, shutil                                   # the page's image folder is a copy of docs/gallery
    os.makedirs(os.path.join(SITE, "img"), exist_ok=True)
    for f in glob.glob(os.path.join(OUT, "[0-9D]*.png")):
        shutil.copy(f, os.path.join(SITE, "img"))
