"""Character line-up for approving the figures: every kind side by side on the
camp sand, same sky, sun and haze as the film. Renders renders/lineup.png.

Run inside Blender (MCP) after film.py:  exec(open(r"<this file>").read())
"""
import importlib
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.path.abspath(os.getcwd())
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import bpy
import colachel_kit as kit
import colachel_world as world
importlib.reload(kit)
importlib.reload(world)

film = bpy.context.scene
sc = bpy.data.scenes.get("Lineup") or bpy.data.scenes.new("Lineup")
for ob in list(sc.collection.all_objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc.world = film.world
for attr in ("engine", "resolution_x", "resolution_y"):
    setattr(sc.render, attr, getattr(film.render, attr))
sc.eevee.taa_render_samples = 64
sc.eevee.use_raytracing = True
sc.eevee.use_fast_gi = True
sc.view_settings.view_transform = film.view_settings.view_transform
sc.view_settings.look = film.view_settings.look
coll = sc.collection

mb = kit.MB()
mb.box(kit.S(30, 30, 0.1) @ kit.T(0, 0, -0.5), "sand")
mb.obj("LineupGround", coll)
for ob in bpy.data.objects:
    if ob.name == "Sun" and ob.type == "LIGHT":
        sc.collection.objects.link(ob)
        break
kinds = [("villager", "cloth_w"), ("villager_robe", "cloth_t"), ("nair", "cloth_w"), ("nair_spear", "cloth_w"),
         ("commander", "cloth_w"), ("king", "cloth_w"), ("dutch", "cloth_w"), ("dutch", "cloth_w")]
for i, (kind, cloth) in enumerate(kinds):
    ob = kit.make_figure(f"Lineup_{kind}{i}", coll, kind, seed=i, cloth=cloth)
    ob.location = ((i - (len(kinds) - 1) / 2) * 0.95, 0, 0)
    ob.rotation_euler[2] = math.radians(-12 if i % 2 else 12)

cd = bpy.data.cameras.new("LineupCam")
cd.lens = 50
cam = bpy.data.objects.new("LineupCam", cd)
coll.objects.link(cam)
cam.location = (0.3, 7.6, 1.75)
cam.rotation_euler = (math.radians(86), 0, math.radians(180))
sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.image_settings.media_type = "IMAGE"
sc.render.image_settings.file_format = "PNG"
sc.render.filepath = os.path.join(HERE, "renders", "lineup.png")
bpy.ops.render.render(write_still=True, scene=sc.name)
print("lineup rendered")
