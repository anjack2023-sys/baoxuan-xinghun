"""Standalone launch blocking; run with Blender --background --python this_file."""
import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

OUT = Path(__file__).resolve().parents[1] / 'art/launch-review-v1'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = 30
scene.frame_start, scene.frame_end = 1, 96


def blend(a, b, t):
    t = max(0, min(1, t))
    return Vector(a).lerp(Vector(b), t*t*(3-2*t))


def elbow(a, b, pole, upper, lower):
    delta = b-a
    distance = delta.length
    assert abs(upper-lower) < distance < upper+lower, (a, b, distance)
    axis = delta.normalized()
    bend = Vector(pole)-a
    bend = (bend-axis*bend.dot(axis)).normalized()
    along = (upper*upper-lower*lower+distance*distance)/(2*distance)
    return a+axis*along+bend*math.sqrt(upper*upper-along*along)


def pose(frame):
    load = max(0, min(1, (frame-16)/15))
    pull = max(0, min(1, (frame-32)/9))
    recover = max(0, min(1, (frame-54)/35))
    lean = load*(1-.65*recover)
    hip = Vector((-.025*lean, -.035*lean, .94-.045*lean))
    chest = hip+Vector((-.015*pull, -.055*lean, .48))
    left = blend((-.21,-.31,1.18),(-.20,-.47,1.08),load)
    left = blend(left,(-.20,-.34,1.16),recover)
    right = blend((-.04,-.29,1.19),(-.035,-.47,1.08),load)
    right = blend(right,(.49,-.23,1.25),pull)
    right = blend(right,(.20,-.21,1.12),recover)
    joints = {'Hip': (Vector((0,0,0)),hip), 'Pelvis':(hip,hip+Vector((0,0,.12))),
              'Spine01':(hip,chest), 'Neck':(chest,chest+Vector((0,0,.10))),
              'Head':(chest+Vector((0,0,.10)),chest+Vector((0,-.01,.31)))}
    for side, sign, hand in [('L',-1,left),('R',1,right)]:
        shoulder = chest+Vector((sign*.19, .015*pull*sign, 0))
        arm_joint = elbow(shoulder,hand,(sign*.65,.10,1.05),.30,.29)
        thigh = hip+Vector((sign*.105,0,0))
        foot = Vector((sign*.18,-.22 if sign<0 else .18,.07))
        knee = elbow(thigh,foot,(sign*.20,-1,.55),.45,.46)
        joints.update({side+'_Clavicle':(chest,shoulder),side+'_Upperarm':(shoulder,arm_joint), side+'_Forearm':(arm_joint,hand),
                       side+'_Hand':(hand,hand+Vector((0,-.09,0))),
                       side+'_Thigh':(thigh,knee),side+'_Calf':(knee,foot),
                       side+'_Foot':(foot,foot+Vector((0,-.18,0)))})
    return joints, left, right


def matrix(a,b):
    return Matrix.Translation(a) @ (b-a).to_track_quat('Y','Z').to_matrix().to_4x4()


rest, _, _ = pose(1)
arm_data = bpy.data.armatures.new('LaunchReviewSkeleton')
rig = bpy.data.objects.new('LaunchReviewRig',arm_data)
scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for name,(a,b) in rest.items():
    bone = arm_data.edit_bones.new(name)
    bone.head, bone.tail = a,b
for name in rest:
    if name == 'Hip': continue
    parent = ('Hip' if name in ('Pelvis','Spine01') or 'Thigh' in name else
              'Neck' if name=='Head' else
              'Spine01' if name=='Neck' or 'Clavicle' in name else
              name.replace('Upperarm','Clavicle') if 'Upperarm' in name else
              name.replace('Forearm','Upperarm').replace('Hand','Forearm').replace('Calf','Thigh').replace('Foot','Calf'))
    arm_data.edit_bones[name].parent = arm_data.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
rig.select_set(False)


def sphere(name, location, scale, color):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=location)
    obj=bpy.context.object
    obj.name=name
    obj.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.color=(*color,1)
    for face in obj.data.polygons: face.use_smooth=True
    return obj


def skin(obj,bone):
    obj.parent=rig
    group=obj.vertex_groups.new(name=bone)
    group.add(list(range(len(obj.data.vertices))),1,'REPLACE')
    modifier=obj.modifiers.new('Skeleton','ARMATURE')
    modifier.object=rig


blue=(.045,.30,.72)
for name,(a,b) in rest.items():
    if name in ('Hip','Pelvis'): continue
    radius=.065 if 'Thigh' in name else .048
    if name=='Spine01': radius=.17
    obj=sphere(name+'Mesh',(a+b)/2,(radius,(b-a).length/2,radius),blue if name.startswith('L_') else (.82,.88,.94))
    obj.rotation_mode='QUATERNION'
    obj.rotation_quaternion=(b-a).to_track_quat('Y','Z')
    skin(obj,name)
    joint=sphere(name+'Joint',a,(radius*.9,)*3,(.12,.16,.23))
    skin(joint,name)
head=sphere('HeadShell',rest['Head'][0]+Vector((0,0,.13)),(.105,.095,.135),(.96,.72,.47))
skin(head,'Head')

def box(name,location,scale,color):
    bpy.ops.mesh.primitive_cube_add(size=1,location=location)
    obj=bpy.context.object
    obj.name=name
    obj.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.color=(*color,1)
    bevel=obj.modifiers.new('Soft edges','BEVEL');bevel.width=.015;bevel.segments=2
    obj.modifiers.new('Normals','WEIGHTED_NORMAL')
    return obj

launcher=box('Launcher', (0,0,0),(.18,.12,.075),(.98,.32,.06))
handle=box('PullHandle',(0,0,0),(.035,.13,.035),(.98,.65,.06))
bpy.ops.mesh.primitive_cone_add(vertices=32,radius1=.025,radius2=.075,depth=.075)
top=bpy.context.object;top.name='Bey';top.color=(.92,.12,.055,1)
cord=box('Ripcord',(0,0,0),(1,.009,.009),(.98,.77,.12))
records=[]
for frame in range(1,97):
    scene.frame_set(frame)
    joints,left,right=pose(frame)
    for name,(a,b) in joints.items():
        pb=rig.pose.bones[name]
        pb.rotation_mode='QUATERNION'
        pb.matrix=matrix(a,b)
        bpy.context.view_layer.update()
        for prop in ('location','rotation_quaternion','scale'): pb.keyframe_insert(data_path=prop,frame=frame)
    launcher.location=left+Vector((0,-.025,-.045))
    handle.location=right
    cord.location=(left+right)/2
    cord.rotation_mode='QUATERNION'
    cord.rotation_quaternion=(right-left).to_track_quat('X','Z')
    cord.scale.x=(right-left).length
    # shortcut: the free ripcord is hidden after extraction; add flexible dynamics for a close-up production shot.
    cord.scale.y=cord.scale.z=1 if frame<42 else .0001
    if frame<=39:
        top.location=launcher.location+Vector((0,0,-.075))
    else:
        t=min((frame-39)/30,(-1+math.sqrt(1+8*.91))/4)
        top.location=Vector((-.20,-.495, .96))+Vector((0,-.95*t,-min(.91,1.0*t+2.0*t*t)))
    top.rotation_euler.z=(max(0,frame-39)/30)*55
    for obj in (launcher,handle,cord,top):
        for prop in ('location','rotation_euler','scale'):obj.keyframe_insert(data_path=prop,frame=frame)
        if obj.rotation_mode=='QUATERNION':obj.keyframe_insert(data_path='rotation_quaternion',frame=frame)
    assert (launcher.location-left-Vector((0,-.025,-.045))).length<1e-6
    for side in ('L','R'):
        assert abs((joints[side+'_Upperarm'][1]-joints[side+'_Upperarm'][0]).length-.30)<1e-6
        assert abs((joints[side+'_Forearm'][1]-joints[side+'_Forearm'][0]).length-.29)<1e-6
        if frame>1: assert (joints[side+'_Foot'][0]-pose(1)[0][side+'_Foot'][0]).length<1e-6
    bpy.context.view_layer.update()
    for name,(a,b) in joints.items():
        assert (rig.pose.bones[name].matrix.translation-a).length<1e-4, name
    records.append({'frame':frame,'left_hand':list(left),'right_hand':list(right),'bey':list(top.location)})
rig.animation_data.action.name='Launch_Blocking_v1_30fps'
for f,label in [(1,'READY'),(17,'SET'),(32,'PULL'),(40,'RELEASE'),(54,'FOLLOW THROUGH'),(89,'RECOVER')]:scene.timeline_markers.new(label,frame=f)

box('Floor',(0,-.3,-.045),(4,4,.05),(.11,.15,.21))
box('LandingPad',(-.2,-1.3,0),(1.2,.9,.025),(.16,.27,.36))
bpy.ops.object.camera_add(location=(3.0,-4.7,2.7))
camera=bpy.context.object;camera.name='ReviewCamera'
camera.rotation_euler=(Vector((0,-.35,.88))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO';camera.data.ortho_scale=2.65;scene.camera=camera
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO'
scene.display.shading.color_type='OBJECT'
scene.display.shading.show_shadows=True
scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='BOTH'
scene.display.shading.background_type='WORLD'
scene.world=bpy.data.worlds.new('ReviewWorld')
scene.world.color=(.045,.06,.085)
scene.render.resolution_x=720;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.frame_set(1)
for obj in bpy.data.objects:
    if obj.type=='MESH':
        material=bpy.data.materials.new(obj.name+'Color')
        material.diffuse_color=obj.color
        material.use_nodes=True
        material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=obj.color
        material.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.75
        obj.data.materials.append(material)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'launch-blocking-v1.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'launch-blocking-v1.glb'),export_format='GLB',export_animations=True,export_animation_mode='SCENE',export_anim_scene_split_object=False)
(OUT/'checks.json').write_text(json.dumps({'status':'PASS','fps':30,'frames':96,'release_frame':40,'checks':['fixed feet','constant arm segment lengths','launcher follows left hand','pose bone matrices match targets'],'samples':records},indent=2))
for frame in range(1,97,2):
    scene.frame_set(frame)
    scene.render.filepath=str(OUT/f'frame-{frame:03}.png')
    bpy.ops.render.render(write_still=True)

# Read the deliverable back so the review also checks exported bone motion.
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(OUT/'launch-blocking-v1.glb'))
imported=next(o for o in bpy.data.objects if o.type=='ARMATURE')
for frame in (1,31,39,41,55,95):
    bpy.context.scene.frame_set(frame)
    expected,_,_=pose(frame)
    for name,(a,b) in expected.items():
        actual=imported.matrix_world @ imported.pose.bones[name].head
        assert (actual-a).length<.001,(frame,name,list(actual),list(a))
(OUT/'export-check.json').write_text(json.dumps({'status':'PASS','reimported':'launch-blocking-v1.glb','frames_checked':[1,31,39,41,55,95],'bone_position_tolerance_m':.001},indent=2))
