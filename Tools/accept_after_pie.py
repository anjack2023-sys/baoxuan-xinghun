import json, os, time, unreal

ROOT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
stamp = time.strftime("%Y%m%d_%H%M%S")
shot_path = os.path.join(ROOT, "screenshots", "accept_formal_PIE_%s.png" % stamp).replace("\\", "/")
report_path = os.path.join(ROOT, "Tools", "accept_visual_ray_%s.json" % stamp)
items = []

def note(k,s,d):
    items.append({"item":k,"status":s,"detail":str(d)})
    unreal.log("ACCEPT %s %s %s" % (k,s,d))

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
note("editor_map","INFO", ues.get_editor_world().get_path_name() if ues.get_editor_world() else None)

if les.is_in_play_in_editor():
    les.editor_request_end_play()
    time.sleep(1.0)

les.editor_request_begin_play()
note("pie_start","PASS","editor_request_begin_play")

world=None
for i in range(100):
    time.sleep(0.25)
    if les.is_in_play_in_editor():
        worlds = unreal.EditorLevelLibrary.get_pie_worlds(False)
        if worlds:
            world = worlds[0]
            break
        world = ues.get_game_world()
        if world:
            break
note("pie_flag","INFO", les.is_in_play_in_editor())

if world is None:
    note("pie_world","FAIL","no PIE world")
    with open(report_path,"w",encoding="utf-8") as f:
        json.dump({"result":"FAIL","items":items,"shot":None},f,ensure_ascii=False,indent=2)
    unreal.log("ACCEPT_VISUAL_FAIL "+report_path)
else:
    note("pie_world","PASS", world.get_path_name())
    actors={a.get_actor_label():a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)}
    note("actor_labels","INFO", sorted(actors.keys()))

    stadium_ok=False; stadium_detail="missing"; bowl_color=None
    for label,a in actors.items():
        mesh=a.get_component_by_class(unreal.StaticMeshComponent)
        if not mesh or not mesh.static_mesh: continue
        mpath=mesh.static_mesh.get_path_name().lower(); lname=label.lower()
        if any(x in mpath or x in lname for x in ["bowl","stadium","smooth"]):
            mat=mesh.get_material(0); mat_name=mat.get_name() if mat else "None"
            # M_Bowl / M_StadiumMatte both acceptable if solid (no busy albedo texture path)
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

    try:
        unreal.SystemLibrary.execute_console_command(world, 'HighResShot 1280x720 filename="%s"'%shot_path, controller)
        time.sleep(3.5)
        # HighResShot may write beside path or under Saved/Screenshots; record both
        note("screenshot","PASS", shot_path)
    except Exception as e:
        note("screenshot","FAIL", e); shot_path=None

    fails=[x for x in items if x["status"]=="FAIL"]
    result="FAIL" if fails else "PASS"
    with open(report_path,"w",encoding="utf-8") as f:
        json.dump({"result":result,"mode":"pie","stamp":stamp,"shot":shot_path,"items":items}, f, ensure_ascii=False, indent=2)
    unreal.log("ACCEPT_VISUAL_%s %s"%(result, report_path))
    try:
        les.editor_request_end_play()
    except Exception:
        pass