import unreal,time,json,traceback
from pathlib import Path
out=Path('C:/BeybladeUE/Saved/PickLayoutCheck');out.mkdir(parents=True,exist_ok=True)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);assert levels.load_level('/Game/Maps/StadiumIndustrialPolish_v1')
s={'start':time.monotonic(),'sent':set(),'shots':set()}
def tick(dt):
 try:
  assert time.monotonic()-s['start']<90
  worlds=unreal.EditorLevelLibrary.get_pie_worlds(False)
  if not worlds:return
  w=worlds[0];t=unreal.GameplayStatics.get_time_seconds(w);pc=unreal.GameplayStatics.get_player_controller(w,0)
  for i,(at,key) in enumerate([(1,'SpaceBar'),(3,'Six'),(3.4,'Seven'),(3.8,'Eight')]):
   if t>=at and i not in s['sent']:
    sub=next(o for o in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if 'Default__' not in o.get_name())
    a=next(a for a in unreal.ObjectIterator(unreal.InputAction) if a.get_outer()==pc and any(str(k.get_editor_property('key_name'))==key for k in sub.query_keys_mapped_to_action(a)))
    sub.inject_input_vector_for_action(a,unreal.Vector(1,0,0),[],[]);s['sent'].add(i)
  for at,name in [(2,'empty'),(4.5,'selected')]:
   if t>=at and name not in s['shots']:
    unreal.SystemLibrary.execute_console_command(w,'HighResShot 1280x720 filename='+str(out/(name+'.png')).replace('\\','/'),pc);s['shots'].add(name)
  if t>6:
   unreal.unregister_slate_post_tick_callback(s['h']);levels.editor_request_end_play();unreal.SystemLibrary.quit_editor()
 except Exception:
  (out/'error.txt').write_text(traceback.format_exc());unreal.unregister_slate_post_tick_callback(s['h']);unreal.SystemLibrary.quit_editor()
s['h']=unreal.register_slate_post_tick_callback(tick);levels.editor_request_begin_play()
