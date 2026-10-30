import bpy,json
from pathlib import Path
from mathutils import Vector
out=Path(r'C:/Users/Administrator/Desktop/ai陀螺游戏/bey-art-refs/stadium-codex-v4');bpy.ops.wm.open_mainfile(filepath=str(out/'arena-v4-preview.blend'));s=bpy.context.scene
# New entrance pieces have no baked atlas UVs; use their own clean surface materials.
def material(name,color,metal,rough):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
floor=material('MAT_Entrance_Floor',(.17,.2,.24),.1,.65);wall=material('MAT_Entrance_Navy',(.025,.045,.075),.25,.5);gold=material('MAT_Entrance_Gold',(.55,.32,.09),.7,.3);steel=material('MAT_Entrance_Rail',(.045,.065,.09),.7,.4)
for o in bpy.data.collections['COL_Entrance'].objects:
 m=floor if 'WalkRamp' in o.name else gold if 'GoldCap' in o.name else steel if 'RailEnd' in o.name else wall;o.data.materials.clear();o.data.materials.append(m)
s.render.filepath=str(out/'arena-v4-entrance-wide.png');bpy.ops.wm.save_as_mainfile(filepath=str(out/'arena-v4-preview.blend'));bpy.ops.render.render(write_still=True)
c=s.camera;c.location=(0,-9.8,4.5);c.rotation_euler=(Vector((0,-4.5,.7))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=22;s.render.filepath=str(out/'arena-v4-entrance-detail.png');bpy.ops.render.render(write_still=True)
p=out/'QA_Entrance.json';r=json.loads(p.read_text(encoding='utf-8'));r['entrance_uses_independent_materials']=True;p.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
