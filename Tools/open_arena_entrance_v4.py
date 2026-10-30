import bpy,math,json
from pathlib import Path
from mathutils import Vector
root=Path(r'C:/Users/Administrator/Desktop/ai陀螺游戏/bey-art-refs');out=root/'stadium-codex-v4';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(root/'stadium-codex-v3/arena-v3-preview.blend'));scene=bpy.context.scene
# Cut a continuous 3m opening through every front wall, tier, and railing.
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,-8.5,2.25));cutter=bpy.context.object;cutter.name='TMP_EntranceCut';cutter.dimensions=(3.0,9.0,6.5);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
changed=[]
for ob in list(scene.objects):
 if ob==cutter or ob.type!='MESH':continue
 points=[ob.matrix_world@Vector(v) for v in ob.bound_box]
 if min(v.x for v in points)>=1.5 or max(v.x for v in points)<=-1.5 or min(v.y for v in points)>=-4 or max(v.y for v in points)<=-13 or min(v.z for v in points)>=5.5 or max(v.z for v in points)<=-1:continue
 ob.data=ob.data.copy();bpy.context.view_layer.objects.active=ob
 mod=ob.modifiers.new('Entrance opening','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
 bpy.ops.object.modifier_apply(modifier=mod.name);changed.append(ob.name)
 if not ob.data.vertices:bpy.data.objects.remove(ob,do_unlink=True)
bpy.data.objects.remove(cutter,do_unlink=True)
coll=bpy.data.collections.new('COL_Entrance');scene.collection.children.link(coll)
def wedge(name,xmin,xmax,y1,y2,z1,z2,depth,material):
 verts=[(xmin,y1,z1),(xmax,y1,z1),(xmax,y2,z2),(xmin,y2,z2),(xmin,y1,z1-depth),(xmax,y1,z1-depth),(xmax,y2,z2-depth),(xmin,y2,z2-depth)]
 faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);coll.objects.link(o);o.data.materials.append(material);return o
floor=bpy.data.materials['MAT_Floor_Concrete'];wall=bpy.data.materials['MAT_Wall_Panel'];gold=bpy.data.materials['MAT_Trim_Gold']
ramp=wedge('SM_Entrance_WalkRamp',-1.3,1.3,-12.7,-4.0,2.75,.1,.18,floor)
for side in [-1,1]:
 x=side*1.4;wedge('SM_Entrance_GuardWall_'+str(side),x-.1,x+.1,-12.7,-4.0,3.65,1.0,.9,wall)
 wedge('SM_Entrance_GoldCap_'+str(side),x-.12,x+.12,-12.7,-4.0,3.7,1.05,.055,gold)
# Check a human-size corridor along the real mesh surface, not just the image.
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();samples=[]
for i in range(12):
 y=-12.3+i*(8.1/11);expected=2.75+(y+12.7)/8.7*(.1-2.75)
 for x in [-.95,0,.95]:
  hit,loc,normal,face,ob,matrix=scene.ray_cast(deps,Vector((x,y,5.4)),Vector((0,0,-1)),distance=7)
  assert hit and ob.name.startswith('SM_Entrance_WalkRamp') and abs(loc.z-expected)<.015,(x,y,ob.name if ob else None,loc)
  blocked,*_=scene.ray_cast(deps,loc+Vector((0,0,.12)),Vector((0,0,1)),distance=2.05);assert not blocked,(x,y,'headroom')
 samples.append({'y':y,'floor_z':expected})
cam=scene.camera;cam.location=(0,-10.8,5.7);cam.rotation_euler=(Vector((0,1.1,1.6))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=25
scene.cycles.samples=24;scene.render.resolution_x=1600;scene.render.resolution_y=900;scene.render.filepath=str(out/'arena-v4-entrance-wide.png')
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(out/'arena-v4-preview.blend'));bpy.ops.render.render(write_still=True)
cam.location=(4,-8,4.4);cam.rotation_euler=(Vector((0,-5.6,1.1))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=24;scene.render.filepath=str(out/'arena-v4-entrance-detail.png');bpy.ops.render.render(write_still=True)
(out/'QA_Entrance.json').write_text(json.dumps({'status':'PASS','clear_width_m':2.6,'ramp_grade_degrees':math.degrees(math.atan(2.65/8.7)),'verified_headroom_m':2.05,'ray_samples':36,'changed_meshes':changed,'floor_samples':samples,'bowl_added':False,'game_integration':False},ensure_ascii=False,indent=2),encoding='utf-8')
