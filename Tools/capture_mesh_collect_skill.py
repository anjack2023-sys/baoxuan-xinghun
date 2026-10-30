# -*- coding: utf-8 -*-
import json, time, traceback
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT = ROOT / "screenshots" / "mesh-collect-skill"
OUT.mkdir(parents=True, exist_ok=True)
LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ST = {"phase": "boot", "t": time.monotonic(), "start": time.monotonic(), "shots": {}, "error": "", "actions": []}

def world():
    return UES.get_game_world()

def mode():
    return unreal.GameplayStatics.get_game_mode(world())

def pc():
    return unreal.GameplayStatics.get_player_controller(world(), 0)

def inject(name):
    ctrl = pc()
    subsystem = next((s for s in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem)
                      if s.get_outer().get_class().get_name() == "LocalPlayer"), None)
    assert subsystem, "no EIS"
    actions = sorted((a for a in unreal.ObjectIterator(unreal.InputAction) if a.get_outer() == ctrl),
                     key=lambda a: int(a.get_name().rsplit("_", 1)[-1]))
    names = ["launch_action", "reset_action", "mode_race5_action", "mode_race8_action",
             "toggle_mode_action", "pick3_action", "pick4_action", "pick5_action", "click_action"]
    assert len(actions) == len(names), [a.get_name() for a in actions]
    action = actions[names.index(name)]
    subsystem.inject_input_vector_for_action(action, unreal.Vector(1, 0, 0), [], [])
    ST["actions"].append(name)

def shot(name):
    path = str(OUT / (name + ".png")).replace("\\", "/")
    unreal.SystemLibrary.execute_console_command(world(), 'HighResShot 1600x900 filename="' + path + '"', pc())
    ST["shots"][name] = path

def finish(ok):
    ST["status"] = "PASS" if ok else "FAIL"
    (OUT / "report.json").write_text(json.dumps(ST, indent=2, ensure_ascii=False), encoding="utf8")
    try:
        LEVELS.editor_request_end_play()
    except Exception:
        pass
    unreal.SystemLibrary.quit_editor()

def tick(_dt):
    try:
        now = time.monotonic()
        if now - ST["start"] > 180:
            raise RuntimeError("watchdog")
        if ST["phase"] == "boot" and now - ST["t"] > 2:
            assert LEVELS.load_level("/Game/Maps/Main")
            LEVELS.editor_request_begin_play()
            ST.update(phase="pie", t=now)
        elif ST["phase"] == "pie" and now - ST["t"] > 6:
            assert world(), "no pie"
            assert mode().get_class().get_name() == "PrototypeBattleMode"
            shot("01_lobby")
            mode().open_collection()
            ST.update(phase="grid", t=now)
        elif ST["phase"] == "grid" and now - ST["t"] > 1.2:
            shot("02_collection_grid")
            mode().select_collection_slot(3)
            ST.update(phase="detail", t=now)
        elif ST["phase"] == "detail" and now - ST["t"] > 1.0:
            shot("03_collection_detail")
            mode().close_collection()
            mode().close_collection()
            ST.update(phase="to_pick", t=now)
        elif ST["phase"] == "to_pick" and now - ST["t"] > 0.8:
            inject("mode_race5_action")
            inject("launch_action")  # lobby -> pick
            ST.update(phase="pick", t=now)
        elif ST["phase"] == "pick" and now - ST["t"] > 1.0:
            shot("04_pick")
            inject("launch_action")  # may confirm if 3 selected - first select via keys
            # pick slots: PickSlot0/1 via click not available; use pick3/4/5 = slots 2,3,4
            # Also need 0,1 - without click hard. Use launch after selecting 2,3,4 only won't confirm.
            # Select via repeated: mode has TogglePickSlot not exposed.
            # Fall back: inject pick3, pick4, pick5 then launch confirm
            inject("pick3_action")
            inject("pick4_action")
            inject("pick5_action")
            ST.update(phase="pick2", t=now)
        elif ST["phase"] == "pick2" and now - ST["t"] > 0.8:
            shot("05_pick_lineup")
            inject("launch_action")  # confirm pick
            ST.update(phase="prep", t=now)
        elif ST["phase"] == "prep" and now - ST["t"] > 1.2:
            shot("06_prep")
            inject("launch_action")  # start fight
            ST.update(phase="fight", t=now)
        elif ST["phase"] == "fight" and now - ST["t"] > 2.5:
            shot("07_fight_skill_shell")
            try:
                mode().fire_active_skill()
            except Exception as e:
                ST["fire_err"] = str(e)
            ST.update(phase="done", t=now)
        elif ST["phase"] == "done" and now - ST["t"] > 1.2:
            finish(True)
    except Exception:
        ST["error"] = traceback.format_exc()
        unreal.log_error(ST["error"])
        finish(False)

ST["handle"] = unreal.register_slate_post_tick_callback(tick)
