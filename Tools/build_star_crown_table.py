import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector
out=Path(r'C:/Users/Administrator/Desktop/ai陀螺游戏/bey-art-refs/star-crown-battle-table');src=out.parent/'stadium-codex-v4/arena-v4-preview.blend'
bpy.ops.wm.open_mainfile(filepath=str(src));s=bpy.context.scene
coll=bpy.data.collections.new('COL_StarCrownTable');s.collection.children.link(coll)
def material(name,color,metal,rough,emission=0,glass=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if emission:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
 if glass:p.inputs['Transmission Weight'].default_value=1.;p.inputs['IOR'].default_value=1.12;p.inputs['Roughness'].default_value=.08;p.inputs['Alpha'].default_value=.18
 return m
navy=material('MAT_Table_Navy',(.018,.035,.065),.45,.32);gold=material('MAT_Table_Gold',(.58,.35,.105),.78,.26);silver=material('MAT_Table_Silver',(.46,.52,.59),.55,.32);cyan=material('MAT_Table_Cyan',(.035,.55,.8),.2,.25,4);glass=material('MAT_Table_Glass',(.7,.87,.94),0,.12,glass=True);dark=material('MAT_Table_Recess',(.012,.02,.032),.3,.6)
def lathe(name,profile,mat,segments=160,start=0,end=math.tau,closed=False):
 n=len(profile);ring_count=segments if closed else segments+1;verts=[];faces=[]
 for i in range(ring_count):
  a=start+(end-start)*i/segments
  for r,z in profile:verts.append((r*math.cos(a),r*math.sin(a),z))
 for i in range(segments):
  j=(i+1)%ring_count
  for k in range(n-1):faces.append((i*n+k,j*n+k,j*n+k+1,i*n+k+1))
 if not closed:
  faces.extend([tuple(reversed([k for k in range(n)])),tuple(segments*n+k for k in range(n))])
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],[tuple(reversed(f)) for f in faces]);me.update();
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=.000001);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);
 if name=='SM_StarCrown_PlaySurface' and sum(f.normal.z for f in bm.faces)<0:bmesh.ops.reverse_faces(bm,faces=bm.faces)
 bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);coll.objects.link(o);me.materials.append(mat)
 for p in me.polygons:p.use_smooth=True
 return o
# The playing surface is one smooth bowl, with no raised star geometry.
profile=[(0,.42)]+[(1.6*i/40,.42+.28*(i/40)**2) for i in range(1,41)]
lathe('SM_StarCrown_PlaySurface',profile,silver,closed=True)
lathe('SM_StarCrown_HousingBase',[(1.6,.14),(1.84,.14),(1.84,.65),(1.6,.65),(1.6,.14)],navy,closed=True)
for i in range(4):
 center=i*math.pi/2;half=math.radians(27)
 lathe('SM_StarCrown_HighWall_'+str(i),[(1.6,.65),(1.6,.94),(1.79,.94),(1.84,.82),(1.84,.65),(1.6,.65)],navy,segments=48,start=center-half,end=center+half)
 lathe('SM_StarCrown_HighTrim_'+str(i),[(1.61,.94),(1.79,.94),(1.79,.953),(1.61,.953),(1.61,.94)],gold,segments=48,start=center-half,end=center+half)
 center+=math.pi/4;half=math.radians(18)
 lathe('SM_StarCrown_LowWall_'+str(i),[(1.6,.65),(1.6,.88),(1.84,.88),(1.84,.65),(1.6,.65)],navy,segments=32,start=center-half,end=center+half)
 lathe('SM_StarCrown_LowLip_'+str(i),[(1.6,.88),(1.84,.88),(1.84,.892),(1.6,.892),(1.6,.88)],silver,segments=32,start=center-half,end=center+half)
for name,r,z,width,height,mat in [('LowerLED',1.835,.255,.012,.032,cyan),('LowerGold',1.827,.31,.014,.018,gold)]:
 lathe('SM_StarCrown_'+name,[(r-width,z-height),(r+width,z-height),(r+width,z+height),(r-width,z+height),(r-width,z-height)],mat,closed=True)
for i,(a,b) in enumerate([(math.radians(63),math.radians(117)),(math.radians(243),math.radians(297))]):
 lathe('SM_StarCrown_ClearShield_'+str(i),[(1.715,.94),(1.735,.94),(1.735,1.13),(1.715,1.13),(1.715,.94)],glass,segments=36,start=a,end=b)
 for angle in [a,b]:
  bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=.027,depth=.225,location=(1.725*math.cos(angle),1.725*math.sin(angle),1.035));o=bpy.context.object;o.name='SM_StarCrown_ShieldPost';o.data.materials.append(gold)
  for c in list(o.users_collection):c.objects.unlink(o)
  coll.objects.link(o)
# A flush painted star stays outside the physics surface height sampling.
verts=[(0,0,.421)];faces=[]
for i in range(16):
 a=i*math.tau/16;r=.29 if i%2==0 else .105;verts.append((r*math.cos(a),r*math.sin(a),.421+.28*(r/1.6)**2))
for i in range(16):faces.append((0,i+1,(i+1)%16+1))
me=bpy.data.meshes.new('StarInlay');me.from_pydata(verts,[],faces);me.materials.append(gold);o=bpy.data.objects.new('SM_StarCrown_StarInlay',me);coll.objects.link(o)
# Close the old installation opening around the new smaller unit with level flooring.
lathe('SM_StarCrown_FloorCollar',[(1.845,.10),(2.53,.10),(2.53,.025),(1.845,.025),(1.845,.10)],bpy.data.materials['MAT_Entrance_Floor'],closed=True)
# Reuse continuous surrounding floor, avoiding any unsupported human standing zones.
for sign in [-1,1]:
 for y in [-1.,1.]:
  bpy.ops.mesh.primitive_cube_add(size=1,location=(sign*2.72,y,.106));o=bpy.context.object;o.name='SM_StarCrown_LaunchMark';o.dimensions=(1.15,.018,.006);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(gold)
  for c in list(o.users_collection):c.objects.unlink(o)
  coll.objects.link(o)
# Validate center, play radius and both standing approaches before export.
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
for r in [0,.4,.8,1.2,1.55]:
 hit,loc,n,_,ob,_=s.ray_cast(deps,Vector((r,0,4)),Vector((0,0,-1)),distance=5);expected=.42+.28*(r/1.6)**2;assert hit and n.z>.8 and abs(loc.z-expected)<.004,(r,loc)
for x in [-2.6,2.6]:
 hit,loc,n,_,ob,_=s.ray_cast(deps,Vector((x,0,3)),Vector((0,0,-1)),distance=4);assert hit and abs(loc.z-.1)<.02,(x,loc)
# Convert fixed scoreboard legends; game scores use small reusable digit meshes.
for name in ['TXT_ScoreP1_Name','TXT_ScoreP2_Name','TXT_ScoreSeparator','TXT_ScoreTarget']:
 o=bpy.data.objects.get(name)
 if o:
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
for group,names in [('SM_StarCrown_Arena80',list(coll.objects)),('SM_ApprovedArena',[o for o in s.objects if o.type=='MESH' and o.name not in coll.objects])]:
 bpy.ops.object.select_all(action='DESELECT')
 for o in names:o.select_set(True)
 bpy.ops.export_scene.fbx(filepath=str(out/(group+'.fbx')),use_selection=True,object_types={'MESH'},apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',add_leaf_bones=False,use_mesh_modifiers=True,path_mode='ABSOLUTE')
for value in range(11):
 cu=bpy.data.curves.new('ScoreDigit','FONT');cu.body=str(value);cu.align_x='CENTER';cu.align_y='CENTER';cu.size=.9;cu.extrude=.002
 o=bpy.data.objects.new('SM_Score_'+str(value),cu);s.collection.objects.link(o);o.rotation_euler=(math.pi/2,0,0);o.data.materials.append(bpy.data.materials['MAT_Scoreboard_WhiteLED']);bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
 bpy.ops.export_scene.fbx(filepath=str(out/('SM_Score_'+str(value)+'.fbx')),use_selection=True,object_types={'MESH'},apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',add_leaf_bones=False,path_mode='ABSOLUTE')
 bpy.data.objects.remove(o,do_unlink=True)
meta={}
for m in bpy.data.materials:
 if not m.use_nodes:continue
 p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 if not p:continue
 meta[m.name]={'base':list(p.inputs['Base Color'].default_value),'base_linked':p.inputs['Base Color'].is_linked,'metal':p.inputs['Metallic'].default_value,'rough':p.inputs['Roughness'].default_value,'emission':list(p.inputs['Emission Color'].default_value),'strength':p.inputs['Emission Strength'].default_value,'glass':'Glass' in m.name,'images':[bpy.path.abspath(n.image.filepath) for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]}
(out/'materials.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
(out/'geometry-qa.json').write_text(json.dumps({'status':'PASS','center_z_m':.42,'play_radius_m':1.6,'outer_radius_m':1.84,'standing_x_m':[-2.6,2.6],'low_wall_count':4,'low_wall_height_m':.18,'gap_half_angle_degrees':18,'table_triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in coll.objects),'scoreboard_numeric_objects_excluded_from_fbx':True},indent=2))
bpy.ops.file.pack_all();s.render.filepath=str(out/'star-crown-arena-preview.png');s.cycles.samples=24;bpy.ops.wm.save_as_mainfile(filepath=str(out/'star-crown-arena.blend'));bpy.ops.render.render(write_still=True)
