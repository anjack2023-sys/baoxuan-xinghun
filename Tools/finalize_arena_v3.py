import bpy,json,math
from pathlib import Path
from mathutils import Vector
out=Path(r'C:/Users/Administrator/Desktop/ai陀螺游戏/bey-art-refs/stadium-codex-v3');bpy.ops.wm.open_mainfile(filepath=str(out/'arena-v3-preview.blend'));scene=bpy.context.scene
for ob in bpy.data.collections['COL_Scoreboard'].objects:ob.location.y-=2.6;ob.location.z+=.55
for ob in scene.objects:
 if ob.name.startswith('SM_Arena_Screen_00_'):ob.location.z+=1.1
# A narrow blue panel alternate makes the low wall readable without extra geometry.
accent=bpy.data.materials.new('MAT_V3_AlternateNavy');accent.use_nodes=True;p=next(n for n in accent.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(.032,.065,.12,1);p.inputs['Metallic'].default_value=.35;p.inputs['Roughness'].default_value=.48
count=0
for ob in scene.objects:
 if ob.type=='MESH' and ob.name.startswith('SM_Arena_Barrier_Panel_') and 'Line' not in ob.name:
  if int(ob.name.rsplit('_',1)[1])%2==0:
   ob.data=ob.data.copy();ob.data.materials.clear();ob.data.materials.append(accent);count+=1
cam=scene.camera;cam.location=(0,-10.8,5.7);cam.rotation_euler=(Vector((0,1.1,1.6))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=25
scene.cycles.samples=40;scene.render.filepath=str(out/'arena-v3-final-wide.png')
assert bpy.data.objects['TXT_ScoreP1'].data.body=='0' and bpy.data.objects['TXT_ScoreP2'].data.body=='0'
assert bpy.data.collections.get('COL_Scoreboard') and not any('Bowl' in o.name for o in scene.objects)
missing=[i.filepath for i in bpy.data.images if i.source=='FILE' and not i.packed_file and not Path(bpy.path.abspath(i.filepath)).exists()];assert not missing,missing
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(out/'arena-v3-preview.blend'));bpy.ops.render.render(write_still=True)
cam.location=(0,-1.8,4.4);cam.rotation_euler=(Vector((0,6.4,3.65))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=42;scene.render.filepath=str(out/'arena-v3-final-scoreboard.png');bpy.ops.render.render(write_still=True)
report={'status':'PASS','scope':'environment refinement and scoreboard only','bowl_added':False,'pit_radius_m':2.5,'score_objects':{n:bpy.data.objects[n].data.body for n in ['TXT_ScoreP1','TXT_ScoreP2','TXT_ScoreP1_Name','TXT_ScoreP2_Name','TXT_ScoreTarget']},'scoreboard_location':[0,6.4,3.65],'scoreboard_game_sync':'pending user approval and later integration','missing_images':missing,'alternate_wall_panels':count,'blender_version':bpy.app.version_string,'preview_camera_saved':'wide','geometry_triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in scene.objects if o.type=='MESH')}
(out/'QA_V3.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
