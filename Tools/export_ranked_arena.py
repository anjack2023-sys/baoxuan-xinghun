import bpy,json
from pathlib import Path
root=Path(r'C:/Users/Administrator/Desktop/ai陀螺游戏/bey-art-refs/stadium-doubao')
bpy.ops.wm.open_mainfile(filepath=str(root/'bey-arena-environment-v2.blend'))
out=Path('C:/BeybladeUE/Saved/ArenaImport');out.mkdir(parents=True,exist_ok=True)
mats={}
for m in bpy.data.materials:
 p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) if m.use_nodes else None
 imgs=[bpy.path.abspath(n.image.filepath) for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image] if m.use_nodes else []
 mats[m.name]={'base':list(p.inputs['Base Color'].default_value) if p else list(m.diffuse_color),'metal':p.inputs['Metallic'].default_value if p else 0,'rough':p.inputs['Roughness'].default_value if p else .7,'emission':list(p.inputs['Emission Color'].default_value) if p else [0,0,0,1],'strength':p.inputs['Emission Strength'].default_value if p else 0,'images':imgs}
mesh=[o for o in bpy.context.scene.objects if o.type=='MESH'];bpy.ops.object.select_all(action='DESELECT')
for o in mesh:o.select_set(True)
bpy.context.view_layer.objects.active=mesh[0];bpy.ops.object.make_single_user(object=True,obdata=True,material=False,animation=False);bpy.ops.object.convert(target='MESH');bpy.ops.object.join()
bpy.ops.export_scene.fbx(filepath=str(out/'SM_RankedArena.fbx'),use_selection=True,object_types={'MESH'},apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',path_mode='ABSOLUTE',add_leaf_bones=False)
(out/'materials.json').write_text(json.dumps(mats,indent=2),encoding='utf-8')
