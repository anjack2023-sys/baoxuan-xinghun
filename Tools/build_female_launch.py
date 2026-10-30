"""Rig the supplied unskinned female and reuse the approved launch timing."""
import json,math
from pathlib import Path
import bpy
from mathutils import Matrix,Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'art/female-launch-v1';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT/'female-source.blend'))
scene=bpy.context.scene
mesh=next(o for o in scene.objects if o.type=='MESH');mesh.name='FemaleLeadMesh'
bones={
 'Root':((0,0,0),(0,0,.08),None),
 'Hip':((0,0,.88),(0,0,.92),'Root'),
 'Pelvis':((0,0,.88),(0,0,.98),'Hip'),
 'Waist':((0,0,.88),(0,0,1.0),'Hip'),
 'Spine01':((0,0,1.0),(0,0,1.15),'Waist'),
 'Spine02':((0,0,1.15),(0,0,1.28),'Spine01'),
 'Neck':((0,0,1.28),(0,0,1.36),'Spine02'),
 'Head':((0,0,1.36),(0,0,1.56),'Neck'),
 'R_Clavicle':((0,-.03,1.26),(-.02,-.145,1.28),'Spine02'),
 'R_Upperarm':((-.02,-.145,1.28),(.116,-.321,1.114),'R_Clavicle'),
 'R_Forearm':((.116,-.321,1.114),(.315,-.35,1.038),'R_Upperarm'),
 'R_Hand':((.315,-.35,1.038),(.365,-.35,1.018),'R_Forearm'),
 'L_Clavicle':((0,.03,1.26),(-.015,.145,1.28),'Spine02'),
 'L_Upperarm':((-.015,.145,1.28),(-.14,.235,1.02),'L_Clavicle'),
 'L_Forearm':((-.14,.235,1.02),(-.165,.32,.855),'L_Upperarm'),
 'L_Hand':((-.165,.32,.855),(-.15,.33,.805),'L_Forearm'),
}
for side,sign in [('L',1),('R',-1)]:
    bones.update({side+'_Thigh':((-.02,sign*.10,.87),(0,sign*.20,.47),'Pelvis'),
                  side+'_Calf':((0,sign*.20,.47),(-.02,sign*.30,.10),side+'_Thigh'),
                  side+'_Foot':((-.02,sign*.30,.10),(.12,sign*.30,.055),side+'_Calf'),
                  side+'_ToeBase':((.12,sign*.30,.055),(.20,sign*.30,.045),side+'_Foot')})
data=bpy.data.armatures.new('FemaleSkeleton');rig=bpy.data.objects.new('FemaleLaunchRig',data);scene.collection.objects.link(rig)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
for name,(a,b,parent) in bones.items():
    bone=data.edit_bones.new(name);bone.head=a;bone.tail=b
for name,(a,b,parent) in bones.items():
    if parent:data.edit_bones[name].parent=data.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
mesh.parent=rig
modifier=mesh.modifiers.new('FemaleSkeleton','ARMATURE');modifier.object=rig
for name in bones:mesh.vertex_groups.new(name=name)
assert any(m.type=='ARMATURE' and m.object==rig for m in mesh.modifiers)

def rigid(vertex,name):
    for group in mesh.vertex_groups:group.remove([vertex.index])
    mesh.vertex_groups[name].add([vertex.index],1,'REPLACE')

def distance_segment(point,a,b):
    axis=b-a;t=max(0,min(1,(point-a).dot(axis)/axis.length_squared))
    return (point-(a+axis*t)).length

cord_start=Vector(bones['L_Hand'][0]);cord_tip=Vector((.13,.40,.612))
color_image=next(n.image for mat in mesh.data.materials for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and any(link.to_socket.name=='Base Color' for link in n.outputs['Color'].links))
pixels=list(color_image.pixels);width,height=color_image.size
vertex_colors={}
for loop in mesh.data.loops:
    uv=mesh.data.uv_layers.active.data[loop.index].uv
    offset=(min(height-1,max(0,int(uv.y*height)))*width+min(width-1,max(0,int(uv.x*width))))*4
    vertex_colors[loop.vertex_index]=pixels[offset:offset+3]
unweighted=0
for v in mesh.data.vertices:
    co=v.co
    side='L' if co.y>0 else 'R'
    arm=[side+'_'+n for n in ('Upperarm','Forearm','Hand')]
    distances={n:distance_segment(co,Vector(bones[n][0]),Vector(bones[n][1])) for n in arm}
    r,g,b=vertex_colors[v.index]
    red=r>g*1.6 and r>b*1.3
    skin=r>g*1.08 and g>b*1.12 and r>.20
    if co.z>1.38 or (co.x<-.13 and co.z>1.31):weights={'Head':1}
    elif distance_segment(co,cord_start,cord_tip)<.035 and (red or co.z<.65):weights={'L_Hand':1}
    elif (co-cord_start).length<.08 and (co.y>.32 or skin):weights={'L_Hand':1}
    elif co.x>.24 and co.y<-.22 and .90<co.z<1.08:weights={'R_Hand':1}
    elif min(distances.values())<.145 and (abs(co.y)>.17 or co.x>.18) and (co.z>1.05 or abs(co.y)>.26 or (co.x<-.09 and abs(co.y)>.21 and co.z>.9)):
        values={n:1/(d+.025)**4 for n,d in distances.items()}
        total=sum(values.values());amount=max(0,min(1,(abs(co.y)-.15)/.09))
        weights={n:w/total*amount for n,w in values.items()};weights['Spine02']=1-amount
    elif co.z<.91:
        if co.z<.15:weights={side+'_Foot':1}
        else:
            leg=[side+'_'+n for n in ('Thigh','Calf')]
            values={n:1/(distance_segment(co,Vector(bones[n][0]),Vector(bones[n][1]))+.025)**4 for n in leg}
            total=sum(values.values());amount=max(0,min(1,(.91-co.z)/.16))
            weights={n:w/total*amount for n,w in values.items()};weights['Pelvis']=1-amount
    else:weights={'Spine02':1}
    for name,weight in weights.items():
        if weight>0:mesh.vertex_groups[name].add([v.index],weight,'REPLACE')
assert all(sum(g.weight for g in v.groups)>.99 for v in mesh.data.vertices)
normal=Matrix.Rotation(-math.pi/2,4,'Z')
mesh.data.transform(normal);rig.data.transform(normal)
rest={b.name:b.matrix_local.copy() for b in data.bones};heads={b.name:b.head_local.copy() for b in data.bones}
red_axis=normal@cord_tip-heads['L_Hand']
socket=normal@Vector((.35,-.25,.947))
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
bone=data.edit_bones.new('LaunchSocket');bone.head=socket;bone.tail=socket+Vector((0,0,.01));bone.parent=data.edit_bones['R_Hand'];bone.use_deform=False
bpy.ops.object.mode_set(mode='OBJECT')
old=set(bpy.data.objects)
with bpy.data.libraries.load(str(ROOT/'art/launch-review-v2/launch-redcord-v2.blend'),link=False) as (src,dst):dst.objects=['LaunchReviewRig']
reference=dst.objects[0];scene.collection.objects.link(reference)
scene.render.fps=30;scene.frame_start=1;scene.frame_end=144

def set_bone(name,m):
    pb=rig.pose.bones[name];pb.rotation_mode='QUATERNION';pb.matrix=m;bpy.context.view_layer.update()

def aimed(name,a,b,rest_end):
    q=(rest_end-heads[name]).rotation_difference(b-a)
    m=q.to_matrix().to_4x4()@rest[name];m.translation=a;return m

def solve(a,b,pole,u,l):
    axis=(b-a).normalized();d=min((b-a).length,(u+l)*.985);b=a+axis*d
    bend=Vector(pole)-a;bend=(bend-axis*bend.dot(axis)).normalized()
    along=(u*u-l*l+d*d)/(2*d)
    return a+axis*along+bend*math.sqrt(max(0,u*u-along*along)),b

samples=[]
for frame in range(1,145):
    scene.frame_set(frame)
    ref={b.name:b.matrix.copy() for b in reference.pose.bones}
    hip=ref['Pelvis'].translation+Vector((0,0,-.12))
    q=Vector((0,0,1)).rotation_difference(ref['Neck'].translation-ref['Pelvis'].translation)
    for name in ('Root','Hip','Pelvis','Waist','Spine01','Spine02','Neck','Head','L_Clavicle','R_Clavicle'):
        m=q.to_matrix().to_4x4()@rest[name];m.translation=hip+q@(heads[name]-heads['Hip'])
        if name=='Root':m=rest[name].copy()
        set_bone(name,m)
    for source_side,target_side in [('L','R'),('R','L')]:
        upper,fore,hand=[source_side+'_'+s for s in ('Upperarm','Forearm','Hand')]
        shoulder=hip+q@(heads[upper]-heads['Hip']);shoulder.y-=.06
        elbow,wrist=solve(shoulder,ref[target_side+'_Hand'].translation,((-.65 if target_side=='L' else .65),.1,1.05),
                         (heads[fore]-heads[upper]).length,(heads[hand]-heads[fore]).length)
        a=aimed(upper,shoulder,elbow,heads[fore]);b=aimed(fore,elbow,wrist,heads[hand]);set_bone(upper,a);set_bone(fore,b)
        m=b@rest[fore].inverted()@rest[hand];m.translation=wrist
        if target_side=='R':
            direction=(ref['L_Hand'].translation+Vector((.06,-.025,-.015))-wrist).normalized()
            if frame<=22:
                t=max(0,min(1,(frame-12)/10));t=t*t*(3-2*t);direction=Vector((0,0,-1)).lerp(direction,t).normalized()
            elif frame>102:
                t=max(0,min(1,(frame-102)/35));t=t*t*(3-2*t);direction=direction.lerp(Vector((0,0,-1)),t).normalized()
            m=red_axis.rotation_difference(direction).to_matrix().to_4x4()@rest[hand];m.translation=wrist
        set_bone(hand,m)
        thigh,calf,foot=[source_side+'_'+s for s in ('Thigh','Calf','Foot')]
        start=hip+q@(heads[thigh]-heads['Hip']);ankle=ref[target_side+'_Foot'].translation.copy();ankle.z=.10
        knee,ankle=solve(start,ankle,((-.2 if target_side=='L' else .2),-1,.55),(heads[calf]-heads[thigh]).length,(heads[foot]-heads[calf]).length)
        set_bone(thigh,aimed(thigh,start,knee,heads[calf]));set_bone(calf,aimed(calf,knee,ankle,heads[foot]))
        m=rest[foot].copy();m.translation=ankle;set_bone(foot,m)
        set_bone(source_side+'_ToeBase',m@rest[foot].inverted()@rest[source_side+'_ToeBase'])
        assert (ankle-ref[target_side+'_Foot'].translation).xy.length<1e-5
        assert abs((elbow-wrist).length-(heads[hand]-heads[fore]).length)<1e-5
    for pb in rig.pose.bones:
        if pb.name=='LaunchSocket':continue
        for prop in ('location','rotation_quaternion','scale'):pb.keyframe_insert(data_path=prop,frame=frame)
    samples.append({n:list(rig.pose.bones[n].matrix.translation) for n in ('L_Hand','R_Hand','L_Foot','R_Foot','LaunchSocket')})
bpy.data.objects.remove(reference,do_unlink=True)
rig.animation_data.action.name='Female_RedCordLaunch_30fps'
for image in bpy.data.images:
    if image.source=='FILE' and image.size[0]>0:
        image.pack()
texture=next(n.image for mat in mesh.data.materials for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and any(link.to_socket.name=='Base Color' for link in n.outputs['Color'].links))
game=Path('C:/BeybladeLaunchWork/LabSources/FemaleLaunch');game.mkdir(parents=True,exist_ok=True)
texture.filepath_raw=str(game/'FemaleColor.png');texture.file_format='PNG';texture.save()
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'female-redcord-launch.blend'))
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);mesh.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(game/'FemaleApprovedLaunch.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0)
bpy.ops.export_scene.gltf(filepath=str(OUT/'female-redcord-launch.glb'),use_selection=True,export_format='GLB',export_animation_mode='SCENE',export_anim_scene_split_object=False)
camera=scene.camera;camera.location=(3,-4.7,2.5);camera.rotation_euler=(Vector((0,-.3,.85))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=2.1
for frame in range(1,145,2):
    scene.frame_set(frame);scene.render.filepath=str(OUT/f'frame-{frame:03}.png');bpy.ops.render.render(write_still=True)
(OUT/'checks.json').write_text(json.dumps({'status':'PASS','vertices':len(mesh.data.vertices),'fallback_unweighted_vertices':unweighted,'bones':len(data.bones),'fps':30,'frames':144,'samples':samples},indent=2))
