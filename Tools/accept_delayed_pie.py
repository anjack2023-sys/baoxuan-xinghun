import json, os, time, unreal

ROOT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
STATE = {"frames": 0, "phase": "wait_idle", "stamp": None, "shot": None, "items": [], "handle": None}

def note(k,s,d):
    STATE["items"].append({"item":k,"status":s,"detail":str(d)})
    unreal.log("ACCEPT %s %s %s" % (k,s,d))

def finish(result):
    report_path = os.path.join(ROOT, "Tools", "accept_visual_ray_%s.json" % STATE["stamp"])
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"result": result, "mode": "pie", "stamp": STATE["stamp"], "shot": STATE["shot"], "items": STATE["items"]}, f, ensure_ascii=False, indent=2)
    unreal.log("ACCEPT_VISUAL_%s %s" % (result, report_path))
    try:
        unreal.unregister_slate_post_tick_callback(STATE["handle"])
    except Exception:
        pass
    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
    except Exception:
        pass

def run_checks():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    worlds = unreal.EditorLevelLibrary.get_pie_worlds(False)
    world = worlds[0] if worlds else ues.get_game_world()
    if world is None:
        note("pie_world", "FAIL", "no PIE world after delay")
        finish("FAIL"); return
    note("pie_world", "PASS", world.get_path_name())
    actors = {a.get_actor_label(): a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)}
    note("actor_labels", "INFO", sorted(actors.keys()))

    stadium_ok=False; stadium_detail="missing"
    for label,a in actors.items():
        mesh=a.get_component_by_class(unreal.StaticMeshComponent)
        if not mesh or not mesh.static_mesh: continue
        mpath=mesh.static_mesh.get_path_name().lower(); lname=label.lower()
        if any(x in mpath or x in lname for x in ["bowl","stadium","smooth"]):
            mat=mesh.get_material(0); mat_name=mat.get_name() if mat else "None"
            stadium_ok = mat_name in ("M_Bowl","M_StadiumMatte","M_Stadium") or ("matte" in mat_name.lower()) or ("bowl" in mat_name.lower())
            stadium_detail="actor=%s mesh=%s mat=%s"%(label, mesh.static_mesh.get_name(), mat_name)
            break
    note("stadium_matte", "PASS" if stadium_ok else "FAIL", stadium_detail)

    widths=[]
    for name in ["BeyA_RedLotus","BeyB"]:
        bey=actors.get(name)
        if not bey:
            note("tops_"+name,"FAIL","missing"); continue
        c=bey.get_component_by_class(unreal.StaticMeshComponent)
        b=c.static_mesh.get_bounds(); sc=bey.get_actor_scale3d()
        width=max(b.box_extent.x*sc.x, b.box_extent.y*sc.y)*2
        widths.append(width)
        pivot_ok=abs(b.origin.x)<0.05 and abs(b.origin.y)<0.05
        mat=c.get_material(0); mat_name=mat.get_name() if mat else "None"
        note("tops_"+name, "PASS" if abs(width-44)<0.5 and pivot_ok else "FAIL",
             "diam=%.2f pivot_ok=%s mat=%s"%(width,pivot_ok,mat_name))
    if len(widths)==2:
        note("tops_same_diameter","PASS" if abs(widths[0]-widths[1])<0.5 else "FAIL", widths)

    for index, bey_name in enumerate(["BeyA_RedLotus","BeyB"],1):
        ln="Label_P%d"%index; label=actors.get(ln); bey=actors.get(bey_name)
        if not label or not bey:
            note(ln,"FAIL","missing"); continue
        parent=label.get_attach_parent_actor()
        tr=label.get_component_by_class(unreal.TextRenderComponent)
        ws=tr.get_editor_property("world_size") if tr else None
        ok=(parent==bey) and (ws is not None) and float(ws)<=30
        note(ln,"PASS" if ok else "FAIL","parent=%s ws=%s"%(parent.get_actor_label() if parent else None, ws))

    male=None
    for label,a in actors.items():
        low=label.lower()
        if any(x in low for x in ["male","lead","character","clean"]):
            male=a; break
    if male is None:
        for label,a in actors.items():
            if a.get_component_by_class(unreal.SkeletalMeshComponent):
                male=a; break
    note("male_lead","PASS" if male else "FAIL", ("label=%s loc=%s"%(male.get_actor_label(), male.get_actor_location())) if male else "missing")

    controller=unreal.GameplayStatics.get_player_controller(world,0)
    view=controller.get_view_target() if controller else None
    view_label=view.get_actor_label() if view else None
    note("battle_camera","PASS" if view_label=="BattleCamera" else "FAIL","view_target=%s"%view_label)
    cam=actors.get("BattleCamera")
    if cam and cam.camera_component:
        try:
            note("camera_fov","INFO", cam.camera_component.get_editor_property("field_of_view"))
        except Exception as e:
            note("camera_fov","WARN", e)

    shot_path = os.path.join(ROOT, "screenshots", "accept_formal_PIE_%s.png" % STATE["stamp"]).replace("\\", "/")
    try:
        unreal.SystemLibrary.execute_console_command(world, 'HighResShot 1280x720 filename="%s"'%shot_path, controller)
        STATE["shot"] = shot_path
        note("screenshot","PASS", shot_path)
    except Exception as e:
        note("screenshot","FAIL", e)

    STATE["phase"] = "flush_shot"
    STATE["frames"] = 0

def on_tick(delta):
    STATE["frames"] += 1
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if STATE["phase"] == "wait_idle":
        if STATE["frames"] < 180:
            return True
        STATE["stamp"] = time.strftime("%Y%m%d_%H%M%S")
        note("delay","INFO","frames=%s starting PIE"%STATE["frames"])
        try:
            les.editor_request_begin_play()
            note("pie_start","PASS","editor_request_begin_play")
        except Exception as e:
            note("pie_start","FAIL",e)
            finish("FAIL"); return False
        STATE["phase"] = "wait_pie"
        STATE["frames"] = 0
        return True
    if STATE["phase"] == "wait_pie":
        if les.is_in_play_in_editor() or unreal.EditorLevelLibrary.get_pie_worlds(False):
            note("pie_ready","PASS","frames=%s"%STATE["frames"])
            STATE["phase"] = "checks"
            STATE["frames"] = 0
            return True
        if STATE["frames"] > 600:
            note("pie_world","FAIL","timeout waiting PIE")
            finish("FAIL"); return False
        return True
    if STATE["phase"] == "checks":
        if STATE["frames"] < 20:
            return True
        try:
            run_checks()
        except Exception as e:
            note("checks","FAIL",e)
            finish("FAIL"); return False
        return True
    if STATE["phase"] == "flush_shot":
        if STATE["frames"] < 90:
            return True
        fails=[x for x in STATE["items"] if x["status"]=="FAIL"]
        finish("FAIL" if fails else "PASS")
        return False
    return True

STATE["handle"] = unreal.register_slate_post_tick_callback(on_tick)
unreal.log("ACCEPT_DELAYED_ARMED")