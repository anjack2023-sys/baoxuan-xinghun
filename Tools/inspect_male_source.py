import bpy,json
from pathlib import Path
bpy.ops.wm.read_factory_settings(use_empty=True)
p=Path(r'C:/Users/Administrator/Desktop/ai陀螺游戏/beyblade-unreal-prototype')
bpy.ops.import_scene.fbx(filepath=str(next((p/'Saved/FeelRef60/work/LabSources/TripoMaleLauncher-v1').glob('*.fbx'))),use_anim=False)
r={'objects':[],'bones':{}}
for o in bpy.context.scene.objects:
 r['objects'].append({'name':o.name,'type':o.type,'matrix':[list(v) for v in o.matrix_world],'parent':o.parent.name if o.parent else None,'bounds':[list(o.matrix_world@__import__('mathutils').Vector(v)) for v in o.bound_box] if o.type=='MESH' else [],'materials':[m.name for m in o.data.materials] if o.type=='MESH' else []})
 if o.type=='ARMATURE':
  for b in o.data.bones:r['bones'][b.name]={'parent':b.parent.name if b.parent else None,'head':list(o.matrix_world@b.head_local),'tail':list(o.matrix_world@b.tail_local)}
(p/'art/launch-review-v2/male-source-inspect.json').write_text(json.dumps(r,indent=2))
