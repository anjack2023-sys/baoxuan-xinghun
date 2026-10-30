"""Batch-only: save a larger character, capture PIE, then close this editor instance."""
import json
import time
from pathlib import Path
import unreal

root=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
out=root/'screenshots/stadium-game-preview'
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
try:
    assert levels.load_level('/Game/Maps/StadiumIndustrialPreview_v1')
    actor=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label()=='MaleLead')
    origin,extent=actor.get_actor_bounds(False)
    bottom=origin.z-extent.z
    actor.set_actor_scale3d(unreal.Vector(2.165,2.165,2.165))
    new_origin,new_extent=actor.get_actor_bounds(False)
    location=actor.get_actor_location()
    actor.set_actor_location(unreal.Vector(location.x,location.y,location.z+bottom-(new_origin.z-new_extent.z)),False,True)
    assert abs(actor.get_actor_scale3d().x-2.165)<.001
    preview_map='/Game/Maps/StadiumIndustrialCharacter125_v1'
    assert unreal.EditorLoadingAndSavingUtils.save_map(ues.get_editor_world(),preview_map)
    del actor
    assert levels.load_level(preview_map)
except Exception:
    unreal.SystemLibrary.quit_editor()
    raise
state={'phase':0,'time':time.monotonic(),'handle':None,'busy':False}
shot=str(out/'industrial_character_125_PIE.png').replace('\\','/')

def tick(dt):
    if state['busy']:return
    state['busy']=True
    try:
        elapsed=time.monotonic()-state['time']
        if state['phase']==0 and elapsed>3:
            levels.editor_request_begin_play();state.update(phase=1,time=time.monotonic())
        elif state['phase']==1 and elapsed>5:
            world=ues.get_game_world()
            assert world
            pc=unreal.GameplayStatics.get_player_controller(world,0)
            assert pc.get_view_target().actor_has_tag('BattleCamera')
            unreal.SystemLibrary.execute_console_command(world,'showhud',pc)
            state.update(phase=2,time=time.monotonic())
        elif state['phase']==2 and elapsed>3:
            world=ues.get_game_world();pc=unreal.GameplayStatics.get_player_controller(world,0)
            unreal.SystemLibrary.execute_console_command(world,'HighResShot 1600x900 filename="'+shot+'"',pc)
            state.update(phase=3,time=time.monotonic())
        elif state['phase']==3 and elapsed>3:
            assert Path(shot).is_file()
            (out/'character-size.json').write_text(json.dumps({'scale':2.165,'relative_to_original':1.25,'screenshot':shot,'map':preview_map},indent=2),encoding='utf8')
            unreal.unregister_slate_post_tick_callback(state['handle'])
            levels.editor_request_end_play()
            unreal.log('CHARACTER_SIZE_PREVIEW_COMPLETE')
            unreal.SystemLibrary.quit_editor()
    except Exception:
        import traceback
        (out/'character-size-error.txt').write_text(traceback.format_exc(),encoding='utf8')
        unreal.unregister_slate_post_tick_callback(state['handle'])
        unreal.SystemLibrary.quit_editor()
    finally:state['busy']=False

state['handle']=unreal.register_slate_post_tick_callback(tick)
