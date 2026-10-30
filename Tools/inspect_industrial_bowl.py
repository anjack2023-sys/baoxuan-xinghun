"""Inspect and render the supplied GLB unchanged; does not export or edit the model."""
import json
import math
from pathlib import Path
import bpy
from mathutils import Vector

root = Path(__file__).resolve().parents[1]
output = root / "art/model-checks/industrial-bowl-v1"
output.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(root / "_import_staging/StadiumIndustrial/industrial-bowl-original.glb"))
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
assert meshes, "No mesh imported"
points = [o.matrix_world @ Vector(p) for o in meshes for p in o.bound_box]
low = Vector([min(p[i] for p in points) for i in range(3)])
high = Vector([max(p[i] for p in points) for i in range(3)])
center, size = (low+high)/2, high-low
assert size.z < min(size.x, size.y), "Unexpected orientation: inspect before rendering"
scene = bpy.context.scene
depsgraph = bpy.context.evaluated_depsgraph_get()
radius = min(size.x, size.y)/2
samples = []
for angle in range(0, 360, 45):
    for fraction in [0, 0.25, 0.5, 0.7, 0.85, 0.95]:
        a = math.radians(angle)
        x, y = center.x + radius*fraction*math.cos(a), center.y + radius*fraction*math.sin(a)
        hit, p, normal, face, obj, matrix = scene.ray_cast(depsgraph, Vector((x,y,high.z+1)), Vector((0,0,-1)))
        samples.append({"angle_deg":angle, "radius_fraction":fraction, "x":x,"y":y,
                        "z":p.z if hit else None, "normal":list(normal) if hit else None})
report = {"source":"industrial-bowl-original.glb", "geometry_changed":False,
          "bounds_min_m":list(low), "bounds_max_m":list(high), "dimensions_m":list(size),
          "objects":[{"name":o.name,"vertices":len(o.data.vertices),"triangles":sum(len(p.vertices)-2 for p in o.data.polygons),
                      "materials":len(o.data.materials),"uv_layers":len(o.data.uv_layers)} for o in meshes],
          "textures":[{"name":im.name,"width":im.size[0],"height":im.size[1],"packed":im.packed_file is not None} for im in bpy.data.images if im.type=="IMAGE"],
          "height_samples":samples}
(output / "inspection.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
scene.render.engine = "CYCLES"
scene.cycles.samples = 16
scene.cycles.use_denoising = True
scene.render.resolution_x = 1000
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.world = bpy.data.worlds.new("InspectionWorld")
scene.world.color = (0.2,0.2,0.2)
scene.view_settings.view_transform = "AgX"
for location, energy, light_size in [((1,-1,2),180,2),((-1,0,1),100,2),((0,1,2),140,2)]:
    data = bpy.data.lights.new("InspectionLight", "AREA")
    data.energy = energy; data.shape="DISK"; data.size = light_size
    light = bpy.data.objects.new(data.name,data); scene.collection.objects.link(light)
    light.location = center + Vector(location)*max(size)
    light.rotation_euler = (center-light.location).to_track_quat("-Z","Y").to_euler()
camera_data = bpy.data.cameras.new("InspectionCamera")
camera = bpy.data.objects.new("InspectionCamera", camera_data)
scene.collection.objects.link(camera); scene.camera = camera
camera_data.type = "ORTHO"; camera_data.ortho_scale = max(size)*1.25
for name, offset in [("top",(0,0,3)),("three-quarter",(1,-1.6,1.7)),("side",(0,-3,0.15))]:
    camera.location = center + Vector(offset)*max(size)
    camera.rotation_euler = (center-camera.location).to_track_quat("-Z","Y").to_euler()
    scene.render.filepath = str(output / (name+".png"))
    bpy.ops.render.render(write_still=True)
print("INDUSTRIAL_BOWL_INSPECTION_COMPLETE", str(output))
