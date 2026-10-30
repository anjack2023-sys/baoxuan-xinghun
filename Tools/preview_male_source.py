import bpy,math
from mathutils import Vector
from pathlib import Path
p=Path(r'C:/Users/Administrator/Desktop/ai陀螺游戏/beyblade-unreal-prototype')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(next((p/'Saved/FeelRef60/work/LabSources/TripoMaleLauncher-v1').glob('*.fbx'))),use_anim=False)
s=bpy.context.scene
s.world=bpy.data.worlds.new('World');s.world.color=(.15,.15,.15)
bpy.ops.object.camera_add(location=(2, -3,1.7));c=bpy.context.object;c.rotation_euler=(Vector((0,0,.5))-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=1.25;s.camera=c
s.render.engine='BLENDER_WORKBENCH';s.display.shading.color_type='TEXTURE';s.render.resolution_x=700;s.render.resolution_y=700;s.render.resolution_percentage=100;s.render.filepath=str(p/'art/launch-review-v2/male-source.png');bpy.ops.render.render(write_still=True)
