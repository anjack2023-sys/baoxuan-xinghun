import unreal,json,traceback
from pathlib import Path
root=Path(r'C:/Users/Administrator/Desktop/ai陀螺游戏/bey-art-refs/ai-avatar-warm-v2');report={};actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
try:
 for label in ['GPT','GROK']:
  base='/Game/FeelLab/Characters/AIAvatars/'+label;mesh=unreal.load_asset(base+'/SK_'+label);assert mesh and mesh.skeleton
  assert 170<mesh.get_bounds().box_extent.z*2<190
  assert all(slot.material_interface for slot in mesh.materials)
  clips={}
  for name,seconds in [('Idle',2.),('Walk',28/30),('Run',20/30),('LaunchR',143/30),('LaunchL',143/30)]:
   a=unreal.load_asset(base+'/A_'+name);assert a and a.get_editor_property('skeleton')==mesh.skeleton
   assert abs(a.get_play_length()-seconds)<1.e-5;clips[name]=a.get_play_length()
  actor=actors.spawn_actor_from_class(unreal.SkeletalMeshActor,unreal.Vector(0,0,0));comp=actor.skeletal_mesh_component;comp.set_skeletal_mesh(mesh)
  delta=comp.get_socket_location('LaunchSocket')-comp.get_socket_location('R_Hand');assert delta.y>10 and abs(delta.x)<2,str(delta)
  actors.destroy_actor(actor);report[label]={'skeleton':mesh.skeleton.get_path_name(),'height_cm':2*mesh.get_bounds().box_extent.z,'animations':clips,'socket_delta_cm':str(delta)}
 report['status']='PASS'
except Exception:report.update(status='FAIL',error=traceback.format_exc());unreal.log_error(report['error'])
(root/'fresh-load-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');unreal.SystemLibrary.quit_editor()

