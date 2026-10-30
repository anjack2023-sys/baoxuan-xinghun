import unreal,time
from pathlib import Path
out=Path('C:/BeybladeUE/Saved/StarCrownVisual');out.mkdir(exist_ok=True)
l=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);assert l.load_level('/Game/Maps/RankedArena_v1');cam=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.CameraActor,unreal.Vector());cam.tags=['StarReviewCamera'];s={'sent':set(),'wall':time.monotonic()}
def tick(dt):
 worlds=unreal.EditorLevelLibrary.get_pie_worlds(False)
 if not worlds:return
 w=worlds[0];pc=unreal.GameplayStatics.get_player_controller(w,0);t=unreal.GameplayStatics.get_time_seconds(w)
 if 'cam' not in s:
  s['cam']=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.CameraActor) if 'StarReviewCamera' in [str(x) for x in a.tags]);pc.set_view_target_with_blend(s['cam'],0);unreal.SystemLibrary.execute_console_command(w,'showhud',pc)
 for i,(at,name,pos,aim) in enumerate([(1,'wide',(0,1080,570),(0,-110,160)),(3,'score',(0,-150,390),(0,-640,365)),(5,'table',(0,180,550),(0,0,60))]):
  if t>at and i not in s['sent']:
   p=unreal.Vector(*pos);s['cam'].set_actor_location_and_rotation(p,unreal.MathLibrary.find_look_at_rotation(p,unreal.Vector(*aim)),False,True);s['cam'].get_component_by_class(unreal.CameraComponent).set_field_of_view(70);s['sent'].add(i)
  if t>at+.5 and name not in s['sent']:
   unreal.SystemLibrary.execute_console_command(w,'HighResShot 1280x720 filename='+str(out/(name+'.png')).replace('\\','/'),pc);s['sent'].add(name)
 if t>7:
  unreal.unregister_slate_post_tick_callback(s['h']);l.editor_request_end_play();unreal.SystemLibrary.quit_editor()
s['h']=unreal.register_slate_post_tick_callback(tick);l.editor_request_begin_play()
