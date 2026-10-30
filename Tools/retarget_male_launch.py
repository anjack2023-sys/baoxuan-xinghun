"""Apply the approved red-cord blocking to the existing textured male rig."""
import json
import math
from pathlib import Path
import bpy
from mathutils import Matrix, Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'art/male-launch-review-v2'
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/launch-review-v2/launch-redcord-v2.blend'))
scene=bpy.context.scene
reference=bpy.data.objects['LaunchReviewRig']
samples=[]
for frame in range(1,145):
    scene.frame_set(frame)
    samples.append({bone.name:bone.matrix.copy() for bone in reference.pose.bones})
mannequin=[obj for obj in scene.objects if obj==reference or any(m.type=='ARMATURE' and m.object==reference for m in obj.modifiers)]
for obj in mannequin:
    bpy.data.objects.remove(obj,do_unlink=True)
for name in ('Launcher','PullHandle','RedGripRing','Ripcord','RipcordTip','InsertionPort'):
    bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
old=set(bpy.data.objects)
source=next((ROOT/'Saved/FeelRef60/work/LabSources/TripoMaleLauncher-v1').glob('*.fbx'))
bpy.ops.import_scene.fbx(filepath=str(source),use_anim=False)
scene.render.fps=30
added=set(bpy.data.objects)-old
rig=next(o for o in added if o.type=='ARMATURE')
rig.name='MaleLaunchRig'
rig.animation_data_clear()
for pb in rig.pose.bones: pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
hip_world=rig.matrix_world@rig.data.bones['Hip'].head_local
rotation=Matrix.Rotation(-math.pi/2,4,'Z')
normal=rotation@Matrix.Scale(1.85,4)
center=normal@hip_world
normal=Matrix.Translation(Vector((-center.x,-center.y,0)))@normal
for obj in added:
    if obj.type=='MESH':
        transform=normal@obj.matrix_world
        obj.data.transform(transform)
        obj.matrix_parent_inverse=Matrix.Identity(4)
        obj.matrix_basis=Matrix.Identity(4)
rig.data.transform(normal@rig.matrix_world)
rig.matrix_world=Matrix.Identity(4)
rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
heads={b.name:b.head_local.copy() for b in rig.data.bones}
rest_hip=heads['Hip']
red_axis=(normal@Vector((.026,.262,.346)))-heads['L_Hand']
checks=[]
# Socket calibrated to the user's marked launcher underside in frame 73.
socket_local=Vector((-.0692741275,.1273543239,.0841545612))
socket_frames=[]

def set_bone(name,world):
    pb=rig.pose.bones[name]
    pb.rotation_mode='QUATERNION'
    pb.matrix=world
    bpy.context.view_layer.update()

def aimed(name,start,end,rest_end):
    q=(rest_end-heads[name]).rotation_difference(end-start)
    m=q.to_matrix().to_4x4()@rest[name]
    m.translation=start
    return m

def solve(a,b,pole,upper,lower):
    delta=b-a
    distance=min(delta.length,(upper+lower)*.985)
    b=a+delta.normalized()*distance
    axis=(b-a).normalized()
    bend=Vector(pole)-a
    bend=(bend-axis*bend.dot(axis)).normalized()
    along=(upper*upper-lower*lower+distance*distance)/(2*distance)
    return a+axis*along+bend*math.sqrt(max(0,upper*upper-along*along)),b

for frame,ref in enumerate(samples,1):
    scene.frame_set(frame)
    hip=ref['Pelvis'].translation+Vector((0,0,-.07))
    chest=ref['Neck'].translation
    torso_q=Vector((0,0,1)).rotation_difference(chest-hip)
    torso=torso_q.to_matrix().to_4x4()
    for bone in rig.data.bones:
        if any(part in bone.name for part in ('Thigh','Calf','Foot','Toe','Upperarm','Forearm','Hand')):continue
        m=torso@rest[bone.name]
        m.translation=hip+torso_q@(heads[bone.name]-rest_hip)
        if bone.name=='Root':m=rest[bone.name].copy()
        set_bone(bone.name,m)
    actual_hands={}
    # This FBX labels the hand carrying the red cord L_Hand; preserve its skin weights.
    for source_side,target_side in [('L','R'),('R','L')]:
        upper,fore,hand=[source_side+'_'+s for s in ('Upperarm','Forearm','Hand')]
        shoulder=hip+torso_q@(heads[upper]-rest_hip)
        desired=ref[target_side+'_Hand'].translation.copy()
        # Keep the approved hand path in front of the narrower character chest.
        shoulder.y-=.10
        elbow,wrist=solve(shoulder,desired,((-1 if target_side=='L' else 1)*.65,.10,1.05),
                         (heads[fore]-heads[upper]).length,(heads[hand]-heads[fore]).length)
        arm_m=aimed(upper,shoulder,elbow,heads[fore])
        fore_m=aimed(fore,elbow,wrist,heads[hand])
        set_bone(upper,arm_m)
        set_bone(fore,fore_m)
        hand_m=fore_m@rest[fore].inverted()@rest[hand]
        hand_m.translation=wrist
        if target_side=='R':
            left_target=ref['L_Hand'].translation+Vector((.06,-.025,-.015))
            direction=(left_target-wrist).normalized()
            if frame<=22:
                t=max(0,min(1,(frame-12)/10));t=t*t*(3-2*t)
                direction=Vector((0,0,-1)).lerp(direction,t).normalized()
            elif frame>102:
                t=max(0,min(1,(frame-102)/35));t=t*t*(3-2*t)
                direction=direction.lerp(Vector((0,0,-1)),t).normalized()
            q=red_axis.rotation_difference(direction)
            hand_m=q.to_matrix().to_4x4()@rest[hand]
            hand_m.translation=wrist
        set_bone(hand,hand_m)
        actual_hands[target_side]=wrist.copy()
        # Twist helpers follow their segment transform rather than retaining the import pose.
        for segment,segment_m in [(upper,arm_m),(fore,fore_m)]:
            delta=segment_m@rest[segment].inverted()
            for name in rest:
                if name.startswith(segment+'Twist'):set_bone(name,delta@rest[name])
        thigh,calf,foot=[source_side+'_'+s for s in ('Thigh','Calf','Foot')]
        start=hip+torso_q@(heads[thigh]-rest_hip)
        ankle=ref[target_side+'_Foot'].translation.copy()
        ankle.z=heads[foot].z
        knee,ankle=solve(start,ankle,((-.2 if target_side=='L' else .2),-1,.55),
                         (heads[calf]-heads[thigh]).length,(heads[foot]-heads[calf]).length)
        thigh_m=aimed(thigh,start,knee,heads[calf]);calf_m=aimed(calf,knee,ankle,heads[foot])
        set_bone(thigh,thigh_m);set_bone(calf,calf_m)
        foot_m=rest[foot].copy();foot_m.translation=ankle;set_bone(foot,foot_m)
        for segment,segment_m in [(thigh,thigh_m),(calf,calf_m)]:
            delta=segment_m@rest[segment].inverted()
            for name in rest:
                if name.startswith(segment+'Twist'):set_bone(name,delta@rest[name])
        toe=source_side+'_ToeBase'
        set_bone(toe,foot_m@rest[foot].inverted()@rest[toe])
        assert (ankle-ref[target_side+'_Foot'].translation).xy.length<1e-5
        assert abs((wrist-elbow).length-(heads[hand]-heads[fore]).length)<1e-5
    for pb in rig.pose.bones:
        for prop in ('location','rotation_quaternion','scale'):pb.keyframe_insert(data_path=prop,frame=frame)
    bey=bpy.data.objects['Bey']
    grip=rig.pose.bones['R_Hand'].matrix
    if frame<=87:
        bey.location=grip@socket_local
        assert (grip.inverted()@bey.location-socket_local).length<1e-5
        release_origin=bey.location.copy()
    else:
        height=release_origin.z-.05
        t=min((frame-87)/30,(-1+math.sqrt(1+8*height))/4)
        bey.location=release_origin+Vector((0,-.95*t,-min(height,t+2*t*t)))
    bey.keyframe_insert(data_path='location',frame=frame)
    socket_frames.append(list(bey.location))
    checks.append({name:list(rig.pose.bones[name].matrix.translation) for name in ('L_Hand','R_Hand','L_Foot','R_Foot')})

rig.animation_data.action.name='Male_RedCordLaunch_30fps'
texture=bpy.data.images.load(str(next(source.with_suffix('.fbm').glob('Color.jpg'))),check_existing=True)
for obj in added:
    if obj.type!='MESH':continue
    obj.name='MaleLeadMesh'
    for mat in obj.data.materials:
        mat.use_nodes=True
        nodes=mat.node_tree.nodes;links=mat.node_tree.links
        nodes.clear()
        output=nodes.new('ShaderNodeOutputMaterial')
        shader=nodes.new('ShaderNodeBsdfPrincipled')
        shader.inputs['Roughness'].default_value=.78
        tex=nodes.new('ShaderNodeTexImage');tex.image=texture
        links.new(tex.outputs['Color'],shader.inputs['Base Color'])
        links.new(shader.outputs['BSDF'],output.inputs['Surface'])
        nodes.active=tex
texture.pack()
scene.display.shading.color_type='TEXTURE'
scene.display.shading.show_cavity=False
scene.view_settings.view_transform='Standard'
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'male-redcord-launch.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'male-redcord-launch.glb'),export_format='GLB',export_animation_mode='SCENE',export_anim_scene_split_object=False)
bpy.ops.export_scene.fbx(filepath=str(OUT/'male-redcord-launch.fbx'),object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim_use_all_actions=False,bake_anim_simplify_factor=0)
for frame in range(1,145,2):
    scene.frame_set(frame)
    scene.render.filepath=str(OUT/f'frame-{frame:03}.png')
    bpy.ops.render.render(write_still=True)
(OUT/'checks.json').write_text(json.dumps({'status':'PASS','frames':144,'fps':30,'release_frame':88,'source':str(source),'checks':['constant forearm lengths','fixed ankle XY','existing textured mesh and built-in props retained'],'samples':checks},indent=2))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(OUT/'male-redcord-launch.glb'))
armatures=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
assert len(armatures)==1
imported=armatures[0]
for frame in (1,18,35,48,79,87,89,103,143):
    bpy.context.scene.frame_set(frame)
    for name,expected in checks[frame-1].items():
        actual=imported.matrix_world@imported.pose.bones[name].head
        assert (actual-Vector(expected)).length<.001,(frame,name,list(actual),expected,(actual-Vector(expected)).length)
    assert (bpy.data.objects['Bey'].matrix_world.translation-Vector(socket_frames[frame-1])).length<.001,(frame,'Bey')
(OUT/'export-check.json').write_text(json.dumps({'status':'PASS','file':'male-redcord-launch.glb','frames_checked':[1,18,35,48,79,87,89,103,143],'hand_and_foot_position_tolerance_m':.001,'armature_count':1},indent=2))
