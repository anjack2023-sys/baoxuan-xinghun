"""Check the deliverable GLBs, including animation, release sockets and embedded textures."""
import json
from pathlib import Path
import bpy

OUT=Path(__file__).resolve().parents[1]/'art/portrait-refine-v1'
report={}
frames=(1,18,48,79,88,143)
for who in ('male','female'):
    bpy.ops.wm.open_mainfile(filepath=str(OUT/(who+'-illustration-refined.blend')))
    rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
    rig.data.pose_position='POSE'
    expected={}
    for frame in frames:
        bpy.context.scene.frame_set(frame)
        expected[frame]={b.name:(rig.matrix_world@b.matrix).translation.copy() for b in rig.pose.bones}
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps=30
    bpy.ops.import_scene.gltf(filepath=str(OUT/(who+'-illustration-refined.glb')))
    rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE'];assert len(rigs)==1
    imported=rigs[0];assert 'LaunchSocket' in imported.pose.bones
    for frame in frames:
        bpy.context.scene.frame_set(frame)
        for name,position in expected[frame].items():
            actual=imported.matrix_world@imported.pose.bones[name].head
            assert (position-actual).length<.001,(who,frame,name)
    assert any(i.size[0]==8192 for i in bpy.data.images)
    report[who]={'status':'PASS','bones':len(imported.pose.bones),'checked_frames':list(frames),'bone_position_tolerance_m':.001,'embedded_8k_texture':True,'release_socket':True}
(OUT/'export-check.json').write_text(json.dumps(report,indent=2))
