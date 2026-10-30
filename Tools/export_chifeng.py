import bpy,math,random
from pathlib import Path
from mathutils import Vector
out=Path('C:/BeybladeUE/art/chifeng-v1');out.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
random.seed(62)
for i in range(28):
 a=random.uniform(-math.pi,math.pi);v=Vector((math.cos(a),math.sin(a),random.uniform(.1,1.2))).normalized();length=random.uniform(.16,.5)
 bpy.ops.mesh.primitive_cone_add(vertices=4,radius1=.018,radius2=0,depth=length,location=v*random.uniform(.2,.8))
 bpy.context.object.rotation_euler=v.to_track_quat('Z','Y').to_euler()
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.join();o=bpy.context.object;o.name='SM_ChifengSparks';bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
assert len(o.data.vertices)==140
bpy.ops.export_scene.fbx(filepath=str(out/'SM_ChifengSparks.fbx'),use_selection=True,object_types={'MESH'},bake_anim=False)

bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
d=bpy.data.curves.new('Attack arcs','CURVE');d.dimensions='3D';d.bevel_depth=.008;d.bevel_resolution=2
for j in range(3):
 s=d.splines.new('POLY');s.points.add(49)
 for i,p in enumerate(s.points):
  a=math.tau*j/3+i/49*1.65;r=1.+.012*math.sin(a*27)
  p.co=(r*math.cos(a),r*math.sin(a),0,1)
for j in range(18):
 a=math.tau*j/18;s=d.splines.new('POLY');s.points.add(1)
 for i,p in enumerate(s.points):p.co=((.98+i*.055)*math.cos(a),(.98+i*.055)*math.sin(a),0,1)
o=bpy.data.objects.new('SM_ChifengRing',d);bpy.context.scene.collection.objects.link(o);o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
bpy.ops.export_scene.fbx(filepath=str(out/'SM_ChifengRing.fbx'),use_selection=True,object_types={'MESH'},bake_anim=False)
