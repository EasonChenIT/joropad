"""Draw the measurement diagrams (SVG -> PNG) for docs/measure_sheet.md."""
import os, math, subprocess, json

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "..", "docs", "img")
FONT = "WenQuanYi Zen Hei, Noto Sans CJK SC, sans-serif"
INK, DIM, KEY, NOTE = "#222", "#c0392b", "#7f8c8d", "#2c3e50"


class Svg:
    def __init__(self, w, h, title):
        self.w, self.h, self.items = w, h, []
        self.text(20, 34, title, 24, weight="bold")

    def add(self, s):
        self.items.append(s)

    def text(self, x, y, s, size=16, color=NOTE, anchor="start", weight="normal"):
        self.add(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" '
                 f'font-weight="{weight}" font-family="{FONT}">{s}</text>')

    def rect(self, x, y, w, h, rx=0, fill="none", stroke=INK, sw=2, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def line(self, x1, y1, x2, y2, color=INK, sw=2, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}"{d}/>')

    def poly(self, pts, fill="none", stroke=INK, sw=2):
        p = " ".join(f"{x},{y}" for x, y in pts)
        self.add(f'<polygon points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def path(self, d, fill="none", stroke=INK, sw=2, dash=None):
        dd = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dd}/>')

    def dim(self, x1, y1, x2, y2, label, off=0, side=1, size=17):
        """Dimension arrow between two points with a label (red)."""
        self.line(x1, y1, x2, y2, DIM, 2)
        ang = math.atan2(y2 - y1, x2 - x1)
        for (x, y, a) in ((x1, y1, ang), (x2, y2, ang + math.pi)):
            p1 = (x + 10 * math.cos(a + 0.4), y + 10 * math.sin(a + 0.4))
            p2 = (x + 10 * math.cos(a - 0.4), y + 10 * math.sin(a - 0.4))
            self.poly([(x, y), p1, p2], fill=DIM, stroke=DIM, sw=1)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        nx, ny = -math.sin(ang) * side, math.cos(ang) * side
        lx, ly = mx + nx * (14 + off), my + ny * (14 + off) + 6
        self.add(f'<text x="{lx}" y="{ly}" font-size="{size}" fill="{DIM}" text-anchor="middle" font-weight="bold" '
                 f'font-family="{FONT}" paint-order="stroke" stroke="#fff" stroke-width="4">{label}</text>')

    def svg(self):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
                f'<rect width="100%" height="100%" fill="#fff"/>' + "".join(self.items) + "</svg>")


def joro():
    s = Svg(1400, 1180, "图 1  Razer Joro 键盘（单位 mm，示意图不按比例）")
    # ---- (a) top view
    x0, y0, W, D = 90, 160, 900, 340
    s.text(x0, 76, "(a) 俯视：键盘正常放在桌上，空格键靠近你", 18, weight="bold")
    s.rect(x0, y0, W, D, rx=14, fill="#f4f4f4")
    ki = 30
    s.rect(x0 + ki, y0 + ki, W - 2 * ki, D - 2 * ki, rx=5, fill="#e6e6e6", stroke=KEY)
    for r in range(6):
        yy = y0 + ki + 8 + r * 46
        for c in range(15):
            s.rect(x0 + ki + 8 + c * 55.5, yy, 47, 38, rx=4, fill="#fff", stroke="#b5b5b5", sw=1)
    s.text(x0 + ki + 14, y0 + ki + 32, "Esc", 14, KEY)
    s.text(x0 + W / 2, y0 + D + 34, "前（空格键这一侧，靠近你）", 16, anchor="middle")
    s.text(x0 + W / 2 + 120, y0 - 12, "后", 16, anchor="middle")
    s.text(x0 - 12, y0 + D / 2, "Esc 侧", 16, anchor="end")
    s.dim(x0, y0 - 40, x0 + W, y0 - 40, "K1 总宽", side=-1)
    s.line(x0, y0 - 50, x0, y0 + 5, DIM, 1, "4 3"); s.line(x0 + W, y0 - 50, x0 + W, y0 + 5, DIM, 1, "4 3")
    s.dim(x0 + W + 50, y0, x0 + W + 50, y0 + D, "K2 深度", side=-1, off=34)
    s.line(x0 + W - 5, y0, x0 + W + 60, y0, DIM, 1, "4 3"); s.line(x0 + W - 5, y0 + D, x0 + W + 60, y0 + D, DIM, 1, "4 3")
    s.dim(x0, y0 + D / 2 + 40, x0 + ki, y0 + D / 2 + 40, "K6", off=4)
    s.dim(x0 + W - ki, y0 + D / 2 + 40, x0 + W, y0 + D / 2 + 40, "K7", off=4)
    s.dim(x0 + 160, y0 + D - ki, x0 + 160, y0 + D, "K8", side=-1, off=8)
    s.dim(x0 + 160, y0, x0 + 160, y0 + ki, "K9", side=-1, off=8)
    # ---- K5 corner detail
    cx, cy = 1080, 160
    s.text(cx, cy - 40, "K5 外框圆角（描图法）", 18, weight="bold")
    s.rect(cx, cy - 20, 280, 230, fill="#fafafa", stroke="#ccc", sw=1)
    ox, oy, R = cx + 50, cy + 30, 120
    s.line(ox - 30, oy, ox + 220, oy, INK, 1, "6 4"); s.line(ox, oy - 30, ox, oy + 190, INK, 1, "6 4")
    s.path(f"M {ox + R} {oy} L {ox + 220} {oy} M {ox} {oy + R} L {ox} {oy + 170} M {ox} {oy + R} A {R} {R} 0 0 1 {ox + R} {oy}", sw=3)
    ax = ox + R - R / math.sqrt(2)
    s.dim(ox, oy, ax, ax - ox + oy, "d", side=1, off=2)
    s.text(cx, cy + 235, "把键盘放在纸上描出外框，", 15)
    s.text(cx, cy + 257, "用尺把两条直边延长交于一点，", 15)
    s.text(cx, cy + 279, "量交点到圆弧的距离 d（沿 45° 方向）。", 15)
    s.text(cx, cy + 301, "四个角都量，写最大值。", 15)
    # ---- (b) side view
    bx, by = 90, 600
    s.text(bx, by - 30, "(b) 侧视：放在桌上量，不含键帽", 18, weight="bold")
    s.line(bx - 20, by + 160, bx + 640, by + 160, "#999", 2)
    s.text(bx + 600, by + 182, "桌面", 14, "#999")
    s.poly([(bx, by + 160), (bx + 600, by + 160), (bx + 600, by + 20), (bx, by + 95)], fill="#f4f4f4")
    for i in range(9):
        px = bx + 40 + i * 62
        top = by + 95 - (px - bx) * (75 / 600)
        s.rect(px, top - 16, 46, 16, rx=3, fill="#fff", stroke="#b5b5b5", sw=1)
    s.dim(bx - 30, by + 160, bx - 30, by + 95, "K4 前高", side=1, off=30)
    s.dim(bx + 630, by + 160, bx + 630, by + 20, "K3 后高", side=-1, off=30)
    s.text(bx, by + 200, "前（靠近你）", 15); s.text(bx + 600, by + 200, "后", 15, anchor="end")
    s.text(bx, by + 228, "从桌面量到铝框上表面（键帽旁边的框），不要量到键帽顶。", 14)
    # keycap zoom
    zx, zy = 800, 590
    s.text(zx, zy - 20, "K10 / K11 键帽高度（放大）", 18, weight="bold")
    s.rect(zx, zy + 120, 520, 24, fill="#ddd")
    s.text(zx + 8, zy + 160, "铝面板（键帽之间的金属面）", 14)
    s.rect(zx + 60, zy + 60, 110, 60, rx=6, fill="#fff")
    s.dim(zx + 40, zy + 120, zx + 40, zy + 60, "K10", side=1, off=12)
    s.text(zx + 115, zy + 50, "正常", 14, anchor="middle")
    s.rect(zx + 300, zy + 92, 110, 28, rx=6, fill="#fff")
    s.dim(zx + 280, zy + 120, zx + 280, zy + 92, "K11", side=1, off=12)
    s.text(zx + 355, zy + 82, "用手指按到底", 14, anchor="middle")
    s.text(zx, zy + 190, "卡尺尾部的深度尺抵住铝面板，伸到键帽顶面。", 14)
    s.text(zx, zy + 210, "选 F 键和空格键各量一次，取较大值。", 14)
    # ---- (c) back view
    cx0, cy0 = 90, 900
    s.text(cx0, cy0 - 30, "(c) 后视：USB-C 口和开关（K13–K16）", 18, weight="bold")
    s.rect(cx0, cy0, 900, 90, rx=6, fill="#f4f4f4")
    s.line(cx0 - 20, cy0 + 90, cx0 + 920, cy0 + 90, "#999", 2)
    s.text(cx0 - 20, cy0 + 112, "桌面", 14, "#999")
    px, pw = cx0 + 700, 50
    s.rect(px, cy0 + 40, pw, 18, rx=9, fill="#555")
    s.rect(px - 120, cy0 + 38, 50, 20, rx=3, fill="#999")
    s.text(px - 95, cy0 + 30, "开关", 14, anchor="middle")
    s.text(px + 25, cy0 + 30, "USB-C", 14, anchor="middle")
    s.text(cx0 + 900, cy0 - 6, "← 从后面看时，Esc 侧在右边", 14, anchor="end")
    s.dim(cx0 + 900, cy0 + 130, px + pw / 2, cy0 + 130, "K14a 到 Esc 侧", side=1, off=6)
    s.dim(cx0, cy0 + 130, px + pw / 2, cy0 + 130, "K14b 到另一侧", side=1, off=6)
    s.dim(px + pw + 40, cy0 + 90, px + pw + 40, cy0 + 49, "K15", side=-1, off=10)
    s.text(cx0, cy0 + 180, "量到 USB-C 口的中心。开关也按同样方法量（K16）：位置、大小、往哪个方向拨。", 14)
    return s


def trackpad():
    s = Svg(1400, 900, "图 2  Magic Trackpad（USB-C 版，单位 mm）")
    x0, y0, W, D = 90, 130, 520, 380
    s.text(x0, y0 - 45, "(a) 俯视：最薄的一边朝向你", 18, weight="bold")
    s.rect(x0, y0, W, D, rx=30, fill="#f4f4f4")
    s.dim(x0, y0 - 20, x0 + W, y0 - 20, "T1 宽", side=-1)
    s.dim(x0 + W + 40, y0, x0 + W + 40, y0 + D, "T2 深", side=-1, off=24)
    s.text(x0 + W / 2, y0 + D + 34, "前（最薄的一边，靠近你）", 16, anchor="middle")
    s.text(x0 + W / 2, y0 + D / 2, "量底面的外形（玻璃面可能略小）", 15, KEY, anchor="middle")
    s.text(x0 - 10, y0 + D / 2 + 50, "左", 16, anchor="end")
    s.text(x0 + 30, y0 + D + 70, "T5 圆角：同图 1 的 K5 描图法，量 d。", 15)
    # side
    bx, by = 760, 130
    s.text(bx, by - 45, "(b) 侧视", 18, weight="bold")
    s.line(bx - 20, by + 150, bx + 540, by + 150, "#999", 2)
    s.poly([(bx, by + 150), (bx + 500, by + 150), (bx + 500, by + 40), (bx, by + 100)], fill="#f4f4f4")
    s.dim(bx - 20, by + 150, bx - 20, by + 100, "T3 前厚", side=1, off=30)
    s.dim(bx + 530, by + 150, bx + 530, by + 40, "T4 后厚", side=-1, off=30)
    s.text(bx, by + 185, "前", 15); s.text(bx + 500, by + 185, "后", 15, anchor="end")
    # back view
    cx0, cy0 = 760, 430
    s.text(cx0, cy0 - 30, "(c) 后视（T6–T8）", 18, weight="bold")
    s.rect(cx0, cy0, 520, 80, rx=8, fill="#f4f4f4")
    s.line(cx0 - 20, cy0 + 80, cx0 + 540, cy0 + 80, "#999", 2)
    px = cx0 + 160
    s.rect(px, cy0 + 34, 40, 16, rx=8, fill="#555")
    s.rect(cx0 + 30, cy0 + 34, 34, 14, rx=3, fill="#999")
    s.text(px + 20, cy0 + 26, "USB-C", 14, anchor="middle")
    s.text(cx0 + 47, cy0 + 26, "开关", 14, anchor="middle")
    s.text(cx0 + 520, cy0 - 6, "从后面看时，正面的左边在右边 →", 14, anchor="end")
    s.dim(cx0 + 520, cy0 + 115, px + 20, cy0 + 115, "T6a 到正面看的左边", side=1, off=6)
    s.dim(cx0, cy0 + 115, px + 20, cy0 + 115, "T6b 到另一边", side=1, off=6)
    s.dim(px + 70, cy0 + 80, px + 70, cy0 + 42, "T7", side=-1, off=8)
    s.text(cx0, cy0 + 165, "开关（T8）也量两边的距离。", 14)
    # bottom
    s.text(90, 700, "(d) 底面：脚垫 / 凸起（键盘 K17 同样要量）", 18, weight="bold")
    s.rect(90, 720, 340, 150, rx=20, fill="#f4f4f4")
    for fx, fy in ((120, 745), (390, 745), (120, 840), (390, 840)):
        s.rect(fx - 12, fy - 8, 24, 16, rx=8, fill="#888")
    s.text(460, 760, "把设备翻过来，对每一个脚垫 / 凸起记下：", 15)
    s.text(460, 786, "· 中心到【正面看的左边】的距离、到前边的距离", 15)
    s.text(460, 812, "· 大小（直径，或长 × 宽）", 15)
    s.text(460, 838, "· 凸出底面的高度（如果是平的就写 0）", 15)
    s.text(460, 864, "拍一张带尺子的底面照片最保险。", 15)
    return s


def usb():
    s = Svg(1400, 620, "图 3  USB-C 母座模块（U）和 90° 弯头插头（P）")
    x0, y0 = 90, 140
    s.text(x0, y0 - 45, "(a) 母座模块：买来后量，两个一样就量一个", 18, weight="bold")
    s.rect(x0 + 80, y0 + 40, 300, 160, rx=6, fill="#e8d7c0")
    s.text(x0 + 230, y0 + 125, "本体 / 电路板", 15, anchor="middle")
    s.rect(x0, y0 + 85, 82, 70, rx=30, fill="#bbb")
    s.text(x0 + 40, y0 + 75, "金属口", 14, anchor="middle")
    s.dim(x0 + 80, y0 + 240, x0 + 380, y0 + 240, "U3 本体深（不含线）", side=1)
    s.dim(x0 + 420, y0 + 40, x0 + 420, y0 + 200, "U1 本体宽", side=-1, off=30)
    s.dim(x0, y0 + 20, x0 + 80, y0 + 20, "U4 金属口伸出", side=-1, off=4)
    s.text(x0, y0 + 310, "U2 本体厚（垂直于纸面）；U5 × U6 金属口外形的宽 × 厚（标准约 8.94 × 3.26）；", 15)
    s.text(x0, y0 + 336, "U7 线从哪一面出来（后面 / 底面 / 侧面）。", 15)
    s.text(x0, y0 + 362, "U4：从本体最前面（或电路板前边）量到金属口最前端。", 15)
    # plug
    px, py = 800, 140
    s.text(px, py - 45, "(b) 90° 弯头插头：插在设备上量", 18, weight="bold")
    s.rect(px, py + 20, 40, 260, fill="#f4f4f4")
    s.text(px + 20, py + 300, "设备", 14, anchor="middle")
    s.rect(px + 40, py + 110, 90, 60, rx=10, fill="#555")
    s.rect(px + 100, py + 170, 30, 90, rx=6, fill="#777")
    s.text(px + 140, py + 240, "线", 14)
    s.dim(px + 40, py + 90, px + 130, py + 90, "P1 伸出长度", side=-1, off=4)
    s.dim(px + 160, py + 110, px + 160, py + 170, "P2 宽", side=-1, off=10)
    s.text(px, py + 340, "P1：插好后，从设备外壳表面量到插头最远端。", 15)
    s.text(px, py + 366, "P3：插头头部的厚度（垂直于纸面）。", 15)
    return s


def render(svgs):
    os.makedirs(IMG, exist_ok=True)
    js = """
const { chromium } = require('playwright');
(async () => {
  const jobs = JSON.parse(process.argv[process.argv.length - 1]);
  const b = await chromium.launch();
  for (const j of jobs) {
    const p = await b.newPage({ viewport: { width: j.w, height: j.h }, deviceScaleFactor: 2 });
    await p.setContent(`<html><body style="margin:0">${require('fs').readFileSync(j.svg, 'utf8')}</body></html>`);
    await p.screenshot({ path: j.png, clip: { x: 0, y: 0, width: j.w, height: j.h } });
    await p.close();
  }
  await b.close();
})();
"""
    jobs = []
    for name, sv in svgs.items():
        svg_path = os.path.join(IMG, f"{name}.svg")
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(sv.svg())
        jobs.append({"svg": os.path.abspath(svg_path), "png": os.path.abspath(os.path.join(IMG, f"{name}.png")), "w": sv.w, "h": sv.h})
    subprocess.run(["node", "-e", js, json.dumps(jobs)], check=True)


if __name__ == "__main__":
    render({"measure_joro": joro(), "measure_trackpad": trackpad(), "measure_usb": usb()})
