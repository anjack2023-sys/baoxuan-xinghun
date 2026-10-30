import unreal,json,time,traceback
from pathlib import Path
out=Path('C:/BeybladeUE/Saved/CharacterRepair');out.mkdir(exist_ok=True)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);assert levels.load_level('/Game/Maps/StadiumIndustrialPolish_v1')
state={'start':time.monotonic()}
def tick(dt):
 try:
  worlds=unreal.EditorLevelLibrary.get_pie_worlds(False)
  if not worlds:return
  if time.monotonic()-state['start']<8:return
  world=worlds[0];rows=[]
  for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor):
   if any(t in [str(x) for x in a.tags] for t in ['FaceCameraCharacter','OpponentCharacter','BattleCamera','BattleGround','BattleBowl']):
    r={'actor':a.get_name(),'tags':[str(x) for x in a.tags],'location':str(a.get_actor_location()),'rotation':str(a.get_actor_rotation()),'scale':str(a.get_actor_scale3d()),'components':[]}
    for c in a.get_components_by_class(unreal.SkeletalMeshComponent):
     r['components'].append({'name':c.get_name(),'mesh':c.skeletal_mesh.get_path_name() if c.skeletal_mesh else None,'loc':str(c.get_world_location()),'rot':str(c.get_world_rotation()),'scale':str(c.get_world_scale()),'relative':str(c.get_relative_transform()),'visible':c.is_visible(),'bounds':str(c.skeletal_mesh.get_bounds()),'bones':{b:str(c.get_socket_location(b)) for b in ['Hip','Head','R_Hand','L_Hand','LaunchSocket'] if c.does_socket_exist(b)}})
    rows.append(r)
  pc=unreal.GameplayStatics.get_player_controller(world,0)
  rows.append({'input_docs':str(unreal.EnhancedInputLocalPlayerSubsystem.inject_input_for_action.__doc__),'action_value':str(unreal.InputActionValue.__doc__)})
  (out/'before.json').write_text(json.dumps(rows,indent=2))
  unreal.SystemLibrary.execute_console_command(world,'HighResShot 1280x720 filename=C:/BeybladeUE/Saved/CharacterRepair/before.png',pc)
  unreal.unregister_slate_post_tick_callback(state['h']);levels.editor_request_end_play();unreal.SystemLibrary.quit_editor()
 except Exception:
  (out/'before-error.txt').write_text(traceback.format_exc());unreal.unregister_slate_post_tick_callback(state['h']);levels.editor_request_end_play();unreal.SystemLibrary.quit_editor()
state['h']=unreal.register_slate_post_tick_callback(tick);levels.editor_request_start_play(unreal.EditorPlaySimulate.SIMULATE_IN_EDITOR) if False else levels.editor_request_begin_play()

