import unreal,json,time,traceback
from pathlib import Path
out=Path('C:/BeybladeUE/Saved/TrainingHallCheck');out.mkdir(exist_ok=True)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);assert levels.load_level('/Game/Maps/StadiumIndustrialPolish_v1')
review=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.CameraActor,unreal.Vector())
review.tags=['ReviewFaceCamera']
state={'wall':time.monotonic(),'clock':0.,'prev':None,'sent':set(),'shots':set(),'samples':[]}
events=[(1,'launch_action'),(2,'pick3_action'),(2.4,'pick4_action'),(2.8,'pick5_action'),(3.3,'launch_action'),(5,'launch_action'),(12,'reset_action'),(13,'launch_action'),(14,'pick3_action'),(14.4,'pick4_action'),(14.8,'pick5_action'),(15.3,'launch_action'),(17,'launch_action'),(18,'reset_action')]
shots=[(.9,'lobby'),(4,'prep'),(5.4,'hold'),(6.1,'insert'),(6.8,'count1'),(7.25,'count2'),(7.6,'count3'),(8.2,'flight'),(10.5,'battle'),(12.5,'reset'),(16,'second_prep'),(17.5,'second_launch'),(18.5,'cancelled')]
def finish(status,error=None):
 (out/'report.json').write_text(json.dumps({'status':status,'error':error,'samples':state['samples']},indent=2))
 unreal.unregister_slate_post_tick_callback(state['h']);levels.editor_request_end_play();unreal.SystemLibrary.quit_editor()
def tick(dt):
 try:
  assert time.monotonic()-state['wall']<200,'PIE timeout'
  worlds=unreal.EditorLevelLibrary.get_pie_worlds(False)
  if not worlds:return
  world=worlds[0];now=unreal.GameplayStatics.get_time_seconds(world)
  if state['prev'] is not None:state['clock']+=min(max(now-state['prev'],0),.1)
  state['prev']=now;t=state['clock']
  pc=unreal.GameplayStatics.get_player_controller(world,0)
  subsystem=next(o for o in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if 'Default__' not in o.get_name())
  for index,(at,action) in enumerate(events):
   if t>=at and index not in state['sent']:
    subsystem.inject_input_vector_for_action(next(a for a in unreal.ObjectIterator(unreal.InputAction) if a.get_outer()==pc and any(str(k.get_editor_property('key_name'))=={'launch_action':'SpaceBar','reset_action':'R','pick3_action':'Three','pick4_action':'Four','pick5_action':'Five'}[action] for k in subsystem.query_keys_mapped_to_action(a))),unreal.Vector(1,0,0),[],[]);state['sent'].add(index)
  for at,name in shots:
   if t<at or name in state['shots']:continue
   actors=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor)
   male=next(a for a in actors if 'FaceCameraCharacter' in [str(x) for x in a.tags])
   female=next(a for a in actors if 'OpponentCharacter' in [str(x) for x in a.tags])
   comps=male.get_components_by_class(unreal.SkeletalMeshComponent)
   idle=next(c for c in comps if c.skeletal_mesh and c.skeletal_mesh.get_name()=='SK_MaleIdleLit')
   launch=next(c for c in comps if c.skeletal_mesh and c.skeletal_mesh.get_name()=='SK_MaleLaunch')
   girl=female.get_component_by_class(unreal.SkeletalMeshComponent)
   assert idle and launch and girl
   assert all('PortraitRefinedV3' in c.get_material(0).get_path_name() for c in (idle,launch,girl))
   head=idle.get_socket_location('Head');hip=idle.get_socket_location('Hip')
   assert head.z-hip.z>50,'male idle is prone or collapsed'
   assert abs(launch.get_world_scale().z-girl.get_world_scale().z)<.001,'character scales differ'
   if name in ('hold','insert','count1','count2','count3','second_launch'):
    assert launch.is_visible() and not idle.is_visible(),('launch not playing',name)
    assert abs(launch.get_position()-girl.get_position())<.001
    for tag,pose in [('BattleP1',launch),('BattleP2',girl)]:
     bey=next(a for a in actors if tag in [str(x) for x in a.tags])
     assert (bey.get_actor_location()-pose.get_socket_location('LaunchSocket')).length()<.1,('detached bey',name,tag)
   if name in ('prep','battle','reset','second_prep','cancelled'):
    assert idle.is_visible() and not launch.is_visible(),('idle not restored',name)
    assert girl.get_position()<.001,('female not ready',name)
   sample={'phase':name,'time':t,'idle_mesh':idle.skeletal_mesh.get_path_name(),'idle_scale':str(idle.get_world_scale()),'launch_scale':str(launch.get_world_scale()),'launch_visible':launch.is_visible(),'launch_time':launch.get_position(),'female_time':girl.get_position(),'head_above_hip':head.z-hip.z,'male_socket':str(launch.get_socket_location('LaunchSocket')),'female_socket':str(girl.get_socket_location('LaunchSocket'))}
   state['samples'].append(sample);state['shots'].add(name)
   unreal.SystemLibrary.execute_console_command(world,'HighResShot 1280x720 filename=C:/BeybladeUE/Saved/TrainingHallCheck/'+name+'.png',pc)
  if 20<t<23:
   actors=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor)
   is_girl=t>=21.5
   person=next(a for a in actors if ('OpponentCharacter' if is_girl else 'FaceCameraCharacter') in [str(x) for x in a.tags])
   pose=next(c for c in person.get_components_by_class(unreal.SkeletalMeshComponent) if c.skeletal_mesh and (is_girl or c.skeletal_mesh.get_name()=='SK_MaleIdleLit'))
   head=pose.get_socket_location('Head')+unreal.Vector(0,0,18)
   front=person.get_actor_right_vector() if is_girl else person.get_actor_forward_vector()
   camera=next(a for a in actors if 'ReviewFaceCamera' in [str(x) for x in a.tags])
   pc.set_view_target_with_blend(camera,0)
   pos=head+front*140+unreal.Vector(0,0,5)
   camera.set_actor_location_and_rotation(pos,unreal.MathLibrary.find_look_at_rotation(pos,head),False,True)
   camera.get_component_by_class(unreal.CameraComponent).set_field_of_view(35)
   if 'hud_hidden' not in state:
    unreal.SystemLibrary.execute_console_command(world,'showhud',pc);state['hud_hidden']=True
   key='female_face' if is_girl else 'male_face'
   if (20.5<t<21.5 or t>22) and key not in state:
    unreal.SystemLibrary.execute_console_command(world,'HighResShot 1280x720 filename=C:/BeybladeUE/Saved/TrainingHallCheck/'+key+'.png',pc);state[key]=True
  if t>24:
   assert len(state['shots'])==len(shots);finish('PASS')
 except Exception:finish('FAIL',traceback.format_exc())
state['h']=unreal.register_slate_post_tick_callback(tick);levels.editor_request_begin_play()
