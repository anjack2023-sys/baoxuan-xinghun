import bpy,json
from pathlib import Path
from mathutils import Vector
p=Path(r'C:/Users/Administrator/Desktop/ai陀螺游戏/beyblade-unreal-prototype/art/female-launch-v1')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=r'D:/Documents/Downloads/tripo_convert_32274143-92db-4948-bd18-76b0890719f6.glb')
r=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
report={'objects':[(o.name,o.type,[list(v) for v in o.matrix_world]) for o in bpy.context.scene.objects],'bones':{b.name:{'head':list(r.matrix_world@b.head_local),'tail':list(r.matrix_world@b.tail_local),'parent':b.parent.name if b.parent else None} for b in r.data.bones},'actions':[a.name for a in bpy.data.actions]}
(p/'rigged-source-inspect.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(p/'female-rigged-source.blend'))
