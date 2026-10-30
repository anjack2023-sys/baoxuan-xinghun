# Pilot BattleCamera + HighResShot + optional brief PIE for runtime camera path
import unreal
import os
import time

_state = {"handle": None, "t0": None, "phase": 0, "flag_seen": None}

def log(m):
    unreal.log("[BeyPolishShot] " + str(m))

def find(label):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in sub.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None

def project_dir():
    return unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())

def force_view_target(cam):
    if not cam:
        return
    try:
        world = unreal.EditorLevelLibrary.get_editor_world()
        pcs = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PlayerController)
        for pc in pcs:
            try:
                pc.set_view_target_with_blend(cam, 0.0)
                log("set_view_target BattleCamera")
            except Exception as e:
                log("view_target: " + str(e))
    except Exception as e:
        log("force_view: " + str(e))
    try:
        unreal.SystemLibrary.execute_console_command(None, "ToggleDebugCamera")
        unreal.SystemLibrary.execute_console_command(None, "ToggleDebugCamera")
    except Exception:
        pass

def on_tick(_dt):
    flag = os.path.join(project_dir(), "Tools", "need_polish_shot.flag")
    if not os.path.isfile(flag):
        return
    # reset if new flag content
    try:
        with open(flag, "r", encoding="utf-8") as f:
            tag = f.read().strip()
    except Exception:
        tag = "x"
    if _state["flag_seen"] != tag:
        _state["flag_seen"] = tag
        _state["t0"] = time.time()
        _state["phase"] = 0
        log("flag found -> schedule polish shots (%s)" % tag)

    elapsed = time.time() - _state["t0"]
    cam = find("BattleCamera")

    if _state["phase"] == 0 and elapsed > 6.0:
        _state["phase"] = 1
        log("pilot BattleCamera")
        try:
            if cam:
                unreal.EditorLevelLibrary.pilot_level_actor(cam)
        except Exception as e:
            log("pilot: " + str(e))
        try:
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_set_game_view(True)
        except Exception:
            pass

    if _state["phase"] == 1 and elapsed > 9.0:
        _state["phase"] = 2
        ascii_dir = r"C:\Users\Administrator\Desktop\beyblade-ue-screenshots"
        os.makedirs(ascii_dir, exist_ok=True)
        os.makedirs(os.path.join(project_dir(), "screenshots"), exist_ok=True)
        base = os.path.join(ascii_dir, "main_polishA_battlecam").replace("\\", "/")
        unreal.SystemLibrary.execute_console_command(None, 'HighResShot 1920x1080 filename="%s.png"' % base)
        try:
            if cam:
                unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, base + "_auto", cam)
                log("AutomationLibrary shot")
        except Exception as e:
            log("auto: " + str(e))
        log("queued " + base)

    if _state["phase"] == 2 and elapsed > 12.0:
        _state["phase"] = 3
        log("start PIE")
        try:
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play()
        except Exception as e:
            log("PIE start: " + str(e))
            try:
                unreal.EditorLevelLibrary.editor_play_in_viewport(False)
            except Exception as e2:
                log("PIE2: " + str(e2))

    if _state["phase"] == 3 and elapsed > 14.5:
        # mid-PIE: force BattleCamera as view target once
        if _state.get("vt_done") != tag:
            _state["vt_done"] = tag
            force_view_target(cam)

    if _state["phase"] == 3 and elapsed > 17.0:
        _state["phase"] = 4
        ascii_dir = r"C:\Users\Administrator\Desktop\beyblade-ue-screenshots"
        base = os.path.join(ascii_dir, "main_polishA_PIE").replace("\\", "/")
        force_view_target(cam)
        unreal.SystemLibrary.execute_console_command(None, 'HighResShot 1920x1080 filename="%s.png"' % base)
        unreal.SystemLibrary.execute_console_command(None, "Shot")
        log("PIE shot queued " + base)
        with open(os.path.join(project_dir(), "Tools", "polish_shot_ready.flag"), "w", encoding="utf-8") as f:
            f.write(str(time.time()))

    if _state["phase"] == 4 and elapsed > 20.0:
        _state["phase"] = 5
        try:
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
        except Exception:
            pass
        try:
            os.remove(flag)
        except Exception:
            pass
        log("done - editor stays open")

def _start():
    _state["handle"] = unreal.register_slate_post_tick_callback(on_tick)
    flag = os.path.join(project_dir(), "Tools", "need_polish_shot.flag")
    if os.path.isfile(flag):
        log("init: polish flag present")

_start()