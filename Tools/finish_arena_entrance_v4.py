import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector
out=Path(r'C:/Users/Administrator/Desktop/ai陀螺游戏/bey-art-refs/stadium-codex-v4');bpy.ops.wm.open_mainfile(filepath=str(out/'arena-v4-preview.blend'));s=bpy.context.scene
for ob in bpy.data.collections['COL_Entrance'].objects:
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(ob.data);bm.free()
# Finish the cut rail ends with posts supported by each tier.
for radius,floor,top in [(4.55,.1,1.1),(4.75,1.55,2.3),(7.1,2.15,3.1),(9.3,2.75,3.7),(11.5,2.75,3.7)]:
 for sign in [-1,1]:
  x=sign*1.54;y=-math.sqrt(radius*radius-x*x)
  bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=.045,depth=top-floor,location=(x,y,(floor+top)/2));o=bpy.context.object;o.name='SM_Entrance_RailEnd_%s_%s'%(radius,sign);o.data.materials.append(bpy.data.materials['MAT_Metal_Structure'])
  for c in list(o.users_collection):c.objects.unlink(o)
  bpy.data.collections['COL_Entrance'].objects.link(o)
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
for x in [-.95,0,.95]:
 for i in range(12):
  y=-12.3+i*8.1/11;hit,loc,n,_,ob,_=s.ray_cast(deps,Vector((x,y,5.4)),Vector((0,0,-1)),distance=7);assert hit and ob.name=='SM_Entrance_WalkRamp' and n.z>.95,(ob.name,n)
  blocked,*_=s.ray_cast(deps,loc+Vector((0,0,.12)),Vector((0,0,1)),distance=2.05);assert not blocked
cam=s.camera;s.cycles.samples=24;s.render.filepath=str(out/'arena-v4-entrance-wide.png');bpy.ops.wm.save_as_mainfile(filepath=str(out/'arena-v4-preview.blend'));bpy.ops.render.render(write_still=True)
cam.location=(4,-8,4.4);cam.rotation_euler=(Vector((0,-5.6,1.1))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=24;s.render.filepath=str(out/'arena-v4-entrance-detail.png');bpy.ops.render.render(write_still=True)
p=out/'QA_Entrance.json';r=json.loads(p.read_text(encoding='utf-8'));r.update(surface_normals_verified=True,rail_ends_finished=True);p.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
