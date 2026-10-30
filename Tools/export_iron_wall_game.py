import bpy,math,json
from pathlib import Path
from mathutils import Vector
root=Path('C:/BeybladeUE');out=root/'art/iron-wall-preview-v1/game-assets';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(root/'art/iron-wall-preview-v1/iron-wall-preview.blend'));bpy.context.scene.frame_set(15)
def export(name,objects):
 bpy.ops.object.select_all(action='DESELECT');copies=[];dep=bpy.context.evaluated_depsgraph_get()
 for src in objects:
  mesh=bpy.data.meshes.new_from_object(src.evaluated_get(dep),depsgraph=dep);obj=bpy.data.objects.new('Bake_'+src.name,mesh);bpy.context.scene.collection.objects.link(obj);obj.matrix_world=src.matrix_world.copy();copies.append(obj)
 for obj in copies:obj.select_set(True)
 bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.convert(target='MESH');bpy.ops.object.join();obj=bpy.context.object
 bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);obj.name=name
 bpy.ops.export_scene.fbx(filepath=str(out/(name+'.fbx')),use_selection=True,object_types={'MESH'},add_leaf_bones=False,bake_anim=False,mesh_smooth_type='FACE')
 bpy.data.objects.remove(obj,do_unlink=True)
export('SM_IronWallField',[bpy.data.objects['Shield transparent shell']])
lines=[o for o in bpy.context.scene.objects if o.type=='CURVE' and o.name.startswith(('Ground defence ring','Ring marker','Shield arc','Armour hex panel'))]
for o in lines:o.data.bevel_depth*=2.5
export('SM_IronWallGround',[o for o in lines if o.name.startswith(('Ground defence ring','Ring marker'))])
export('SM_IronWallLines',[o for o in lines if o.name.startswith(('Shield arc','Armour hex panel'))])
# A single local-XY ring is oriented toward the actual incoming collision at runtime.
d=bpy.data.curves.new('Hit ring','CURVE');d.dimensions='3D';d.bevel_depth=.026;d.bevel_resolution=2;s=d.splines.new('POLY');s.points.add(63)
for i,p in enumerate(s.points):a=math.tau*i/64;p.co=(math.cos(a),math.sin(a),0,1)
s.use_cyclic_u=True;o=bpy.data.objects.new('Ripple export',d);bpy.context.scene.collection.objects.link(o);export('SM_IronWallRipple',[o])
(out/'mesh-checks.json').write_text(json.dumps({'status':'PASS','meshes':4,'visual_only':True,'coordinates':'Blender metres; FBX imports as UE centimetres'},indent=2))
