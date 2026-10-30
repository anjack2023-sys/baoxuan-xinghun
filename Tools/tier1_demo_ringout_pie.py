"""Tier1: PIE with -ProtoDemoRingout. Capture landed frame + verify lock window."""
import json, os, time, unreal

ROOT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
ST = {"phase": "boot", "frames": 0, "handle": None, "items": [], "stamp": time.strftime("%Y%m%d_%H%M%S")}

def note(k, s, d):
    ST["items"].append({"item": k, "status": s, "detail": str(d)})
    unreal.log("TIER1 %s %s %s" % (k, s, d))

def world():
    worlds = unreal.EditorLevelLibrary.get_pie_worlds(False)
    if worlds:
        return worlds[0]
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()

def actors(w):
    return {a.get_actor_label(): a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor)}

def press(pc, key_name):
    key = unreal.Key(key_name)
    pc.input_key(key, unreal.EInputEvent.IE_PRESSED, 1.0, False)
    pc.input_key(key, unreal.EInputEvent.IE_RELEASED, 0.0, False)

def shot(w, pc, name):
    path = os.path.join(ROOT, "screenshots", name).replace("\\", "/")
    unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720 filename="%s"' % path, pc)
    return path

def finish(result):
    report = os.path.join(ROOT, "Tools", "tier1_demo_ringout_%s.json" % ST["stamp"])
    with open(report, "w", encoding="utf-8") as f:
        json.dump({"result": result, "stamp": ST["stamp"], "items": ST["items"],
                   "land_shot": ST.get("land_shot"), "spam_shot": ST.get("spam_shot")}, f, ensure_ascii=False, indent=2)
    unreal.log("TIER1_%s %s" % (result, report))
    try:
        unreal.unregister_slate_post_tick_callback(ST["handle"])
    except Exception:
        pass
    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
    except Exception:
        pass

def on_tick(delta):
    ST["frames"] += 1
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    try:
        if ST["phase"] == "boot":
            if ST["frames"] < 90:
                return True
            assert les.load_level("/Game/Maps/Main")
            note("load_main", "PASS", "/Game/Maps/Main")
            les.editor_request_begin_play()
            ST["phase"] = "wait_pie"; ST["frames"] = 0
            return True

        if ST["phase"] == "wait_pie":
            if les.is_in_play_in_editor() or unreal.EditorLevelLibrary.get_pie_worlds(False):
                note("pie", "PASS", "frames=%s" % ST["frames"])
                ST["phase"] = "launch"; ST["frames"] = 0
                return True
            if ST["frames"] > 900:
                note("pie", "FAIL", "timeout"); finish("FAIL"); return False
            return True

        if ST["phase"] == "launch":
            if ST["frames"] < 45:
                return True
            w = world(); pc = unreal.GameplayStatics.get_player_controller(w, 0)
            press(pc, "SpaceBar")
            note("launch", "PASS", "SpaceBar")
            ST["phase"] = "wait_land"; ST["frames"] = 0
            return True

        if ST["phase"] == "wait_land":
            w = world(); a = actors(w); pc = unreal.GameplayStatics.get_player_controller(w, 0)
            # Spam SPACE during expected fall window to verify lock (should not rematch early).
            if 30 <= ST["frames"] <= 90:
                press(pc, "SpaceBar")
            for label in ("BeyA_RedLotus", "BeyB"):
                p = a[label].get_actor_location()
                r = (p.x * p.x + p.y * p.y) ** 0.5
                if p.z < 5.0 and r >= 300.0:
                    ST["loser"] = label
                    ST["loser_xyz"] = [p.x, p.y, p.z]
                    ST["loser_r"] = r
                    note("ringout_land", "PASS", "label=%s r=%.1f z=%.2f" % (label, r, p.z))
                    # Winner should be the other bey, still roughly in bowl
                    other = "BeyB" if label == "BeyA_RedLotus" else "BeyA_RedLotus"
                    wp = a[other].get_actor_location()
                    wr = (wp.x * wp.x + wp.y * wp.y) ** 0.5
                    note("winner_inside", "PASS" if wr < 220 else "FAIL", "label=%s r=%.1f" % (other, wr))
                    ST["land_shot"] = shot(w, pc, "tier1_ringout_landed_PIE.png")
                    # Keep spamming SPACE a bit more; if lock works, still landed next frames
                    ST["phase"] = "spam_lock"; ST["frames"] = 0
                    return True
            if ST["frames"] > 600:
                note("ringout_land", "FAIL", "no land within timeout (need -ProtoDemoRingout on editor cmdline)")
                finish("FAIL"); return False
            return True

        if ST["phase"] == "spam_lock":
            w = world(); a = actors(w); pc = unreal.GameplayStatics.get_player_controller(w, 0)
            press(pc, "SpaceBar")
            press(pc, "R")
            if ST["frames"] < 45:
                return True
            p = a[ST["loser"]].get_actor_location()
            r = (p.x * p.x + p.y * p.y) ** 0.5
            # Still outside + low = presentation finished or still holding landed pose (not rematched to ready spawn)
            still = r >= 270 and p.z < 30
            note("input_lock_or_settled", "PASS" if still else "WARN", "after_spam r=%.1f z=%.2f" % (r, p.z))
            ST["spam_shot"] = shot(w, pc, "tier1_after_space_spam_PIE.png")
            fails = [i for i in ST["items"] if i["status"] == "FAIL"]
            finish("FAIL" if fails else "PASS")
            return False
        return True
    except Exception as e:
        note("exception", "FAIL", repr(e))
        finish("FAIL")
        return False

ST["handle"] = unreal.register_slate_post_tick_callback(on_tick)
unreal.log("TIER1_SCRIPT_LOADED")
