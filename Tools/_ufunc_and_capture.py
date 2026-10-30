from pathlib import Path
h=Path(r"C:\BeybladeUE\Source\BeybladePrototype\PrototypeBattle.h").read_text(encoding="utf-8")
# Make collection/skill methods BlueprintCallable for capture scripts
repls=[
("    void OpenCollection();", "    UFUNCTION(BlueprintCallable) void OpenCollection();"),
("    void CloseCollection();", "    UFUNCTION(BlueprintCallable) void CloseCollection();"),
("    void SelectCollectionSlot(int32 Index);", "    UFUNCTION(BlueprintCallable) void SelectCollectionSlot(int32 Index);"),
("    void FireActiveSkill();", "    UFUNCTION(BlueprintCallable) void FireActiveSkill();"),
]
for a,b in repls:
    if b not in h and a in h:
        h=h.replace(a,b)
Path(r"C:\BeybladeUE\Source\BeybladePrototype\PrototypeBattle.h").write_text(h,encoding="utf-8")
print("UFUNCTION added", "BlueprintCallable) void OpenCollection" in h)

# Better capture script
Path(r"C:\BeybladeUE\Tools\capture_mesh_collect_skill.py").write_text(r'''# -*- coding: utf-8 -*-
import json, time, traceback
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT = ROOT / "screenshots" / "mesh-collect-skill"
OUT.mkdir(parents=True, exist_ok=True)
LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ST = {"phase": "boot", "t": time.monotonic(), "start": time.monotonic(), "shots": {}, "error": ""}

def world():
    return UES.get_game_world()

def mode():
    return unreal.GameplayStatics.get_game_mode(world())

def pc():
    return unreal.GameplayStatics.get_player_controller(world(), 0)

def shot(name):
    path = str(OUT / (name + ".png")).replace("\\", "/")
    unreal.SystemLibrary.execute_console_command(world(), 'HighResShot 1600x900 filename="' + path + '"', pc())
    ST["shots"][name] = path
    unreal.log("SHOT " + path)

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
        if now - ST["start"] > 150:
            raise RuntimeError("watchdog")
        if ST["phase"] == "boot" and now - ST["t"] > 2:
            assert LEVELS.load_level("/Game/Maps/Main") or LEVELS.load_level("/Game/Maps/StadiumIndustrialPolish_v1")
            LEVELS.editor_request_begin_play()
            ST.update(phase="pie", t=now)
        elif ST["phase"] == "pie" and now - ST["t"] > 6:
            assert world(), "no pie"
            gm = mode()
            assert gm.get_class().get_name() == "PrototypeBattleMode"
            shot("01_lobby")
            gm.open_collection()
            ST.update(phase="grid", t=now)
        elif ST["phase"] == "grid" and now - ST["t"] > 1.2:
            shot("02_collection_grid")
            mode().select_collection_slot(3)
            ST.update(phase="detail", t=now)
        elif ST["phase"] == "detail" and now - ST["t"] > 1.0:
            shot("03_collection_detail")
            mode().close_collection()
            mode().close_collection()
            # Build lineup ChiFeng, BiLei, ChiWen via toggle + confirm
            mode().select_race_mode(5)  # may fail type; try int cast path
            ST.update(phase="pick", t=now)
        elif ST["phase"] == "pick" and now - ST["t"] > 0.5:
            gm = mode()
            # Race enum: use SelectRaceMode from C++ with ERaceMode::RaceTo5 = 5 raw
            try:
                gm.call_method("SelectRaceMode", (5,))
            except Exception:
                pass
            # Prefer known methods
            for fn in ("select_race_mode", "SelectRaceMode"):
                if hasattr(gm, fn):
                    try:
                        getattr(gm, fn)(5)
                    except Exception as e:
                        ST["race_err"] = str(e)
            gm.toggle_pick_slot(0)
            gm.toggle_pick_slot(1)
            gm.toggle_pick_slot(4)
            gm.confirm_pick()
            ST.update(phase="prep", t=now)
        elif ST["phase"] == "prep" and now - ST["t"] > 1.2:
            shot("04_prep")
            mode().launch()
            ST.update(phase="fight", t=now)
        elif ST["phase"] == "fight" and now - ST["t"] > 2.0:
            shot("05_fight_skill_shell")
            # Attempt fire (likely blocked at 0 hits) for log
            try:
                mode().fire_active_skill()
            except Exception as e:
                ST["fire_err"] = str(e)
            ST.update(phase="done", t=now)
        elif ST["phase"] == "done" and now - ST["t"] > 1.0:
            finish(True)
    except Exception:
        ST["error"] = traceback.format_exc()
        unreal.log_error(ST["error"])
        finish(False)

ST["handle"] = unreal.register_slate_post_tick_callback(tick)
''', encoding="utf-8")
print("capture rewritten")
