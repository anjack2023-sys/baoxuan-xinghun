import bpy,math
from mathutils import Matrix
from pathlib import Path
out=Path('C:/BeybladeUE/art/portrait-refine-v1')
bpy.ops.wm.open_mainfile(filepath=str(out/'male-illustration-refined.blend'))
coords=[v.co.copy() for v in bpy.data.objects['MaleLeadMesh'].data.vertices]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath='C:/BeybladeLaunchWork/LabSources/TripoMaleLauncher-v1/tripo_convert_e53ccadf-79af-4870-b609-39f5054e33d9.fbx',use_anim=False)
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH')
hip=rig.matrix_world@rig.data.bones['Hip'].head_local
normal=Matrix.Rotation(-math.pi/2,4,'Z')@Matrix.Scale(1.85,4);center=normal@hip
normal=Matrix.Translation((-center.x,-center.y,0))@normal
inv=(normal@mesh.matrix_world).inverted()
assert len(coords)==len(mesh.data.vertices)
for v,co in zip(mesh.data.vertices,coords):v.co=inv@co
rig.animation_data_clear()
for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);mesh.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(out/'male-refined-idle.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,axis_forward='-Z',axis_up='Y')
