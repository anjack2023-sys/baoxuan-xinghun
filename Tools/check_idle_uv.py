import bpy,math,json
from mathutils import Matrix
from pathlib import Path
out=Path('C:/BeybladeUE/art/portrait-refine-v1')
bpy.ops.wm.open_mainfile(filepath=str(out/'male-illustration-refined.blend'))
mesh=bpy.data.objects['MaleLeadMesh'];coords=[v.co.copy() for v in mesh.data.vertices];normals=[n.vector.copy() for n in mesh.data.corner_normals];indices=[l.vertex_index for l in mesh.data.loops];uvs={layer.name:[tuple(d.uv) for d in layer.data] for layer in mesh.data.uv_layers}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath='C:/BeybladeLaunchWork/LabSources/TripoMaleLauncher-v1/tripo_convert_e53ccadf-79af-4870-b609-39f5054e33d9.fbx',use_anim=False)
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH')
hip=rig.matrix_world@rig.data.bones['Hip'].head_local;normal=Matrix.Rotation(-math.pi/2,4,'Z')@Matrix.Scale(1.85,4);center=normal@hip;normal=Matrix.Translation((-center.x,-center.y,0))@normal
inv=(normal@mesh.matrix_world).inverted();ntransform=inv.to_3x3().inverted().transposed()
assert indices==[l.vertex_index for l in mesh.data.loops]
print('UV_COMPARISON',json.dumps({'refined':list(uvs),'original':[l.name for l in mesh.data.uv_layers],'differences':{l.name:{name:max((abs(d.uv.x-uv[0])+abs(d.uv.y-uv[1])) for d,uv in zip(l.data,values)) for name,values in uvs.items()} for l in mesh.data.uv_layers}}))
old_normals=[n.vector.copy() for n in mesh.data.corner_normals]
new_normals=[(ntransform@n).normalized() for n in normals]
head=mesh.vertex_groups.get('Head');head_ids={v.index for v in mesh.data.vertices if any(g.group==head.index and g.weight>.5 for g in v.groups)}
dots=[a.dot(b) for a,b,l in zip(old_normals,new_normals,mesh.data.loops) if l.vertex_index in head_ids]
for v,co in zip(mesh.data.vertices,coords):v.co=inv@co
for p in mesh.data.polygons:p.use_smooth=True
mesh.data.normals_split_custom_set(new_normals)
rig.animation_data_clear()
for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);mesh.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(out/'male-refined-idle-normals.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,axis_forward='-Z',axis_up='Y',mesh_smooth_type='FACE')
(out/'idle-normal-check.json').write_text(json.dumps({'head_corners':len(dots),'mean_normal_dot':sum(dots)/len(dots),'opposing_normals':sum(d<0 for d in dots),'topology_unchanged':True},indent=2))

