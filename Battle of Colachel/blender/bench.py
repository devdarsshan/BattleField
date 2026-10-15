"""Time one busy frame under different render settings (run with blender -b Colachel.blend -P bench.py)."""
import time

import bpy

sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.filepath = "//renders/bench_tmp.png"
FRAME = 612
haze = bpy.data.objects.get("Haze")
ee = sc.eevee
base = dict(samples=ee.taa_render_samples, rt=ee.use_raytracing, gi=ee.use_fast_gi)


def run(label, setup=lambda: None, undo=lambda: None):
    setup()
    t = time.time()
    sc.frame_set(FRAME)
    t_eval = time.time() - t
    t = time.time()
    bpy.ops.render.render(write_still=False)
    print(f"BENCH {label:28s} eval {t_eval:5.2f}s  render {time.time() - t:5.2f}s", flush=True)
    undo()


run("warm-up (shader compile)")
run("baseline (48 samples)")
run("no haze volume", lambda: setattr(haze, "hide_render", True), lambda: setattr(haze, "hide_render", False))
run("no ray tracing", lambda: setattr(ee, "use_raytracing", False), lambda: setattr(ee, "use_raytracing", base["rt"]))
run("no fast GI", lambda: setattr(ee, "use_fast_gi", False), lambda: setattr(ee, "use_fast_gi", base["gi"]))
run("16 samples", lambda: setattr(ee, "taa_render_samples", 16), lambda: setattr(ee, "taa_render_samples", base["samples"]))
run("1080p baseline", lambda: setattr(sc.render, "resolution_percentage", 150),
    lambda: setattr(sc.render, "resolution_percentage", 100))
