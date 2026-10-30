import bpy,math,json
from pathlib import Path
from mathutils import Vector
out=Path(r'C:/Users/Administrator/Desktop/ai陀螺游戏/bey-art-refs/stadium-codex-v3')
bpy.ops.wm.open_mainfile(filepath=str(out/'arena-v3-preview.blend'));scene=bpy.context.scene
report={'scope':'arena environment and 3D scoreboard only; no battle bowl','volumes':[]}
for tree in [scene.world.node_tree]+[m.node_tree for m in bpy.data.materials if m.use_nodes]:
 for n in tree.nodes:
  if n.type in {'VOLUME_SCATTER','VOLUME_ABSORPTION','PRINCIPLED_VOLUME'}:
   report['volumes'].append({'name':n.name,'density':n.inputs['Density'].default_value})
   if n.inputs['Density'].is_linked:
    for link in list(n.inputs['Density'].links):tree.links.remove(link)
   n.inputs['Density'].default_value=.0015
# Deepen painted panels, keep physical roughness and normal textures.
for name,color in {'MAT_Wall_Panel':(.018,.035,.067),'MAT_Seat_Navy':(.018,.032,.055),'MAT_Banner_Fabric':(.012,.025,.06),'MAT_Metal_Structure':(.045,.063,.09),'MAT_Floor_Concrete':(.17,.20,.24)}.items():
 p=next(n for n in bpy.data.materials[name].node_tree.nodes if n.type=='BSDF_PRINCIPLED');socket=p.inputs['Base Color']
 for link in list(socket.links):bpy.data.materials[name].node_tree.links.remove(link)
 socket.default_value=(*color,1)
 p.inputs['Metallic'].default_value=.25 if 'Metal' not in name else .65
for name in ['MAT_Screen_Emissive']:
 p=next(n for n in bpy.data.materials[name].node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(.008,.025,.065,1);p.inputs['Emission Color'].default_value=(.02,.12,.28,1);p.inputs['Emission Strength'].default_value=.8
# Distinct materials keep LED surfaces separate from metal framing.
def mat(name,color,metal=.0,rough=.5,emission=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if emission:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
 return m
navy=mat('MAT_Scoreboard_Navy',(.012,.025,.05),.35,.4);gold=mat('MAT_Scoreboard_Gold',(.55,.31,.07),.75,.3);black=mat('MAT_Scoreboard_LED',(.003,.008,.018),.1,.5);white=mat('MAT_Scoreboard_WhiteLED',(.65,.83,1),emission=2);orange=mat('MAT_Scoreboard_P1',(.95,.21,.04),emission=1.5);cyan=mat('MAT_Scoreboard_P2',(.08,.62,1),emission=1.5)
coll=bpy.data.collections.new('COL_Scoreboard');scene.collection.children.link(coll)
def move(ob):
 for c in list(ob.users_collection):c.objects.unlink(ob)
 coll.objects.link(ob)
def box(name,loc,size,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);b=o.modifiers.new('Edge chamfer','BEVEL');b.width=.04;b.segments=3;move(o);return o
Y=9.0;Z=3.1
box('SM_Scoreboard_Housing',(0,Y,Z),(6.0,.32,1.5),navy)
box('SM_Scoreboard_Display',(0,Y-.18,Z),(5.7,.045,1.26),black)
for x in [-2.95,2.95]:box('SM_Scoreboard_SideTrim',(x,Y-.2,Z),(.055,.07,1.44),gold)
for z in [Z-.72,Z+.72]:box('SM_Scoreboard_HorizontalTrim',(0,Y-.2,z),(5.94,.07,.055),gold)
for x in [-2.3,2.3]:box('SM_Scoreboard_Mount',(x,Y+.2,Z+.8),(.14,.4,.5),navy)
font=bpy.data.fonts.load('C:/Windows/Fonts/msyhbd.ttc')
def text(name,body,x,z,size,material):
 cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.align_x='CENTER';cu.align_y='CENTER';cu.size=size;cu.extrude=.002;cu.font=font
 o=bpy.data.objects.new(name,cu);coll.objects.link(o);o.location=(x,Y-.22,z);o.rotation_euler=(math.pi/2,0,0);o.data.materials.append(material);return o
text('TXT_ScoreP1_Name','P1',-2.0,Z+.1,.42,orange);text('TXT_ScoreP2_Name','P2',2.0,Z+.1,.42,cyan)
text('TXT_ScoreP1','0',-.65,Z-.06,.9,white);text('TXT_ScoreP2','0',.65,Z-.06,.9,white);text('TXT_ScoreSeparator',':',0,Z-.06,.6,gold)
text('TXT_ScoreTarget','抢 8 分',0,Z+.48,.2,gold)
# Floor and architecture get separate pools of light instead of a washed-out world.
for n in scene.world.node_tree.nodes:
 if n.type=='BACKGROUND':n.inputs['Strength'].default_value=.035
for ob in scene.objects:
 if ob.type=='LIGHT' and ob.data.type=='AREA' and 'Overhead_Big' in ob.name:ob.data.energy=1600;ob.data.size=7
cam=scene.camera;cam.location=(0,-10.8,5.7);target=Vector((0,1.1,1.6));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=25
scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.2
scene.cycles.samples=32;scene.render.resolution_x=1600;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.filepath=str(out/'arena-v3-scoreboard-wide.png')
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(out/'arena-v3-preview.blend'))
(out/'计分牌与二轮调整.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.render.render(write_still=True)
# A second, closer view makes the editable scoreboard legible.
cam.location=(0,-.4,3.8);target=Vector((0,9,3.2));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=46
scene.render.filepath=str(out/'arena-v3-scoreboard-close.png');bpy.ops.render.render(write_still=True)

