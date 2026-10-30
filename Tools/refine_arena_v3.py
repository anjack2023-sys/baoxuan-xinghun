import bpy,math,json
from pathlib import Path
from mathutils import Vector
src=Path(r'C:/Users/Administrator/Desktop/ai陀螺游戏/bey-art-refs/stadium-doubao/bey-arena-environment-v2.blend')
out=src.parent.parent/'stadium-codex-v3';bpy.ops.wm.open_mainfile(filepath=str(src));scene=bpy.context.scene
report={'source':str(src),'iterations':[],'baseline_objects':len(scene.objects)}
# Keep the existing material texture graph; tint its base rather than discarding its maps.
palette={'MAT_Banner_Fabric':(.018,.035,.065),'MAT_Floor_Concrete':(.19,.22,.26),'MAT_Metal_Structure':(.055,.075,.105),'MAT_Pit_Recess':(.012,.018,.025),'MAT_Seat_Navy':(.025,.045,.075),'MAT_Trim_Gold':(.55,.32,.09),'MAT_Wall_Panel':(.024,.047,.08),'MAT_Emblem_Gold':(.55,.32,.09),'MAT_Truss_Dark':(.026,.038,.055)}
for name,color in palette.items():
 mat=bpy.data.materials.get(name)
 if not mat:continue
 p=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');socket=p.inputs['Base Color']
 if socket.is_linked:
  link=socket.links[0];old=link.from_socket;mat.node_tree.links.remove(link)
  tint=mat.node_tree.nodes.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1;tint.inputs[2].default_value=(*[min(v*1.5,1) for v in color],1)
  mat.node_tree.links.new(old,tint.inputs[1]);mat.node_tree.links.new(tint.outputs[0],socket)
 else:socket.default_value=(*color,1)
 if 'Gold' in name:p.inputs['Metallic'].default_value=.7;p.inputs['Emission Strength'].default_value=.06
 if name=='MAT_Floor_Concrete':p.inputs['Roughness'].default_value=.6
for name,strength in [('MAT_Emissive_Cyan',2.2),('MAT_Screen_Emissive',.7),('MAT_Screen_Text_Emissive',3.5),('MAT_Spot_Lens',6)]:
 mat=bpy.data.materials.get(name)
 if mat:
  p=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Emission Strength'].default_value=strength
# Modest bevels retain shared seat meshes and make edges catch the light.
for ob in scene.objects:
 if ob.type=='MESH' and any(k in ob.name for k in ['Seat_','Barrier_Panel_','Banner','Screen_Frame','Wall_Panel']):
  bevel=ob.modifiers.new('V3_EdgeHighlights','BEVEL');bevel.width=.018;bevel.segments=2;bevel.limit_method='ANGLE'
# The foreground entrance is a deliberate open aisle, not a camera hidden behind seats.
removed=[]
for ob in list(scene.objects):
 if ob.type=='MESH' and 'Seat_' in ob.name:
  pos=ob.matrix_world.translation
  if pos.y < -4.7 and abs(pos.x)<2.2:removed.append(ob.name);bpy.data.objects.remove(ob,do_unlink=True)
report['entrance_seats_removed']=removed
# Add layered screen framing, using existing shared trim materials.
def cube(name,loc,size,mat):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);ob=bpy.context.object;ob.name=name;ob.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);ob.data.materials.append(bpy.data.materials[mat]);b=ob.modifiers.new('Soft manufactured edge','BEVEL');b.width=.035;b.segments=3;return ob
# Audit the screen location before placing decorative frames.
report['screen_objects']=[{'name':o.name,'location':list(o.location),'dimensions':list(o.dimensions)} for o in scene.objects if 'Screen' in o.name]
# Reduce scattering haze while preserving visible narrow spot shafts.
for n in scene.world.node_tree.nodes:
 if n.type=='VOLUME_SCATTER':n.inputs['Density'].default_value=.0035;n.inputs['Anisotropy'].default_value=.45
 if n.type=='BACKGROUND':n.inputs['Strength'].default_value=.06
for ob in scene.objects:
 if ob.type=='LIGHT':
  if ob.data.type=='SPOT':ob.data.energy*=1.6;ob.data.spot_blend=.28
  if 'Overhead_Big' in ob.name:ob.data.energy=700
  if 'Wall_Wash' in ob.name:ob.data.energy=280
  if 'Truss_Rim' in ob.name:ob.data.energy=180
# Camera at the aisle, aimed across the central platform.
cam=scene.camera;cam.location=(0,-8.4,4.0);target=Vector((0,.8,1.6));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=26;cam.data.clip_start=.08
scene.view_settings.exposure=.55;scene.view_settings.view_transform='AgX'
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(out/'arena-v3-preview-pass1.png')
# Package source textures so the review file is portable.
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(out/'arena-v3-preview.blend'))
(out/'制作记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.render.render(write_still=True)
