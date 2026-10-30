import bpy,math,json
from pathlib import Path
out=Path('C:/BeybladeUE/art/chiwen-v1');out.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
v=[];f=[]
for j in range(10):
 start=math.tau*j/10;base=len(v)
 for i in range(8):
  t=i/7;a=start+t*.75;r=.92-.32*t;w=.13*(1-t)**.7
  for side in [-1,1]:v.append((r*math.cos(a)+side*w*math.cos(a+math.pi/2),r*math.sin(a)+side*w*math.sin(a+math.pi/2),t*(.85+.22*(j%3))))
 for i in range(7):k=base+i*2;f.extend([(k,k+1,k+2),(k+1,k+3,k+2)])
m=bpy.data.meshes.new('Flame ribbons');m.from_pydata(v,[],f);m.update();o=bpy.data.objects.new('SM_ChiwenFlames',m);bpy.context.scene.collection.objects.link(o);o.select_set(True);bpy.context.view_layer.objects.active=o
assert len(m.polygons)==140
bpy.ops.export_scene.fbx(filepath=str(out/'SM_ChiwenFlames.fbx'),use_selection=True,object_types={'MESH'},bake_anim=False)
(out/'export-check.json').write_text(json.dumps({'status':'PASS','triangles':140,'unit':'metres'}))
