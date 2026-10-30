"""QA harness: start saved Main Play, then capture a real ringout after pressing SPACE."""
import os
import time
import unreal

assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level("/Game/Maps/Main")
_capture_started = time.monotonic()
_capture_handle = None

def _capture_tick(delta):
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if world:
        beys = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor)
        for bey in beys:
            if bey.actor_has_tag("BattleP1"):
                p = bey.get_actor_location()
                if p.z < 1 and p.x*p.x + p.y*p.y > 270*270:
                    unreal.unregister_slate_post_tick_callback(_capture_handle)
                    path = os.path.join(unreal.Paths.project_dir(), "Tools", "verify_ringout_pie.py")
                    with open(path, encoding="utf-8") as f:
                        exec(compile(f.read(), path, "exec"), {})
                    return
    if time.monotonic() - _capture_started > 120:
        unreal.unregister_slate_post_tick_callback(_capture_handle)
        unreal.log_error("Ringout capture timed out: press SPACE in Main PIE with -ProtoSeed=4242")

_capture_handle = unreal.register_slate_post_tick_callback(_capture_tick)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play()
