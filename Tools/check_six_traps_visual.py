import unreal,time
from pathlib import Path
out=Path('C:/BeybladeUE/Saved/SixSlowTraps');levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert levels.load_level('/Game/Maps/RankedArena_AccentPreview')
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
camera=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(0,220,430));camera.tags=['TrapReviewCamera']
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(),unreal.Vector(0,0,45)),False)
camera.get_component_by_class(unreal.CameraComponent).set_field_of_view(65)
state={'sent':False,'start':time.monotonic()}
def tick(dt):
 worlds=unreal.EditorLevelLibrary.get_pie_worlds(False)
 if worlds:
  w=worlds[0];t=unreal.GameplayStatics.get_time_seconds(w);pc=unreal.GameplayStatics.get_player_controller(w,0)
  if t>2 and not state['sent']:
   cam=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.CameraActor) if 'TrapReviewCamera' in [str(x) for x in a.tags])
   pc.set_view_target_with_blend(cam,0);unreal.SystemLibrary.execute_console_command(w,'showhud',pc);state['sent']=True
  if t>4 and not state.get('shot'):
   unreal.SystemLibrary.execute_console_command(w,'HighResShot 1280x720 filename=C:/BeybladeUE/Saved/SixSlowTraps/in-game.png',pc);state['shot']=True
  if t>6:
   unreal.unregister_slate_post_tick_callback(state['handle']);levels.editor_request_end_play();unreal.SystemLibrary.quit_editor()
 if time.monotonic()-state['start']>90:
  unreal.SystemLibrary.quit_editor()
state['handle']=unreal.register_slate_post_tick_callback(tick);levels.editor_request_begin_play()
