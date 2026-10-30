import unreal,json,traceback,time
from pathlib import Path
r=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
started=time.monotonic()
state={'handle':None,'shots':set(),'samples':[],'world':None,'done':False}
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert levels.load_level('/Game/Maps/StadiumIndustrialPolish_v1')
def tick(dt):
    try:
        assert time.monotonic()-started<130,"PIE check timed out"
        worlds=unreal.EditorLevelLibrary.get_pie_worlds(False)
        if not worlds:return
        world=worlds[0];t=unreal.GameplayStatics.get_time_seconds(world)
        if t>.9 and 'action' not in state['shots']:
            state['shots'].add('action')
            person=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor) if 'FaceCameraCharacter' in [str(tag) for tag in a.tags])
            pose=person.get_component_by_class(unreal.PoseableMeshComponent)
            assert pose and pose.get_num_bones()==41
            state['samples'].append({'t':t,'arm':str(pose.get_bone_rotation_by_name('L_Upperarm',unreal.BoneSpaces.COMPONENT_SPACE)),'bones':pose.get_num_bones()})
            unreal.SystemLibrary.execute_console_command(world,'HighResShot 1280x720 filename="'+str(r/'Saved/launch-action.png')+'"',unreal.GameplayStatics.get_player_controller(world,0))
        if t>3.1 and 'battle' not in state['shots']:
            state['shots'].add('battle')
            unreal.SystemLibrary.execute_console_command(world,'HighResShot 1280x720 filename="'+str(r/'Saved/launch-battle.png')+'"',unreal.GameplayStatics.get_player_controller(world,0))
        if t>70. and 'recap' not in state['shots']:
            state['shots'].add('recap')
            unreal.SystemLibrary.execute_console_command(world,'HighResShot 1280x720 filename="'+str(r/'Saved/launch-recap.png')+'"',unreal.GameplayStatics.get_player_controller(world,0))
        if t>73.:
            (r/'Saved/launch-presentation-report.json').write_text(json.dumps({'status':'PASS','samples':state['samples'],'shots':list(state['shots'])},indent=2))
            unreal.unregister_slate_post_tick_callback(state['handle']);levels.editor_request_end_play();unreal.SystemLibrary.quit_editor()
    except Exception:
        (r/'Saved/launch-presentation-report.json').write_text(json.dumps({'status':'FAIL','error':traceback.format_exc()}))
        unreal.unregister_slate_post_tick_callback(state['handle']);levels.editor_request_end_play();unreal.SystemLibrary.quit_editor()
state['handle']=unreal.register_slate_post_tick_callback(tick)
levels.editor_request_begin_play()
