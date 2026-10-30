import bpy,json
from pathlib import Path
from mathutils import Vector
out=Path(r'C:/Users/Administrator/Desktop/ai陀螺游戏/bey-art-refs/stadium-codex-v3');bpy.ops.wm.open_mainfile(filepath=str(out/'arena-v3-preview.blend'));s=bpy.context.scene
for o in s.objects:
 if o.name.startswith('SM_Arena_Banner_00'):o.location.z+=1.2
s.cycles.samples=24;s.render.filepath=str(out/'arena-v3-final-wide.png');bpy.ops.wm.save_as_mainfile(filepath=str(out/'arena-v3-preview.blend'));bpy.ops.render.render(write_still=True)
c=s.camera;c.location=(0,-1.8,4.4);c.rotation_euler=(Vector((0,6.4,3.65))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=42;s.render.filepath=str(out/'arena-v3-final-scoreboard.png');bpy.ops.render.render(write_still=True)
p=out/'QA_V3.json';r=json.loads(p.read_text(encoding='utf-8'));r['main_title_occlusion_fixed']=True;p.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
