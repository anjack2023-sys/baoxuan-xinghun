import bpy,math,json
from pathlib import Path
out=Path('C:/BeybladeUE/art/hengren-v1');out.mkdir(exist_ok=True)
def clear():
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def curve(name,paths):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=.010;d.bevel_resolution=2
 for points in paths:
  s=d.splines.new('POLY');s.points.add(len(points)-1)
  for p,v in zip(s.points,points):p.co=(*v,1)
 o=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(o);o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
 bpy.ops.export_scene.fbx(filepath=str(out/(name+'.fbx')),use_selection=True,object_types={'MESH'},bake_anim=False)
 assert len(bpy.context.object.data.vertices)>100
clear();paths=[]
for j in range(4):
 start=j*math.pi/2
 paths.append([(math.cos(a),math.sin(a),0) for a in [start+i/48*1.02 for i in range(49)]])
 end=start+1.02
 paths.append([(math.cos(end-.12)*.95,math.sin(end-.12)*.95,0),(math.cos(end)*1.04,math.sin(end)*1.04,0),(math.cos(end-.12)*1.09,math.sin(end-.12)*1.09,0)])
curve('SM_HengrenArc',paths)
clear();paths=[]
for j in range(4):
 a=math.tau*j/4
 pts=[(.82,-.14),(.96,-.14),(1.08,0),(.96,.14),(.82,.14)]
 paths.append([(x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a),0) for x,y in pts])
for j in range(8):
 a=j*math.tau/8;paths.append([(.95*math.cos(a),.95*math.sin(a),0),(1.02*math.cos(a),1.02*math.sin(a),0)])
curve('SM_HengrenSeal',paths)
(out/'export-check.json').write_text(json.dumps({'status':'PASS','meshes':2,'unit':'metres'}))
