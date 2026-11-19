"""Design checks. Prints a report and exits non-zero if a hard check fails.

usage: python check.py
"""
import sys
from build123d import Align, Cylinder, Pos
import params as P
import deck as Dk
import split as S

FAIL = []
CN = "tray" if P.LID else "cover"


def line(ok, msg):
    print(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        FAIL.append(msg)


def note(msg):
    print("  info " + msg)


def overlap(a, b):
    r = a & b
    return sum(s.volume for s in r.solids()) if r is not None else 0.0


def main():
    print("== layout")
    print(P.summary())
    top, cov = Dk.top_case(), Dk.cover()
    kb, caps, tp = Dk.keyboard(), Dk.keycaps(), Dk.trackpad()
    socks = Dk.socket_bodies()

    print("== measurements")
    line(P.MEASURED, "measurements.json confirmed (real caliper readings, not estimates)"
         + ("" if P.MEASURED else "  -> order files are blocked until this passes"))
    if P.PORTS:
        line(P.KB_PORT_FACE == "back", f"Joro USB-C port face: {P.KB_PORT_FACE} (the layout routes it from the back face)")

    print("== solids")
    line(top.is_valid and len(top.solids()) == 1, f"top case: valid single solid, {top.volume / 1000:.1f} cm3")
    line(cov.is_valid and len(cov.solids()) == 1, f"{CN}: valid single solid, {cov.volume / 1000:.1f} cm3")

    print("== device fit (interference volume, mm3)")
    v = overlap(kb, top); line(v < 1.0, f"Joro body vs top case: {v:.2f}")
    v = overlap(kb, cov); line(v < 1.0, f"Joro body vs {CN}: {v:.2f}")
    v = overlap(caps, top); line(v < 1.0, f"key caps vs top case: {v:.2f}")
    v = overlap(tp, cov); line(v < 1.0, f"trackpad vs {CN}: {v:.2f}")
    v = overlap(tp, top)
    ribs = Dk.crush_ribs()
    v_rib = sum(overlap(tp, r) for r in ribs)
    line(abs(v - v_rib) < 1.0, f"trackpad vs top case: {v:.2f} (all of it is the {len(ribs)} crush ribs: {v_rib:.2f})")
    for s, b in zip(P.sockets, socks):
        vt, vc = overlap(b, top), overlap(b, cov)
        line(vt < 1.0 and vc < 1.0, f"{s['name']} socket body vs top / cover: {vt:.2f} / {vc:.2f}")

    print("== clearances (mm)")
    d = kb.distance_to(cov); line(abs(d - P.KB_PAD) < 0.05, f"Joro bottom -> rails: {d:.3f} (foam {P.KB_PAD})")
    d = min(tp.distance_to(r) for r in Dk.tp_rail_solids())
    line(abs(d - P.TP_PAD) < 0.05, f"trackpad bottom -> rails: {d:.3f} (pad {P.TP_PAD})")
    tbb = tp.bounding_box()
    line(abs((P.H - tbb.max.Z) - P.TP_DROP) < 0.01, f"glass below the deck top: {P.H - tbb.max.Z:.3f}")
    kbb = kb.bounding_box()
    line(abs(kbb.max.Z - P.z_kb_top) < 0.01, f"Joro top plate against the panel underside (z {kbb.max.Z:.3f})")
    d = caps.distance_to(top); line(d > P.KEY_CLR - 0.05, f"key caps -> opening edge: {d:.3f}")
    proud = P.KEYCAP_H - P.KB_SKIN
    line(proud - P.KEY_TRAVEL >= 0.3, f"key cap still {proud - P.KEY_TRAVEL:.2f} proud of the deck when pressed "
         f"(cap {P.KEYCAP_H}, panel {P.KB_SKIN}, travel {P.KEY_TRAVEL}); needs >= 0.3")
    line(P.H <= 20.0, f"deck height {P.H:.2f}")

    if P.LID:
        print("== lid on tray (no screws)")
        v = overlap(top, cov); line(v < 0.5, f"lid vs tray interference: {v:.2f} mm3")
        line(len(P.MAG_POS) >= 6, f"{len(P.MAG_POS)} magnet pairs (d{P.MAG_D:g} x {P.MAG_H:g}), {len(P.PIN_POS)} alignment pins, "
                                  f"{len(P.HOOK_X)} back hooks")
        from build123d import Axis
        hinge = Axis((0, P.D, P.COVER_T), (1, 0, 0))            # the lid pivots on its back bottom edge
        hit = [(a, overlap(top.rotate(hinge, -a), cov) + overlap(top.rotate(hinge, -a), kb))
               for a in (1, 3, 6, 10, 15, 20, 30, 45, 60, 80)]
        worst = max(hit, key=lambda t: t[1])
        line(worst[1] < 0.5, "lid swings open about the back edge without hitting the tray or the Joro: "
                             + ", ".join(f"{a}deg {v:.1f}" for a, v in hit) + " mm3")
        floor = P.COVER_T + P.MAG_PAD_H - P.MAG_H - 0.2
        line(floor >= 0.8, f"tray under each magnet pocket: {floor:.2f} mm (MJF min 0.8)")
        note("charging ports removed: the Joro and the trackpad come out of the deck to charge")

    if P.sockets:
        print("== sockets on the left face")
    for s in P.sockets:
        y_lo, y_hi = s["y"] - P.slot_w / 2, s["y"] + P.slot_w / 2
        flat = P.CORNER_R <= y_lo and y_hi <= P.D - P.CORNER_R
        line(flat, f"{s['name']}: slot y {y_lo:.1f}..{y_hi:.1f} lies on the flat part of the left face")

    if P.SPLIT:
        tiles_report(top, cov)
    else:
        print("== one-piece parts vs bureau build volume " + " x ".join(f"{v:.0f}" for v in P.BUILD_VOLUME))
        lim = sorted(P.BUILD_VOLUME)
        for name, part in (("top case", top), (CN, cov)):
            bb = part.bounding_box()
            dims = sorted((bb.size.X, bb.size.Y, bb.size.Z))
            line(all(d <= l - 5 for d, l in zip(dims, lim)),
                 f"{name}: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} fits (5 mm margin, any orientation)")
        print("== bureau tolerance budget (worst case +/-0.4% of length, JLC3DP MJF spec)")
        tol = 0.004
        kf_len = max(P.kf_x1 - P.kf_x0, P.kf_y1 - P.kf_y0)
        left = P.KEY_CLR - tol * kf_len / 2
        line(left >= 0.15, f"key caps -> opening edge: {P.KEY_CLR:.2f} nominal, {left:.2f} worst case (needs >= 0.15)")
        left = P.TP_CLR - tol * (P.TP_W + 2 * P.TP_CLR) / 2
        line(left >= 0.1, f"trackpad -> opening edge: {P.TP_CLR:.2f} nominal, {left:.2f} worst case (needs >= 0.10)")
        left = P.KB_CLR - tol * (P.KB_W + 2 * P.KB_CLR) / 2
        line(left >= 0.2, f"Joro -> bay wall: {P.KB_CLR:.2f} nominal, {left:.2f} worst case (needs >= 0.20; EVA strips fill it)")
        left = P.tp_ring_in - tol * (P.TP_W + 2 * P.tp_ring_in) / 2
        line(left >= 0.3, f"trackpad -> pocket wall: {P.tp_ring_in:.2f} nominal, {left:.2f} worst case (EVA pads fill it)")
        if not P.LID:
            note("cover <-> wall gap is not budgeted: both parts come out of the same build and scale together")
        else:
            note("tray position does not affect any visible gap: both devices are centred by the lid itself")

    print("== mass")
    g = (top.volume + cov.volume) / 1000 * P.DENSITY
    note(f"solid {'MJF PA12' if P.SVC else 'PETG'} {g:.0f} g (top {top.volume / 1000 * P.DENSITY:.0f} g + cover {cov.volume / 1000 * P.DENSITY:.0f} g); "
         f"with devices (374 + 230 g) about {(g + 604) / 1000:.2f} kg")

    print()
    print("FAILED: " + "; ".join(FAIL) if FAIL else "all checks passed")
    return 1 if FAIL else 0


def tiles_report(top, cov):
    print("== tiles")
    tiles = {**S.top_tiles(), **S.cover_tiles()}
    lim = P.BED - 2 * P.BED_MARGIN
    tot_top = tot_cov = 0
    for name, t in tiles.items():
        bb = S.print_pose(name, t).bounding_box()
        ok = t.is_valid and len(t.solids()) == 1 and bb.size.X <= lim and bb.size.Y <= lim
        line(ok, f"{name:9s} {bb.size.X:6.1f} x {bb.size.Y:6.1f} x {bb.size.Z:4.1f}  {t.volume / 1000:5.1f} cm3  "
                 f"solids={len(t.solids())}")
        if name.startswith("top"):
            tot_top += t.volume
        else:
            tot_cov += t.volume
    note(f"tiles hold {tot_top / top.volume * 100:.2f}% / {tot_cov / cov.volume * 100:.2f}% of the top case / cover volume "
         f"(the rest is the {P.GAP} joint gap)")

    print("== screw bosses vs seams (every boss and every cover screw must sit in exactly one tile)")
    for bx, by in P.bosses:
        cyl = Pos(bx, by, P.COVER_T) * Cylinder(P.BOSS_R, 5, align=(Align.CENTER, Align.CENTER, Align.MIN))
        owners_t = [n for n, t in S.top_tiles().items() if overlap(cyl, t) > 1.0]
        pad = Pos(bx, by, 0) * Cylinder(4.0, P.COVER_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
        owners_c = [n for n, t in S.cover_tiles().items() if overlap(pad, t) > 1.0]
        ok = len(owners_t) == 1 and len(owners_c) == 1
        if not ok:
            line(False, f"boss ({bx:.1f}, {by:.1f}) in {owners_t} / {owners_c}")
    per_tile = {}
    for bx, by in P.bosses:
        pad = Pos(bx, by, 0) * Cylinder(4.0, P.COVER_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
        for n, t in S.cover_tiles().items():
            if overlap(pad, t) > 1.0:
                per_tile[n] = per_tile.get(n, 0) + 1
        cyl = Pos(bx, by, P.COVER_T) * Cylinder(P.BOSS_R, 5, align=(Align.CENTER, Align.CENTER, Align.MIN))
        for n, t in S.top_tiles().items():
            if overlap(cyl, t) > 1.0:
                per_tile[n] = per_tile.get(n, 0) + 1
    for n in tiles:
        line(per_tile.get(n, 0) >= 3, f"{n}: {per_tile.get(n, 0)} screws")


if __name__ == "__main__":
    sys.exit(main())
