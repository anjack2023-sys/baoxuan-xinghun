import json, os, time, unreal

ROOT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
stamp = time.strftime("%Y%m%d_%H%M%S")
report_path = os.path.join(ROOT, "Tools", "accept_visual_ray_%s.json" % stamp)
shot_path = os.path.join(ROOT, "screenshots", "accept_formal_PIE_%s.png" % stamp).replace("\\", "/")
os.makedirs(os.path.join(ROOT, "screenshots"), exist_ok=True)
items = []

def note(k,s,d):
    items.append({"item":k,"status":s,"detail":str(d)})
    unreal.log("ACCEPT %s %s %s" % (k,s,d))

# discover play APIs
play_apis = []
for name in dir(unreal.EditorLevelLibrary):
    low = name.lower()
    if ("play" in low) or ("simulate" in low) or ("pie" in low):
        play_apis.append("EditorLevelLibrary."+name)
les = None
try:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    for name in dir(les):
        low = name.lower()
        if ("play" in low) or ("simulate" in low) or ("pie" in low) or ("session" in low):
            play_apis.append("LevelEditorSubsystem."+name)
except Exception as e:
    note("les", "WARN", e)
note("play_apis", "INFO", play_apis)
with open(os.path.join(ROOT, "Tools", "play_api_probe.json"), "w", encoding="utf-8") as f:
    json.dump({"play_apis": play_apis}, f, indent=2)

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
path = ues.get_editor_world().get_path_name() if ues.get_editor_world() else ""
note("editor_map", "INFO", path)
if "Main" not in path and les:
    try:
        les.load_level("/Game/Maps/Main")
    except Exception as e:
        note("load_main", "WARN", e)

# try play methods in preferred order
preferred = [
    "editor_request_fullscreen_play_session",
    "editor_request_play_session",
    "request_play_session",
    "start_play_in_editor_session",
    "editor_play_session",
    "play_in_editor",
    "editor_play_simulate",
    "pilot_level_at",
]
started = False
# try LevelEditorSubsystem methods first
if les:
    for name in preferred:
        if hasattr(les, name):
            try:
                fn = getattr(les, name)
                fn()
                started = True
                note("pie_start", "PASS", "LevelEditorSubsystem."+name)
                break
            except Exception as e:
                note("pie_try", "WARN", "LevelEditorSubsystem.%s: %s" % (name, e))
    if not started:
        for name in dir(les):
            low = name.lower()
            if low.startswith("_"):
                continue
            if ("play" in low) and ("session" in low or "editor" in low or low.endswith("play")):
                try:
                    getattr(les, name)()
                    started = True
                    note("pie_start", "PASS", "LevelEditorSubsystem."+name)
                    break
                except TypeError as e:
                    # maybe needs args
                    note("pie_try", "WARN", "LevelEditorSubsystem.%s TypeError: %s" % (name, e))
                except Exception as e:
                    note("pie_try", "WARN", "LevelEditorSubsystem.%s: %s" % (name, e))

if not started:
    for name in preferred:
        if hasattr(unreal.EditorLevelLibrary, name):
            try:
                getattr(unreal.EditorLevelLibrary, name)()
                started = True
                note("pie_start", "PASS", "EditorLevelLibrary."+name)
                break
            except Exception as e:
                note("pie_try", "WARN", "EditorLevelLibrary.%s: %s" % (name, e))

world = None
for i in range(100):
    time.sleep(0.2)
    world = ues.get_game_world()
    if world is not None:
        break

if world is None:
    # fallback: verify editor world actors + take editor viewport shot via AutomationLibrary if possible
    note("pie_world", "FAIL", "no game world; falling back to editor-world structural check")
    world = ues.get_editor_world()
    mode = "editor"
else:
    note("pie_world", "PASS", world.get_path_name())
    mode = "pie"

actors = {a.get_actor_label(): a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)}
note("actor_labels", "INFO", sorted(actors.keys()))

# stadium
stadium_ok=False; stadium_detail="missing"
for label,a in actors.items():
    mesh=a.get_component_by_class(unreal.StaticMeshComponent)
    if not mesh or not mesh.static_mesh: continue
    mpath=mesh.static_mesh.get_path_name().lower(); lname=label.lower()
    if any(x in mpath or x in lname for x in ["bowl","stadium","smooth"]):
        mat=mesh.get_material(0); mat_name=mat.get_name() if mat else "None"
        stadium_ok=("matte" in mat_name.lower()) or ("stadium" in mat_name.lower())
        stadium_detail="actor=%s mesh=%s mat=%s"%(label, mesh.static_mesh.get_name(), mat_name)
        break
note("stadium_matte", "PASS" if stadium_ok else "WARN", stadium_detail)

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
    note("tops_"+name, "PASS" if abs(width-44)<0.5 and pivot_ok else "FAIL", "diam=%.2f pivot_ok=%s mat=%s"%(width,pivot_ok,mat_name))
if len(widths)==2:
    note("tops_same_diameter", "PASS" if abs(widths[0]-widths[1])<0.5 else "FAIL", widths)

for index, bey_name in enumerate(["BeyA_RedLotus","BeyB"],1):
    ln="Label_P%d"%index; label=actors.get(ln); bey=actors.get(bey_name)
    if not label or not bey:
        note(ln,"FAIL","missing"); continue
    parent=label.get_attach_parent_actor()
    tr=label.get_component_by_class(unreal.TextRenderComponent)
    ws=tr.get_editor_property("world_size") if tr else None
    ok=(parent==bey) and (ws is not None) and float(ws)<=30
    note(ln, "PASS" if ok else "FAIL", "parent=%s ws=%s"%(parent.get_actor_label() if parent else None, ws))

male=None
for label,a in actors.items():
    low=label.lower()
    if any(x in low for x in ["male","lead","character","clean"]):
        male=a; break
if male is None:
    for label,a in actors.items():
        if a.get_component_by_class(unreal.SkeletalMeshComponent):
            male=a; break
note("male_lead", "PASS" if male else "FAIL", ("label=%s loc=%s"%(male.get_actor_label(), male.get_actor_location())) if male else "missing")

controller=unreal.GameplayStatics.get_player_controller(world,0) if mode=="pie" else None
view_label=None
if controller:
    view=controller.get_view_target()
    view_label=view.get_actor_label() if view else None
    note("battle_camera", "PASS" if view_label=="BattleCamera" else "FAIL", "view_target=%s"%view_label)
else:
    cam=actors.get("BattleCamera")
    note("battle_camera", "WARN" if cam else "FAIL", "no PIE controller; BattleCamera present=%s"%(cam is not None))
    if cam and cam.camera_component:
        try:
            # activate for screenshot intent
            cam.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)
        except Exception:
            pass

# FOV info
cam=actors.get("BattleCamera")
if cam and cam.camera_component:
    try:
        note("camera_fov","INFO", cam.camera_component.get_editor_property("field_of_view"))
    except Exception as e:
        note("camera_fov","WARN",e)

# screenshot
try:
    if mode=="pie" and controller:
        unreal.SystemLibrary.execute_console_command(world, 'HighResShot 1280x720 filename="%s"'%shot_path, controller)
    else:
        # editor take high res of active viewport
        try:
            unreal.AutomationLibrary.take_high_res_screenshot(1280,720, shot_path)
        except Exception:
            unreal.SystemLibrary.execute_console_command(None, 'HighResShot 1280x720 filename="%s"'%shot_path)
    time.sleep(2.5)
    note("screenshot","PASS", shot_path)
except Exception as e:
    note("screenshot","FAIL",e); shot_path=None

fails=[x for x in items if x["status"]=="FAIL"]
result="FAIL" if fails else "PASS"
out={"result":result,"mode":mode,"stamp":stamp,"shot":shot_path,"items":items}
with open(report_path,"w",encoding="utf-8") as f:
    json.dump(out,f,ensure_ascii=False,indent=2)
unreal.log("ACCEPT_VISUAL_%s %s"%(result, report_path))
if mode=="pie":
    try:
        if les and hasattr(les, "editor_request_end_play"):
            les.editor_request_end_play()
        elif hasattr(unreal.EditorLevelLibrary, "editor_end_play"):
            unreal.EditorLevelLibrary.editor_end_play()
    except Exception:
        pass