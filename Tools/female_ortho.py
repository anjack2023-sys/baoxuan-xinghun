import bpy
from pathlib import Path
from mathutils import Vector
p=Path(r'C:/Users/Administrator/Desktop/ai陀螺游戏/beyblade-unreal-prototype/art/female-launch-v1')
bpy.ops.wm.open_mainfile(filepath=str(p/'female-source.blend'));s=bpy.context.scene;c=s.camera
for name,loc in [('front-ortho',(4,0,.86)),('side-ortho',(0,-4,.86))]:
 c.location=loc;c.rotation_euler=(Vector((0,0,.86))-c.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(p/(name+'.png'));bpy.ops.render.render(write_still=True)
