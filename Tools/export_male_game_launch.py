"""Export only the approved character and add a bone at its calibrated release point."""
from pathlib import Path
import bpy
from mathutils import Vector

root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'art/male-launch-review-v2/male-redcord-launch.blend'))
rig=bpy.data.objects['MaleLaunchRig']
bpy.context.scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
hand=rig.data.edit_bones['R_Hand']
socket=rig.data.edit_bones.new('LaunchSocket')
socket.head=hand.matrix@Vector((-.0692741275,.1273543239,.0841545612))
socket.tail=socket.head+Vector((0,0,.01))
socket.parent=hand
bpy.ops.object.mode_set(mode='OBJECT')
bpy.data.objects['MaleLeadMesh'].select_set(True)
out=Path('C:/BeybladeLaunchWork/LabSources/ApprovedLaunch')
out.mkdir(parents=True,exist_ok=True)
bpy.ops.export_scene.fbx(filepath=str(out/'MaleApprovedLaunch.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0)
