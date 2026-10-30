import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(r'C:/Users/Administrator/Desktop/ai陀螺游戏/beyblade-unreal-prototype')
out=root/'art/portrait-refine-v1';report={}
for who,path in [('male','art/male-launch-review-v2/male-redcord-launch.blend'),('female','art/female-rigged-launch-v1/female-redcord-launch.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(root/path));s=bpy.context.scene
 rig=next(o for o in s.objects if o.type=='ARMATURE');rig.data.pose_position='REST'
 mesh=next(o for o in s.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers))
 for o in s.objects:
  if o.type=='MESH' and o!=mesh:o.hide_render=True
 head=rig.data.bones['Head'].head_local;neck=rig.data.bones['NeckTwist01'].head_local
 report[who]={'head':list(head),'neck':list(neck),'bounds':[[min(v.co[k] for v in mesh.data.vertices),max(v.co[k] for v in mesh.data.vertices)] for k in range(3)],'verts':len(mesh.data.vertices)}
 c=s.camera;target=head+Vector((0,-.03,.075));c.location=target+Vector((.3,-1,.08));c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=.44
 s.render.engine='BLENDER_WORKBENCH';s.display.shading.color_type='TEXTURE';s.display.shading.light='STUDIO';s.display.shading.show_cavity=False
 s.render.resolution_x=640;s.render.resolution_y=720;s.render.resolution_percentage=100;s.render.filepath=str(out/(who+'-head-before.png'));bpy.ops.render.render(write_still=True)
(out/'source-inspect.json').write_text(json.dumps(report,indent=2))
