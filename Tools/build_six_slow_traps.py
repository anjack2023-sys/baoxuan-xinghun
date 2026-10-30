import bpy, math
from pathlib import Path
out=Path('C:/BeybladeUE/Saved/SixSlowTraps');out.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
def mat(name,color,metal,rough):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 return m
gold=mat('TrapGold',(.58,.35,.105),.78,.3);navy=mat('TrapNavy',(.018,.035,.065),.3,.7);rib=mat('TrapRib',(.045,.065,.09),.4,.65)
verts=[];faces=[];materials=[]
def patch(points,index,angle):
 start=len(verts);n=(math.cos(angle),math.sin(angle));t=(-n[1],n[0])
 for x,y in points:
  wx=n[0]*(1.23+y)+t[0]*x;wy=n[1]*(1.23+y)+t[1]*x
  verts.append((wx,wy,.42+.28*((wx*wx+wy*wy)/1.6**2)+.003))
 faces.append(tuple(range(start,len(verts))));materials.append(index)
def capsule(radius):
 return [(side*.13+radius*math.cos(a),radius*math.sin(a)) for side,offset in [(1,-math.pi/2),(-1,math.pi/2)] for a in [offset+j*math.pi/16 for j in range(17)]]
for i in range(6):
 angle=math.pi/2+i*math.pi/3
 patch(capsule(.09),0,angle)
 patch(capsule(.079),1,angle)
 for j in range(-9,10):
  x=j*.019
  patch([(x-.002,-.064),(x+.002,-.064),(x+.002,.064),(x-.002,.064)],2,angle)
mesh=bpy.data.meshes.new('SixSlowTraps');mesh.from_pydata(verts,[],faces);mesh.update()
# Layer the inset and ribs by fractions of a millimetre to avoid coplanar flicker.
for p,index in zip(mesh.polygons,materials):
 p.material_index=index
 for v in p.vertices:mesh.vertices[v].co.z+=index*.0004
for m in [gold,navy,rib]:mesh.materials.append(m)
obj=bpy.data.objects.new('SM_SixSlowTraps',mesh);bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active=obj;obj.select_set(True)
assert len(mesh.polygons)==6*21
bpy.ops.export_scene.fbx(filepath=str(out/'SM_SixSlowTraps.fbx'),use_selection=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',object_types={'MESH'},use_mesh_modifiers=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'six-slow-traps.blend'))

