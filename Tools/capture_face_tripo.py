"""Reuse the full-match QA; add imported meshes and editable face-camera checks."""
from pathlib import Path
import unreal

root=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
source=(root/'Tools/capture_p3_ui.py').read_text(encoding='utf8')
source=source.replace("screenshots/P3-UI", "screenshots/Face-Tripo")
source=source.replace("(.7,'input','pick3_action')", "(.7,'input','pick4_action')")
source=source.replace("(.5,'input','pick5_action')", "(.5,'input','mode_race5_action')")
source=source.replace("(.8,'input','mode_race5_action')", "(.8,'input','pick3_action')")
exec(compile(source,str(root/'Tools/capture_p3_ui.py'),'exec'),globals())
base_capture=capture
base_finish=finish
config=root/'Saved/FaceCamera.ini'
original_config=config.read_bytes() if config.exists() else None
config.write_text('[FaceCamera]\nPitch=-18\nHeight=0\nLocked=False\n',encoding='utf8')

def restore_and_finish(ok):
    if original_config is None:
        if config.exists():config.unlink()
    else:config.write_bytes(original_config)
    base_finish(ok)

reload_state={'phase':'idle','t':0,'handle':None}
def reload_tick(dt):
    try:
        elapsed=time.monotonic()-reload_state['t']
        if reload_state['phase']=='stop' and elapsed>2:
            LEVELS.editor_request_begin_play()
            reload_state.update(phase='start',t=time.monotonic())
        elif reload_state['phase']=='start' and elapsed>5:
            unreal.GameplayStatics.get_game_mode(world()).toggle_face_view()
            reload_state.update(phase='check',t=time.monotonic())
        elif reload_state['phase']=='check' and elapsed>2:
            camera=controller().get_view_target()
            assert abs(camera.get_actor_rotation().pitch+80)<2,'Saved pitch not restored'
            assert camera.get_actor_location().z>300,'Saved height not restored'
            ST['camera_reload']='PASS'
            unreal.unregister_slate_post_tick_callback(reload_state['handle'])
            restore_and_finish(True)
    except Exception:
        ST['error']=traceback.format_exc()
        unreal.unregister_slate_post_tick_callback(reload_state['handle'])
        restore_and_finish(False)

def finish(ok):
    if not ok:
        restore_and_finish(False)
        return
    assert all('/SM_'+n in logs() for n in ('Chifeng','Bilei','Hengren')),'Not all three tops appeared'
    LEVELS.editor_request_end_play()
    ST['phase']='reload_camera'
    reload_state.update(phase='stop',t=time.monotonic())
    reload_state['handle']=unreal.register_slate_post_tick_callback(reload_tick)

def capture(name):
    mode=unreal.GameplayStatics.get_game_mode(world())
    camera=controller().get_view_target()
    if name=='face_enable':
        mode.toggle_face_view()
        mode.adjust_face_view(-1000,1000)
        mode.lock_face_view()
        mode.adjust_face_view(1000,-1000)
        return
    if name=='face_clamped':
        assert abs(camera.get_actor_rotation().pitch+80)<2,'Pitch clamp/lock failed'
        assert camera.get_actor_location().z>300,'Height clamp/lock failed'
        assert config.exists(),'Camera settings were not saved'
        base_capture(name)
        mode.lock_face_view()
        mode.adjust_face_view(56,-305)
        return
    if name=='face_adjusted':
        assert abs(camera.get_actor_rotation().pitch+24)<3,'Face pitch did not adjust'
        assert 230<camera.get_actor_location().z<270,'Face height did not adjust'
    if name=='face_return':
        mode.toggle_face_view()
        return
    base_capture(name)
    if name=='04_battle':
        art=[c for c in unreal.ObjectIterator(unreal.StaticMeshComponent)
             if c.get_owner() and c.get_owner().get_path_name().startswith(world().get_path_name())
             and c.static_mesh and '/Art/Tripo_v1/' in c.static_mesh.get_path_name()]
        assert len(art)==2,'Expected two imported tops in battle'
        for c in art:
            assert c.get_collision_enabled()==unreal.CollisionEnabled.NO_COLLISION
        ST['queue'][0:0]=[(.5,'shot','face_enable'),(1.8,'shot','face_clamped'),
                         (1.8,'shot','face_adjusted'),(.5,'shot','face_return')]
