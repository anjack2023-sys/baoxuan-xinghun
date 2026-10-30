"""Formal Main PIE: ringout land + R reset + feel notes. Does not change freeze params."""
import json, os, time, unreal

ROOT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
ST = {"phase": "boot", "frames": 0, "handle": None, "items": [], "stamp": time.strftime("%Y%m%d_%H%M%S"),
      "land_shot": None, "reset_shot": None, "loser_z": None, "ready_pos": None}

def note(k, s, d):
    ST["items"].append({"item": k, "status": s, "detail": str(d)})
    unreal.log("RINGOUT_ACCEPT %s %s %s" % (k, s, d))

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
    report = os.path.join(ROOT, "Tools", "accept_ringout_feel_%s.json" % ST["stamp"])
    with open(report, "w", encoding="utf-8") as f:
        json.dump({"result": result, "stamp": ST["stamp"], "land_shot": ST["land_shot"],
                   "reset_shot": ST["reset_shot"], "loser_z": ST["loser_z"],
                   "ready_pos": ST["ready_pos"], "items": ST["items"]}, f, ensure_ascii=False, indent=2)
    unreal.log("RINGOUT_ACCEPT_%s %s" % (result, report))
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
            if ST["frames"] < 120:
                return True
            assert les.load_level("/Game/Maps/Main")
            note("load_main", "PASS", "/Game/Maps/Main")
            les.editor_request_begin_play()
            ST["phase"] = "wait_pie"; ST["frames"] = 0
            return True

        if ST["phase"] == "wait_pie":
            if les.is_in_play_in_editor() or unreal.EditorLevelLibrary.get_pie_worlds(False):
                note("pie", "PASS", "frames=%s" % ST["frames"])
                ST["phase"] = "ready_settle"; ST["frames"] = 0
                return True
            if ST["frames"] > 900:
                note("pie", "FAIL", "timeout"); finish("FAIL"); return False
            return True

        if ST["phase"] == "ready_settle":
            if ST["frames"] < 45:
                return True
            w = world(); pc = unreal.GameplayStatics.get_player_controller(w, 0)
            mode = unreal.GameplayStatics.get_game_mode(w)
            note("game_mode", "PASS" if mode and mode.get_class().get_name()=="PrototypeBattleMode" else "FAIL",
                 mode.get_class().get_name() if mode else None)
            view = pc.get_view_target() if pc else None
            note("battle_camera", "PASS" if view and view.actor_has_tag("BattleCamera") else "FAIL",
                 view.get_actor_label() if view else None)
            a = actors(w)
            ST["ready_pos"] = {
                "p1": [a["BeyA_RedLotus"].get_actor_location().x, a["BeyA_RedLotus"].get_actor_location().y, a["BeyA_RedLotus"].get_actor_location().z],
                "p2": [a["BeyB"].get_actor_location().x, a["BeyB"].get_actor_location().y, a["BeyB"].get_actor_location().z],
            }
            press(pc, "SpaceBar")
            note("launch", "PASS", "SpaceBar")
            ST["phase"] = "wait_land"; ST["frames"] = 0
            return True

        if ST["phase"] == "wait_land":
            w = world(); a = actors(w)
            # seed 4242 match1: P1 loses, lands outside rim
            for label in ("BeyA_RedLotus", "BeyB"):
                p = a[label].get_actor_location()
                r = (p.x*p.x + p.y*p.y) ** 0.5
                if p.z < 2.0 and r > 270:
                    ST["loser_z"] = p.z
                    note("ringout_land", "PASS" if abs(p.z - 0.5) < 1.5 else "FAIL",
                         "label=%s xyz=(%.2f,%.2f,%.2f) r=%.1f" % (label, p.x, p.y, p.z, r))
                    # confirm not mid-air freeze (bowl height ~42-107cm)
                    note("not_midair", "PASS" if p.z < 20 else "FAIL", "z_cm=%.2f" % p.z)
                    pc = unreal.GameplayStatics.get_player_controller(w, 0)
                    ST["land_shot"] = shot(w, pc, "accept_ringout_landed_%s.png" % ST["stamp"])
                    note("land_shot", "PASS", ST["land_shot"])
                    ST["phase"] = "flush_land"; ST["frames"] = 0
                    return True
            if ST["frames"] > 60 * 25:  # ~25s wall
                # dump positions for diagnosis
                dump = {k: [a[k].get_actor_location().x, a[k].get_actor_location().y, a[k].get_actor_location().z]
                        for k in ("BeyA_RedLotus", "BeyB") if k in a}
                note("ringout_land", "FAIL", "timeout dump=%s" % dump)
                finish("FAIL"); return False
            return True

        if ST["phase"] == "flush_land":
            if ST["frames"] < 60:
                return True
            w = world(); pc = unreal.GameplayStatics.get_player_controller(w, 0)
            press(pc, "R")
            note("reset_key", "PASS", "R")
            ST["phase"] = "check_reset"; ST["frames"] = 0
            return True

        if ST["phase"] == "check_reset":
            if ST["frames"] < 30:
                return True
            w = world(); a = actors(w); pc = unreal.GameplayStatics.get_player_controller(w, 0)
            p1 = a["BeyA_RedLotus"].get_actor_location()
            p2 = a["BeyB"].get_actor_location()
            # ready spawn ~ (-85,10) and (85,-10) cm-ish from sim metres*100; height on bowl ~42cm
            ok1 = abs(p1.x - ST["ready_pos"]["p1"][0]) < 5 and abs(p1.y - ST["ready_pos"]["p1"][1]) < 5
            ok2 = abs(p2.x - ST["ready_pos"]["p2"][0]) < 5 and abs(p2.y - ST["ready_pos"]["p2"][1]) < 5
            on_bowl = p1.z > 30 and p2.z > 30  # back on bowl surface, not floor 0.5
            note("reset_pos", "PASS" if ok1 and ok2 else "FAIL",
                 "p1=(%.1f,%.1f,%.1f) p2=(%.1f,%.1f,%.1f) ready=%s" % (p1.x,p1.y,p1.z,p2.x,p2.y,p2.z, ST["ready_pos"]))
            note("reset_on_bowl", "PASS" if on_bowl else "FAIL", "z1=%.1f z2=%.1f" % (p1.z, p2.z))
            ST["reset_shot"] = shot(w, pc, "accept_ringout_reset_%s.png" % ST["stamp"])
            note("reset_shot", "PASS", ST["reset_shot"])
            ST["phase"] = "flush_reset"; ST["frames"] = 0
            return True

        if ST["phase"] == "flush_reset":
            if ST["frames"] < 90:
                return True
            fails = [x for x in ST["items"] if x["status"] == "FAIL"]
            finish("FAIL" if fails else "PASS")
            return False
    except Exception as e:
        note("exception", "FAIL", e)
        finish("FAIL")
        return False
    return True

ST["handle"] = unreal.register_slate_post_tick_callback(on_tick)
unreal.log("RINGOUT_ACCEPT_ARMED stamp=%s" % ST["stamp"])
