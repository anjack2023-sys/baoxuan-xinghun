import bpy,math,random
from pathlib import Path
out=Path('C:/BeybladeUE/art/changxuan-v1');out.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
d=bpy.data.curves.new('Flowing energy','CURVE');d.dimensions='3D';d.bevel_depth=.012;d.bevel_resolution=2
for start,length in [(0,5.6),(.35,1.4),(3.4,1.3)]:
 s=d.splines.new('POLY');s.points.add(95)
 for i,p in enumerate(s.points):
  a=start+i/95*length;r=1 if start==0 else 1.045
  p.co=(r*math.cos(a),r*math.sin(a),.015*math.sin(a*3),1)
o=bpy.data.objects.new('SM_ChangxuanRing',d);bpy.context.scene.collection.objects.link(o);o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
bpy.ops.export_scene.fbx(filepath=str(out/'SM_ChangxuanRing.fbx'),use_selection=True,object_types={'MESH'},bake_anim=False)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
random.seed(18)
for i in range(24):
 a=math.tau*i/24;r=random.uniform(.75,1.15)
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=random.uniform(.012,.025),location=(r*math.cos(a),r*math.sin(a),random.uniform(0,.55)))
 bpy.context.object.scale.z=1.7
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.join();o=bpy.context.object;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.name='SM_ChangxuanMotes'
assert len(o.data.vertices)==288
bpy.ops.export_scene.fbx(filepath=str(out/'SM_ChangxuanMotes.fbx'),use_selection=True,object_types={'MESH'},bake_anim=False)
