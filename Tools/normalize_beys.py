"""Export centered, bottom-origin, 44 cm diameter static bey assets for Unreal."""
import json
from pathlib import Path
import bpy
from mathutils import Matrix, Vector

project = Path(__file__).resolve().parents[1]
outputs = project / "_import_staging" / "Normalized"
outputs.mkdir(exist_ok=True)
report = []
for name, source in [("RedLotus", "red-lotus-tripo-v2.glb"), ("BeyB", "bey-b-tripo-v2.fbx")]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    path = project / "_import_staging" / "Beys" / source
    if path.suffix == ".glb":
        bpy.ops.import_scene.gltf(filepath=str(path))
    else:
        bpy.ops.import_scene.fbx(filepath=str(path))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    assert meshes, source
    points = [obj.matrix_world @ vertex.co for obj in meshes for vertex in obj.data.vertices]
    low = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    scale = 0.44 / max(high.x - low.x, high.y - low.y)
    origin = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, low.z))
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        transform = obj.matrix_world.copy()
        for vertex in obj.data.vertices:
            vertex.co = (transform @ vertex.co - origin) * scale
        obj.parent = None
        obj.matrix_world = Matrix.Identity(4)
        obj.select_set(True)
    normalized = [v.co for obj in meshes for v in obj.data.vertices]
    assert abs(min(v.z for v in normalized)) < 0.00001
    assert abs((min(v.x for v in normalized) + max(v.x for v in normalized)) / 2) < 0.00001
    assert abs((min(v.y for v in normalized) + max(v.y for v in normalized)) / 2) < 0.00001
    target = outputs / (name + "_Centered.fbx")
    bpy.ops.export_scene.fbx(filepath=str(target), use_selection=True, object_types={"MESH"},
                             add_leaf_bones=False, bake_anim=False, axis_forward="-Y", axis_up="Z")
    report.append({"source": str(path), "output": str(target), "diameter_m": 0.44,
                   "height_m": max(v.z for v in normalized), "source_offset": list(origin)})
(outputs / "normalization_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("NORMALIZE_BEYS_PASS")
