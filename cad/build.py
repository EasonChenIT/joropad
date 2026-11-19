"""Build everything and write the deliverables to ../out.

usage: python build.py            # STEP + STL + 3MF + fit tests
       python build.py --no-step  # skip the (slow, large) STEP files
"""
import os, sys, time, zipfile
import numpy as np
from build123d import Color, Compound, export_step, export_stl
import params as P
import deck as Dk
import split as S

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out")
NAMES = {  # tile -> display name (Chinese, as used in the docs)
    "top_FL": "上壳-左前", "top_FR": "上壳-右前", "top_RL": "上壳-左后", "top_RR": "上壳-右后",
    "cover_FL": "底盖-左前", "cover_FR": "底盖-右前", "cover_RL": "底盖-左后", "cover_RR": "底盖-右后",
    "fit_kb_L": "试配-键区左", "fit_kb_R": "试配-键区右", "fit_tp": "试配-触控板", "fit_sock": "试配-USB座",
}


def weld(verts, tris):
    """tessellate() gives every B-rep face its own vertices; merge them so the mesh is one closed manifold."""
    v = np.array([(p.X, p.Y, p.Z) for p in verts])
    key = np.round(v / 1e-4).astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    t = inv.ravel()[np.array(tris, dtype=np.int64)]
    t = t[(t[:, 0] != t[:, 1]) & (t[:, 1] != t[:, 2]) & (t[:, 0] != t[:, 2])]
    return v[first], t


def write_3mf(path, items, title):
    """Minimal 3MF core file: one object per item, laid out side by side (use Arrange in the slicer)."""
    objs, build, x = [], [], 0.0
    for i, (key, shape) in enumerate(items, 1):
        verts, tris = weld(*shape.tessellate(0.02, 0.15))
        bb = shape.bounding_box()
        vs = "".join(f'<vertex x="{x - bb.min.X:.4f}" y="{y - bb.min.Y:.4f}" z="{z - bb.min.Z:.4f}"/>' for x, y, z in verts)
        ts = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tris)
        objs.append(f'<object id="{i}" name="{NAMES.get(key, key)} ({key})" type="model"><mesh><vertices>{vs}</vertices>'
                    f'<triangles>{ts}</triangles></mesh></object>')
        build.append(f'<item objectid="{i}" transform="1 0 0 0 1 0 0 0 1 {x:.2f} 0 0"/>')
        x += bb.size.X + 10
    model = ('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="zh-CN" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<metadata name="Title">{title}</metadata><resources>' + "".join(objs) +
             '</resources><build>' + "".join(build) + '</build></model>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr("3D/3dmodel.model", model)


def labelled(shape, label, color):
    shape.label = label
    shape.color = Color(color)
    return shape


def main():
    step = "--no-step" not in sys.argv
    t0 = time.time()
    for d in ("step/tiles", "print/stl"):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)
    top, cov = Dk.top_case(), Dk.cover()
    tiles = {**S.top_tiles(), **S.cover_tiles()}
    kl, kr = Dk.fit_keyboard()
    fits = {"fit_kb_L": kl, "fit_kb_R": kr, "fit_tp": Dk.fit_trackpad(), "fit_sock": Dk.fit_socket()}
    print(f"geometry {time.time() - t0:.0f}s")

    if step:
        export_step(labelled(top.moved(top.location), "top_case", "#C9CCD1"), os.path.join(OUT, "step", "top_case_v9.step"))
        export_step(labelled(cov.moved(cov.location), "bottom_cover", "#8FA9C2"), os.path.join(OUT, "step", "bottom_cover_v9.step"))
        asm = Compound(label="joro_trackpad_deck_v9", children=[
            labelled(top.moved(top.location), "top_case", "#C9CCD1"),
            labelled(cov.moved(cov.location), "bottom_cover", "#8FA9C2"),
            labelled(Dk.keyboard().moved(Dk.keyboard().location), "joro_envelope", "#303030"),
            labelled(Dk.keycaps().moved(Dk.keycaps().location), "joro_keycaps_envelope", "#505050"),
            labelled(Dk.trackpad().moved(Dk.trackpad().location), "trackpad_envelope", "#EDEDED"),
        ] + [labelled(b, f"usbc_module_{s['name']}_envelope", "#D08030") for s, b in zip(P.sockets, Dk.socket_bodies())])
        export_step(asm, os.path.join(OUT, "step", "deck_v9_assembly.step"))
        for n, t in tiles.items():
            export_step(labelled(t, n, "#C9CCD1" if n.startswith("top") else "#8FA9C2"), os.path.join(OUT, "step", "tiles", f"{n}.step"))
        with zipfile.ZipFile(os.path.join(OUT, "joro_deck_v9_step.zip"), "w", zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(os.path.join(OUT, "step")):
                for f in files:
                    p = os.path.join(root, f)
                    z.write(p, os.path.relpath(p, OUT))
        print(f"step {time.time() - t0:.0f}s")

    printed = {n: S.print_pose(n, t) for n, t in tiles.items()}
    printed_fit = {n: S.print_pose("top", t) for n, t in fits.items()}   # all fit pieces print face-down
    for n, t in {**printed, **printed_fit}.items():
        export_stl(t, os.path.join(OUT, "print", "stl", f"{n}.stl"), tolerance=0.02, angular_tolerance=0.15)
    write_3mf(os.path.join(OUT, "print", "joro_deck_v9.3mf"), list(printed.items()), "Joro + Magic Trackpad deck v9")
    write_3mf(os.path.join(OUT, "print", "joro_deck_v9_fit_test.3mf"), list(printed_fit.items()), "Joro deck v9 fit tests")
    print(f"done {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
