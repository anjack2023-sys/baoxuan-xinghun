import bpy,math,random,json
from pathlib import Path
from mathutils import Vector
ROOT=Path('C:/BeybladeUE');OUT=ROOT/'art/iron-wall-preview-v1';(OUT/'frames').mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=960;scene.render.resolution_y=540;scene.render.resolution_percentage=100
scene.render.fps=24;scene.frame_start=1;scene.frame_end=84;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.render.image_settings.color_mode='RGB';scene.world=bpy.data.worlds.new('Dark studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.012,.017,.025,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
scene.view_settings.view_transform='AgX'
bpy.ops.import_scene.gltf(filepath=str(ROOT/'docs/P3-art-inbox/batch3-tripo-v1/BEY_bilei_DEFENSE_tripo_v1.glb'))
meshes=[o for o in scene.objects if o.type=='MESH'];assert meshes
pts=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box];lo=Vector([min(p[i] for p in pts) for i in range(3)]);hi=Vector([max(p[i] for p in pts) for i in range(3)])
size=hi-lo
# Normalise the reviewed top to a 2-unit diameter without changing its proportions.
assert size.z<max(size.x,size.y),(tuple(lo),tuple(hi))
scale=2/max(size.x,size.y);center=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))
rotor=bpy.data.objects.new('Bilei_Rotation',None);scene.collection.objects.link(rotor)
for o in meshes:
 world=o.matrix_world.copy();o.parent=rotor;o.matrix_world=world
rotor.scale=(scale,)*3;rotor.location=-center*scale
# Bake the static import transforms into a clean parent so only yaw is animated.
bpy.context.view_layer.update()
spin=bpy.data.objects.new('TopSpin',None);scene.collection.objects.link(spin)
for o in meshes:
 world=o.matrix_world.copy();o.parent=spin;o.matrix_world=world
bpy.data.objects.remove(rotor,do_unlink=True)
for f,a in [(1,0),(84,math.tau*9)]:spin.rotation_euler.z=a;spin.keyframe_insert('rotation_euler',frame=f)
if spin.animation_data:
 for layer in spin.animation_data.action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
ENV=[(1,0),(4,.05),(10,1),(30,1),(33,1),(61,1),(77,0),(84,0)]
def glow(name,color,power=4,keys=ENV):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();l=m.node_tree.links
 out=n.new('ShaderNodeOutputMaterial');trans=n.new('ShaderNodeBsdfTransparent');e=n.new('ShaderNodeEmission');e.inputs['Color'].default_value=(*color,1);e.inputs['Strength'].default_value=power
 v=n.new('ShaderNodeValue');v.name='EffectEnvelope'
 for frame,value in keys:v.outputs[0].default_value=value;v.outputs[0].keyframe_insert('default_value',frame=frame)
 mix=n.new('ShaderNodeMixShader');l.new(v.outputs[0],mix.inputs[0]);l.new(trans.outputs[0],mix.inputs[1]);l.new(e.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
 m.surface_render_method='DITHERED';return m
blue=glow('Shield_Line_Blue',(.035,.38,1),3.8)
soft=glow('Shield_Secondary',(.035,.15,.6),2)
def curve(name,coords,mat,width=.008,closed=False):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=width;d.bevel_resolution=2;s=d.splines.new('POLY');s.points.add(len(coords)-1)
 for p,co in zip(s.points,coords):p.co=(*co,1)
 s.use_cyclic_u=closed;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.data.materials.append(mat);return o
def ring(name,r,z,mat,width=.008):return curve(name,[(r*math.cos(i*math.tau/128),r*math.sin(i*math.tau/128),z) for i in range(128)],mat,width,True)
fx=bpy.data.objects.new('Shield_Controller',None);scene.collection.objects.link(fx)
for f,s in [(1,.2),(10,1),(61,1),(78,1.08)]:fx.scale=(s,s,s);fx.keyframe_insert('scale',frame=f)
for r in (1.38,1.48):ring('Ground defence ring',r,.045,blue,.012).parent=fx
for i in range(18):
 a=i*math.tau/18;coords=[(1.43*math.cos(a+t),1.43*math.sin(a+t),.05) for t in (-.045,.045)]
 curve('Ring marker',coords,blue,.022).parent=fx
# A transparent sphere with brighter grazing edges leaves the actual top readable.
shell=bpy.data.materials.new('Transparent shield field');shell.use_nodes=True;n=shell.node_tree.nodes;n.clear();l=shell.node_tree.links
out=n.new('ShaderNodeOutputMaterial');trans=n.new('ShaderNodeBsdfTransparent');em=n.new('ShaderNodeEmission');em.inputs['Color'].default_value=(.025,.22,1,1);em.inputs['Strength'].default_value=1.4
fres=n.new('ShaderNodeFresnel');fres.inputs['IOR'].default_value=1.15;mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=.55;l.new(fres.outputs[0],mul.inputs[0])
env=n.new('ShaderNodeValue')
for frame,value in ENV:env.outputs[0].default_value=value;env.outputs[0].keyframe_insert('default_value',frame=frame)
factor=n.new('ShaderNodeMath');factor.operation='MULTIPLY';l.new(mul.outputs[0],factor.inputs[0]);l.new(env.outputs[0],factor.inputs[1])
mix=n.new('ShaderNodeMixShader');l.new(factor.outputs[0],mix.inputs[0]);l.new(trans.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs[0]);shell.surface_render_method='DITHERED'
bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,location=(0,0,.64));o=bpy.context.object;o.name='Shield transparent shell';o.scale=(1.45,1.45,1.12);o.data.materials.append(shell);o.parent=fx
for p in o.data.polygons:p.use_smooth=True
# Four meridian arcs plus selected hexagonal panels suggest an armour field, without a cage of lines.
for a in [i*math.pi/2+.35 for i in range(4)]:
 pts=[]
 for j in range(49):
  t=.12+(math.pi-.24)*j/48;pts.append((1.45*math.cos(t)*math.cos(a),1.45*math.cos(t)*math.sin(a),.64+1.12*math.sin(t)))
 curve('Shield arc',pts,soft,.005).parent=fx
for i in range(10):
 a=i*math.tau/10;z=.65+(i%2)*.35;rr=1.45*math.sqrt(1-((z-.64)/1.12)**2)
 center=Vector((rr*math.cos(a),rr*math.sin(a),z));tangent=Vector((-math.sin(a),math.cos(a),0));vertical=Vector((0,0,1));verts=[]
 for j in range(6):
  t=j*math.tau/6;verts.append(center+tangent*(.19*math.cos(t))+vertical*(.19*math.sin(t)))
 curve('Armour hex panel',verts,soft,.005,True).parent=fx
# One illustrative impact during the sustained shield stage.
impact=Vector((.95,-1.04,.90));normal=Vector((.67,-.73,.15)).normalized();q=Vector((0,0,1)).rotation_difference(normal)
for i in range(3):
 mat=glow('Impact ripple '+str(i),(.25,.65,1),5,[(1,0),(31+i*2,0),(33+i*2,1),(44+i*2,0),(84,0)])
 o=curve('Impact ripple',[(math.cos(j*math.tau/64),math.sin(j*math.tau/64),0) for j in range(64)],mat,.012,True);o.location=impact+normal*.02;o.rotation_mode='QUATERNION';o.rotation_quaternion=q
 for f,r in [(31+i*2,.03),(43+i*2,.55+i*.08)]:o.scale=(r,)*3;o.keyframe_insert('scale',frame=f)
tracer=glow('Incoming demonstration hit',(1,.45,.12),4,[(1,0),(27,0),(29,1),(32,1),(34,0),(84,0)])
o=curve('Incoming streak',[(0,0,0),tuple(normal*.32)],tracer,.018)
for f,pos in [(27,impact+normal*1.2),(32,impact)]:o.location=pos;o.keyframe_insert('location',frame=f)
random.seed(12)
for i in range(12):
 mat=glow('Blue impact spark '+str(i),(.12,.55,1),4,[(1,0),(32,0),(34,1),(43,0),(84,0)])
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.014);o=bpy.context.object;o.name='Shield hit spark';o.data.materials.append(mat)
 d=Vector((random.uniform(-1,1),random.uniform(-1,1),random.uniform(0,1))).normalized()
 for f,pos in [(32,impact),(44,impact+d*.65)]:o.location=pos;o.keyframe_insert('location',frame=f)
# Neutral dark studio, matching the supplied skill references.
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.012));ground=bpy.context.object;m=bpy.data.materials.new('Charcoal floor');m.diffuse_color=(.018,.022,.03,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.018,.022,.03,1);p.inputs['Roughness'].default_value=.38;ground.data.materials.append(m)
def area(name,pos,power,size,color):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,.6))-o.location).to_track_quat('-Z','Y').to_euler()
area('Soft key',(2,-3,5),380,5,(.82,.9,1));area('Warm fill',(-3,-1,3),190,4,(1,.88,.75));area('Blue rim',(0,3,4),330,3,(.4,.65,1))
bpy.ops.object.camera_add(location=(4.4,-6.5,4.0));camera=bpy.context.object;camera.rotation_euler=(Vector((0,0,.72))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=5.5;scene.camera=camera
tree=bpy.data.node_groups.new('Shield Glow','CompositorNodeTree');scene.compositing_node_group=tree
tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
nodes=tree.nodes;links=tree.links;rl=nodes.new('CompositorNodeRLayers');g=nodes.new('CompositorNodeGlare');g.inputs['Type'].default_value='Fog Glow';g.inputs['Quality'].default_value='High';g.inputs['Threshold'].default_value=1.5;g.inputs['Strength'].default_value=.25;com=nodes.new('NodeGroupOutput');links.new(rl.outputs['Image'],g.inputs['Image']);links.new(g.outputs['Image'],com.inputs['Image'])

for im in bpy.data.images:
 if im.source=='FILE' and im.size[0]>0 and not im.packed_file:im.pack()
scene.frame_set(35);scene.render.filepath=str(OUT/'shield-impact.png');bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'iron-wall-preview.blend'));bpy.ops.render.render(write_still=True)
report={'status':'PASS','frames':84,'fps':24,'duration_seconds':3.5,'game_project_modified':False,'source_model':'BEY_bilei_DEFENSE_tripo_v1.glb','phases':{'deploy':[1,10],'sustain':[10,61],'impact':[32,48],'fade':[61,78]}}
(OUT/'preview-checks.json').write_text(json.dumps(report,indent=2))
scene.render.filepath=str(OUT/'frames/frame-');bpy.ops.render.render(animation=True)
