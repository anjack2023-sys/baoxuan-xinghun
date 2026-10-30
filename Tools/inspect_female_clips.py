import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(r'C:/Users/Administrator/Desktop/ai陀螺游戏/beyblade-unreal-prototype/art/female-launch-v1')
bpy.ops.wm.open_mainfile(filepath=str(root/'female-rigged-source.blend'))
r=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');actions=list(bpy.data.actions)
for track in list(r.animation_data.nla_tracks):r.animation_data.nla_tracks.remove(track)
for o in bpy.context.scene.objects:
 if o.type=='MESH' and not any(m.type=='ARMATURE' for m in o.modifiers):o.hide_render=True
s=bpy.context.scene;s.world=bpy.data.worlds.new('ClipReviewWorld');s.world.color=(.1,.13,.17)
bpy.ops.object.camera_add(location=(2,-2,1.3));c=bpy.context.object;c.rotation_euler=(Vector((0,0,.5))-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=1.4;s.camera=c
s.render.engine='BLENDER_WORKBENCH';s.display.shading.color_type='TEXTURE';s.render.resolution_x=360;s.render.resolution_y=420;s.render.resolution_percentage=100
report=[]
for action in actions:
 r.animation_data.action=action
 if action.slots:r.animation_data.action_slot=action.slots[0]
 frame=round(sum(action.frame_range)/2);s.frame_set(frame);s.render.filepath=str(root/('original-'+action.name+'.png'));bpy.ops.render.render(write_still=True)
 report.append({'name':action.name,'frame_range':list(action.frame_range),'sample_frame':frame})
(root/'original-clips.json').write_text(json.dumps(report,indent=2))
