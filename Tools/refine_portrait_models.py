"""Non-destructive portrait-led mesh, palette and hair refinement of both launch rigs."""
import json,math
from pathlib import Path
import bpy,bmesh
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'art/portrait-refine-v1';OUT.mkdir(parents=True,exist_ok=True)
SOURCES={'male':('art/male-launch-review-v2/male-redcord-launch.blend','MaleLeadMesh'),
         'female':('art/female-rigged-launch-v1/female-redcord-launch.blend','FemaleLeadMesh')}

def linear(rgb):
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb)

def light(name,location,power,size):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(obj);obj.location=location
    obj.rotation_euler=(Vector((0,0,1))-obj.location).to_track_quat('-Z','Y').to_euler()

def studio(scene):
    for obj in list(scene.objects):
        if obj.type=='LIGHT':bpy.data.objects.remove(obj,do_unlink=True)
    scene.render.engine='BLENDER_EEVEE';scene.render.image_settings.file_format='PNG'
    scene.world=bpy.data.worlds.new('PortraitStudio');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.60,.64,.70,1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.30
    light('SoftKey',(3,-4,5),220,5);light('SoftFill',(-3,-2,3),110,4);light('HairRim',(0,3,4),70,3)
    scene.view_settings.view_transform='Standard'
    scene.render.resolution_percentage=100
    scene.render.film_transparent=False

def shot(scene,target,offset,scale,path,width=640,height=800):
    cam=scene.camera;cam.location=Vector(target)+Vector(offset)
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.type='ORTHO';cam.data.ortho_scale=scale
    scene.render.resolution_x=width;scene.render.resolution_y=height
    scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)

def grade_and_bake(mesh,who):
    source=mesh.data.materials[0]
    image=next(n.image for n in source.node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
    mat=bpy.data.materials.new(who+'IllustrationPalette');mat.use_nodes=True
    nodes=mat.node_tree.nodes;links=mat.node_tree.links;nodes.clear()
    texture=nodes.new('ShaderNodeTexImage');texture.image=image
    attribute=nodes.new('ShaderNodeVertexColor');attribute.layer_name='ArtMasks'
    separate=nodes.new('ShaderNodeSeparateColor');links.new(attribute.outputs['Color'],separate.inputs['Color'])
    rgb=nodes.new('ShaderNodeSeparateColor');links.new(texture.outputs['Color'],rgb.inputs['Color'])
    r,g,b=[rgb.outputs[n] for n in ('Red','Green','Blue')]
    def math_node(operation,a,b):
        node=nodes.new('ShaderNodeMath');node.operation=operation
        for i,value in enumerate((a,b)):
            if isinstance(value,(int,float)):node.inputs[i].default_value=value
            else:links.new(value,node.inputs[i])
        return node.outputs[0]
    def threshold(a,b):
        difference=math_node('SUBTRACT',a,b)
        node=nodes.new('ShaderNodeMapRange');node.interpolation_type='SMOOTHSTEP'
        node.inputs['From Min'].default_value=-.008;node.inputs['From Max'].default_value=.008
        links.new(difference,node.inputs['Value']);return node.outputs['Result']
    skin_pixel=math_node('MULTIPLY',threshold(r,math_node('MULTIPLY',g,1.07)),threshold(g,math_node('MULTIPLY',b,1.03)))
    skin_pixel=math_node('MULTIPLY',skin_pixel,threshold(b,math_node('MULTIPLY',r,.48)))
    skin_pixel=math_node('MULTIPLY',skin_pixel,threshold(r,.16))
    skin=math_node('MULTIPLY',skin_pixel,separate.outputs['Red'])
    navy=math_node('MULTIPLY',threshold(b,math_node('MULTIPLY',r,1.14)),threshold(b,math_node('MULTIPLY',g,1.05)))
    navy=math_node('MULTIPLY',navy,math_node('LESS_THAN',b,.6))
    maximum=math_node('MAXIMUM',r,math_node('MAXIMUM',g,b))
    minimum=math_node('MINIMUM',r,math_node('MINIMUM',g,b))
    hair=math_node('MULTIPLY',threshold(r,math_node('MULTIPLY',g,1.04)),threshold(r,math_node('MULTIPLY',b,1.05)))
    hair=math_node('MULTIPLY',hair,math_node('LESS_THAN',maximum,.20))
    hair=math_node('MULTIPLY',hair,math_node('SUBTRACT',1,skin_pixel))
    cream=math_node('MULTIPLY',threshold(maximum,.38),threshold(minimum,math_node('MULTIPLY',maximum,.72)))
    cream=math_node('MULTIPLY',cream,attribute.outputs['Alpha'])
    result=texture.outputs['Color']
    for mask,color,strength in [(skin,(.96,.70,.53),.22),(navy,(.12,.16,.27),.20),
                                (hair,(.15,.105,.09),.22),(cream,(.93,.89,.80),.15)]:
        multiply=nodes.new('ShaderNodeMath');multiply.operation='MULTIPLY';multiply.inputs[1].default_value=strength;links.new(mask,multiply.inputs[0])
        mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX';links.new(multiply.outputs[0],mix.inputs[0]);links.new(result,mix.inputs[1]);mix.inputs[2].default_value=(*linear(color),1);result=mix.outputs[0]
    emission=nodes.new('ShaderNodeEmission');links.new(result,emission.inputs['Color'])
    output=nodes.new('ShaderNodeOutputMaterial');links.new(emission.outputs[0],output.inputs['Surface'])
    baked=image.copy();baked.name=who+'IllustrationColor'
    target=nodes.new('ShaderNodeTexImage');target.image=baked;nodes.active=target;target.select=True
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.mesh.primitive_plane_add(size=2,location=(100,0,0))
    plane=bpy.context.object;plane.data.materials.append(mat)
    attributes=plane.data.color_attributes.new(name='ArtMasks',type='FLOAT_COLOR',domain='CORNER')
    for item in attributes.data:item.color=(1,1,1,1)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1;scene.render.threads_mode='FIXED';scene.render.threads=8
    scene.render.bake.margin=0;scene.render.bake.use_clear=False;bpy.ops.object.bake(type='EMIT')
    baked.filepath_raw=str(OUT/(who+'-illustration-color.png'));baked.file_format='PNG';baked.save();baked.pack()
    plane_data=plane.data;bpy.data.objects.remove(plane,do_unlink=True);bpy.data.meshes.remove(plane_data)
    mesh.data.materials[0]=mat
    nodes.clear();tex=nodes.new('ShaderNodeTexImage');tex.image=baked
    shader=nodes.new('ShaderNodeBsdfPrincipled');shader.inputs['Roughness'].default_value=.95;shader.inputs['Specular IOR Level'].default_value=.10
    links.new(tex.outputs['Color'],shader.inputs['Base Color'])
    links.new(tex.outputs['Color'],shader.inputs['Emission Color']);shader.inputs['Emission Strength'].default_value=.08
    output=nodes.new('ShaderNodeOutputMaterial');links.new(shader.outputs['BSDF'],output.inputs['Surface']);nodes.active=tex
    return baked

report={}
for who,(source_path,mesh_name) in SOURCES.items():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/source_path));scene=bpy.context.scene;scene.frame_set(1)
    rig=next(o for o in scene.objects if o.type=='ARMATURE');mesh=bpy.data.objects[mesh_name]
    for obj in scene.objects:
        if obj.type=='MESH' and obj!=mesh:obj.hide_render=True
    if 'LaunchSocket' not in rig.data.bones:
        bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
        bpy.ops.object.mode_set(mode='EDIT')
        hand=rig.data.edit_bones['R_Hand'];socket=rig.data.edit_bones.new('LaunchSocket')
        socket.head=hand.matrix@Vector((-.0692741275,.1273543239,.0841545612));socket.tail=socket.head+Vector((0,0,.01));socket.parent=hand;socket.use_deform=False
        bpy.ops.object.mode_set(mode='OBJECT')
    rig.data.pose_position='REST';head=rig.data.bones['Head'].head_local.copy()
    original_count=len(mesh.data.vertices)
    original_weights=[[(g.group,g.weight) for g in v.groups] for v in mesh.data.vertices]
    original_uv=[list(v.uv) for v in mesh.data.uv_layers.active.data]
    animation_samples={}
    rig.data.pose_position='POSE'
    for frame in (1,18,48,79,88,143):
        scene.frame_set(frame);animation_samples[frame]={b.name:b.matrix.copy() for b in rig.pose.bones}
    rig.data.pose_position='REST';scene.frame_set(1)
    studio(scene)
    shot(scene,head+Vector((0,-.03,.075)),(.3,-1,.015),.44,OUT/(who+'-face-before.png'))
    shot(scene,(0,0,.88),(2.6,-4.5,.3),2.05,OUT/(who+'-body-before.png'),720,1000)
    texture=next(n.image for n in mesh.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
    bm=bmesh.new();bm.from_mesh(mesh.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-5)
    bm.verts.ensure_lookup_table()
    tree=KDTree(len(bm.verts))
    for v in bm.verts:tree.insert(v.co,v.index)
    tree.balance()
    source_to_welded=[tree.find(v.co)[1] for v in mesh.data.vertices]
    smooth_ids=set()
    for v in mesh.data.vertices:
        weight=sum(g.weight for g in v.groups if mesh.vertex_groups[g.group].name=='Head')
        if weight>.55 and head.z-.02<v.co.z<head.z+.17 and v.co.y<head.y+.015:smooth_ids.add(source_to_welded[v.index])
    for _ in range(2):bmesh.ops.smooth_vert(bm,verts=[bm.verts[i] for i in smooth_ids],factor=.16,use_axis_x=True,use_axis_y=True,use_axis_z=True)
    # Smooth coincident UV-split vertices together without welding the actual skin or UVs.
    for v in mesh.data.vertices:
        index=source_to_welded[v.index]
        if index in smooth_ids:v.co=bm.verts[index].co
    bm.free()
    moved=0
    hair_moved=0
    for v in mesh.data.vertices:
        old=v.co.copy();delta=v.co-head
        weight=sum(g.weight for g in v.groups if mesh.vertex_groups[g.group].name=='Head')
        if weight>.4:
            nose=math.exp(-(delta.x/.023)**2-((delta.z-(.09 if who=='male' else .07))/.032)**2)
            if delta.y<-.035:v.co.y+=nose*.006*weight
            if delta.z>.18 and abs(delta.x)>.06:
                v.co.x+=math.copysign(.003*min(1,(abs(delta.x)-.06)/.06),delta.x)*weight;hair_moved+=1
            if who=='female' and delta.y>.14:
                amount=min(1,(delta.y-.14)/.18)*weight;v.co.x+=(delta.x*.035-.003)*amount;hair_moved+=1
            jaw=math.exp(-((delta.z-.015)/.045)**2)
            v.co.x=head.x+(v.co.x-head.x)*(1+(.025 if who=='male' else -.035)*jaw*weight)
        if (v.co-old).length>1e-6:moved+=1
    seam_groups={}
    for index,group in enumerate(source_to_welded):seam_groups.setdefault(group,[]).append(index)
    for indices in seam_groups.values():
        if len(indices)>1:
            center=sum((mesh.data.vertices[i].co for i in indices),Vector())/len(indices)
            for index in indices:mesh.data.vertices[index].co=center
    assert all((mesh.data.vertices[indices[0]].co-mesh.data.vertices[i].co).length<1e-6 for indices in seam_groups.values() for i in indices)
    for face in mesh.data.polygons:face.use_smooth=True
    baked=grade_and_bake(mesh,who)
    locks=[]
    studio(scene)
    shot(scene,head+Vector((0,-.03,.075)),(.3,-1,.015),.44,OUT/(who+'-face-after.png'))
    shot(scene,(0,0,.88),(2.6,-4.5,.3),2.05,OUT/(who+'-body-after.png'),720,1000)
    assert len(mesh.data.vertices)==original_count
    assert original_weights==[[(g.group,g.weight) for g in v.groups] for v in mesh.data.vertices]
    assert original_uv==[list(v.uv) for v in mesh.data.uv_layers.active.data]
    rig.data.pose_position='POSE'
    for frame,expected in animation_samples.items():
        scene.frame_set(frame)
        for name,matrix in expected.items():
            assert max(abs(matrix[r][c]-rig.pose.bones[name].matrix[r][c]) for r in range(4) for c in range(4))<1e-5,(who,frame,name)
        if frame in (18,48,88):shot(scene,(0,-.2,.86),(2.6,-4.5,1.1),2.05,OUT/f'{who}-action-{frame:03}.png',720,1000)
    scene.frame_set(1)
    for image in bpy.data.images:
        if image.source=='FILE' and image.size[0]>0 and not image.packed_file:image.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(who+'-illustration-refined.blend')))
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);mesh.select_set(True)
    for obj in locks:obj.select_set(True)
    bpy.context.view_layer.objects.active=rig
    bpy.ops.export_scene.gltf(filepath=str(OUT/(who+'-illustration-refined.glb')),use_selection=True,export_format='GLB',export_animation_mode='SCENE',export_anim_scene_split_object=False)
    bpy.ops.export_scene.fbx(filepath=str(OUT/(who+'-illustration-refined.fbx')),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0)
    report[who]={'source_vertices':original_count,'head_vertices_adjusted':moved,'existing_hair_vertices_adjusted':hair_moved,'skin_weights_unchanged':True,'original_uv_unchanged':True,'bone_animation_unchanged':True,'uv_seam_positions_continuous':True,'release_socket_present':'LaunchSocket' in rig.data.bones,'verified_frames':list(animation_samples),'baked_color_size':list(baked.size)}
(OUT/'checks.json').write_text(json.dumps({'status':'PASS','characters':report},indent=2))
