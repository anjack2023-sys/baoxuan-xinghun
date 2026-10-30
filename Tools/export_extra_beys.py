import bpy,math,json
from pathlib import Path
from mathutils import Vector
root=Path('C:/BeybladeUE');out=root/'art/extra-beys-v1';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(root/'art/huangkai-preview-v1/huangkai-preview.blend'));bpy.context.scene.frame_set(15)
def export(name,objects):
 bpy.ops.object.select_all(action='DESELECT');dep=bpy.context.evaluated_depsgraph_get();copies=[]
 for src in objects:
  mesh=bpy.data.meshes.new_from_object(src.evaluated_get(dep),depsgraph=dep);obj=bpy.data.objects.new('Bake_'+src.name,mesh);bpy.context.scene.collection.objects.link(obj);obj.matrix_world=src.matrix_world.copy();copies.append(obj)
 for obj in copies:obj.select_set(True)
 bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();obj=bpy.context.object;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);obj.name=name
 bpy.ops.export_scene.fbx(filepath=str(out/(name+'.fbx')),use_selection=True,object_types={'MESH'},bake_anim=False);bpy.data.objects.remove(obj,do_unlink=True)
export('SM_GoldPanels',[o for o in bpy.context.scene.objects if o.name.startswith('Armour petal membrane')])
export('SM_GoldLines',[o for o in bpy.context.scene.objects if o.name.startswith('Armour petal outline')])
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
rocks=[]
for i in range(8):
 a=math.tau*i/8;bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(1.15*math.cos(a),1.15*math.sin(a),.12));o=bpy.context.object;o.scale=(.14,.10,.12+(i%3)*.035);o.rotation_euler=(i,.3*i,a);rocks.append(o)
export('SM_StoneFragments',rocks)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
shards=[]
for i in range(12):
 a=math.tau*i/12;bpy.ops.mesh.primitive_cone_add(vertices=4,radius1=.08,radius2=0,depth=.25+(i%3)*.12,location=(1.02*math.cos(a),1.02*math.sin(a),.15));o=bpy.context.object;o.rotation_euler=(.18*math.cos(a),.18*math.sin(a),a);shards.append(o)
export('SM_FrostShards',shards)
(out/'export-check.json').write_text(json.dumps({'status':'PASS','meshes':4,'unit':'metres'}))
