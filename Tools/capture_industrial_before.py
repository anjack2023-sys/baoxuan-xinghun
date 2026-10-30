# -*- coding: utf-8 -*-
"""Capture BEFORE shots of StadiumIndustrialPolish_v1. No content changes."""
import json, time, traceback
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT = ROOT / "screenshots/grok-art-20261027/before"
OUT.mkdir(parents=True, exist_ok=True)
MAP = "/Game/Maps/StadiumIndustrialPolish_v1"
LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

STATE = {"phase": "start", "time": time.monotonic(), "busy": False, "handle": None, "report": {}}

def inventory():
    rows = []
    for a in ACTORS.get_all_level_actors():
        tags = [str(t) for t in a.tags]
        item = {
            "label": a.get_actor_label(),
            "tags": tags,
            "loc": [a.get_actor_location().x, a.get_actor_location().y, a.get_actor_location().z],
            "scale": [a.get_actor_scale3d().x, a.get_actor_scale3d().y, a.get_actor_scale3d().z],
        }
        mesh = a.get_component_by_class(unreal.StaticMeshComponent)
        if mesh:
            mats = []
            for i in range(mesh.get_num_materials()):
                m = mesh.get_material(i)
                mats.append(m.get_path_name() if m else None)
            item["materials"] = mats
            if mesh.static_mesh:
                item["mesh"] = mesh.static_mesh.get_path_name()
        rows.append(item)
    return rows

def tick(dt):
    if STATE["busy"]:
        return
    STATE["busy"] = True
    try:
        elapsed = time.monotonic() - STATE["time"]
        if STATE["phase"] == "start" and elapsed > 2:
            assert LEVELS.load_level(MAP)
            bowl = next(a for a in ACTORS.get_all_level_actors() if a.get_actor_label() == "SmoothBowl_v1")
            hit = bowl.get_component_by_class(unreal.StaticMeshComponent).line_trace_component(
                unreal.Vector(0, 0, 600), unreal.Vector(0, 0, -200), True, False, False)
            male = next(a for a in ACTORS.get_all_level_actors() if a.get_actor_label() == "MaleLead")
            STATE["report"] = {
                "map": MAP,
                "center_collision_z_cm": hit[0].z if hit else None,
                "character_scale": male.get_actor_scale3d().x,
                "actors": inventory(),
                "face_camera_ini": (ROOT / "Saved/FaceCamera.ini").read_text(encoding="utf-8", errors="ignore"),
            }
            STATE.update(phase="wait_load", time=time.monotonic())
        elif STATE["phase"] == "wait_load" and elapsed > 4:
            LEVELS.editor_request_begin_play()
            STATE.update(phase="wait_pie", time=time.monotonic())
        elif STATE["phase"] == "wait_pie" and elapsed > 8:
            world = UES.get_game_world()
            assert world
            pc = unreal.GameplayStatics.get_player_controller(world, 0)
            unreal.SystemLibrary.execute_console_command(world, "showhud 0", pc)
            path = str(OUT / "stadium_before.png").replace("\\", "/")
            unreal.SystemLibrary.execute_console_command(world, 'HighResShot 1600x900 filename="' + path + '"', pc)
            STATE["report"]["stadium_before"] = path
            STATE.update(phase="hud_on", time=time.monotonic())
        elif STATE["phase"] == "hud_on" and elapsed > 4:
            world = UES.get_game_world()
            pc = unreal.GameplayStatics.get_player_controller(world, 0)
            unreal.SystemLibrary.execute_console_command(world, "showhud 1", pc)
            path = str(OUT / "lobby_or_hud_before.png").replace("\\", "/")
            unreal.SystemLibrary.execute_console_command(world, 'HighResShot 1600x900 filename="' + path + '"', pc)
            STATE["report"]["lobby_before"] = path
            STATE.update(phase="flush", time=time.monotonic())
        elif STATE["phase"] == "flush" and elapsed > 5:
            assert Path(STATE["report"]["stadium_before"]).is_file()
            STATE["report"]["status"] = "PASS"
            (OUT / "before_report.json").write_text(json.dumps(STATE["report"], indent=2), encoding="utf8")
            unreal.unregister_slate_post_tick_callback(STATE["handle"])
            LEVELS.editor_request_end_play()
            unreal.log("GROK_ART_BEFORE_CAPTURE_COMPLETE")
            unreal.SystemLibrary.quit_editor()
    except Exception:
        (OUT / "error.txt").write_text(traceback.format_exc(), encoding="utf8")
        unreal.log_error(traceback.format_exc())
        try:
            unreal.unregister_slate_post_tick_callback(STATE["handle"])
        except Exception:
            pass
        unreal.SystemLibrary.quit_editor()
    finally:
        STATE["busy"] = False

STATE["handle"] = unreal.register_slate_post_tick_callback(tick)
