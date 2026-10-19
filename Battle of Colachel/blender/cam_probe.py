"""Render probe stills from Today.blend with ad-hoc cameras.
blender -b Today.blend -P cam_probe.py -- OUT_DIR FRAME name:px,py,pz:lx,ly,lz:lens ...
Positions are in world coordinates, except that 'P+' / 'S+' prefixes give pillar- or stockade-relative offsets in the
film's frame: tangent TX/TY, normal NX/NY (inland). Use  p(dt,dn,z)  style: name:p,dt,dn,z:p,dt,dn,z:lens
"""
import math
import os
import sys

import bpy

HERE = r"C:\Users\sdevdarsshan\Desktop\Dev\Devv\BattleField\Battle of Colachel\blender"
sys.path.insert(0, HERE)
import siege_world as sw
import today_world as tw

NX, NY, TX, TY = sw.NX, sw.NY, sw.TX, sw.TY
PX, PY = tw.PILLAR
args = sys.argv[sys.argv.index("--") + 1:]
out, frame = args[0], int(args[1])
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 960, 540
sc.timeline_markers.clear()
sc.frame_set(frame)
sc.render.image_settings.file_format = "PNG"


def pt(s):
    kind, a, b, c = s.split(",")
    a, b, c = float(a), float(b), float(c)
    if kind == "p":      # relative to the pillar: along coast (a), inland (b), height c
        return (PX + TX * a + NX * b, PY + TY * a + NY * b, c)
    return (a, b, c)


cd = bpy.data.cameras.new("Probe")
cd.clip_start, cd.clip_end = 0.3, 120000
cam = bpy.data.objects.new("Probe", cd)
sc.collection.objects.link(cam)
tg = bpy.data.objects.new("ProbeT", None)
sc.collection.objects.link(tg)
c = cam.constraints.new("TRACK_TO")
c.target, c.track_axis, c.up_axis = tg, "TRACK_NEGATIVE_Z", "UP_Y"
sc.camera = cam
for spec in args[2:]:
    name, p0, p1, lens = spec.split(":")
    cam.location = pt(p0)
    tg.location = pt(p1)
    cd.lens = float(lens)
    bpy.context.view_layer.update()
    sc.render.filepath = os.path.join(out, name + ".png")
    bpy.ops.render.render(write_still=True)
