"""Render build123d shapes to PNG with three.js in headless Chromium.

render(parts, out_png, camera) where parts = [(shape, "#rrggbb", opacity, edges), ...]
camera = dict(pos=(x,y,z), target=(x,y,z), ortho=<view height mm> or fov=deg)
Needs: node + playwright (preinstalled) and `npm install three` in RENDER_DIR.
"""
import json, os, shutil, subprocess, socket, threading, http.server, functools
from build123d import export_stl

HERE = os.path.dirname(os.path.abspath(__file__))
RENDER_DIR = os.environ.get("RENDER_DIR", os.path.join(HERE, "_render"))


def _free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def render(parts, out_png, camera, size=(1600, 1000), tol=0.08):
    os.makedirs(RENDER_DIR, exist_ok=True)
    shutil.copy(os.path.join(HERE, "viewer.html"), RENDER_DIR)
    desc = {"width": size[0], "height": size[1], "camera": camera, "parts": []}
    for i, item in enumerate(parts):
        shape, color = item[0], item[1]
        if shape is None or not getattr(shape, "_wrapped", True) or not shape.solids():
            continue
        opacity = item[2] if len(item) > 2 else 1.0
        edges = item[3] if len(item) > 3 else False
        fn = f"p{i}.stl"
        export_stl(shape, os.path.join(RENDER_DIR, fn), tolerance=tol, angular_tolerance=0.3)
        desc["parts"].append({"file": fn, "color": color, "opacity": opacity, "edges": edges})
    with open(os.path.join(RENDER_DIR, "scene.json"), "w") as f:
        json.dump(desc, f)
    port = _free_port()
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=RENDER_DIR)
    handler.log_message = lambda *a, **k: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    th = threading.Thread(target=srv.serve_forever, daemon=True); th.start()
    try:
        subprocess.run(["node", os.path.join(HERE, "shot.js"), str(port), os.path.abspath(out_png)],
                       check=True, cwd=RENDER_DIR, env={**os.environ, "NODE_PATH": os.pathsep.join(filter(None, [os.environ.get("NODE_PATH"), os.path.join(RENDER_DIR, "node_modules")]))})
    finally:
        srv.shutdown()
