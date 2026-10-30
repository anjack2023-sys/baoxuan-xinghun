# -*- coding: utf-8 -*-
"""Import Beyblade assets and build Content/Maps/Main for first visual pass (UE 5.8)."""
import unreal
import math
import os
import time

STAGE = r"C:\Users\Administrator\Desktop\beyblade-ue-import-src"
LOG = []

def log(msg):
    line = str(msg)
    LOG.append(line)
    unreal.log("[BeySetup] " + line)

def g2u(x, y, z):
    """Godot Y-up meters -> UE Z-up cm."""
    return unreal.Vector(float(x) * 100.0, float(z) * 100.0, float(y) * 100.0)

def write_report(project_dir):
    report = os.path.join(project_dir, "Tools", "setup_main_report.txt")
    os.makedirs(os.path.dirname(report), exist_ok=True)
    with open(report, "w", encoding="utf-8") as f:
        f.write("\n".join(LOG))
        f.write("\n")
    log("REPORT " + report)

def import_file(src, dest_path, dest_name=None):
    if not os.path.isfile(src):
        log("MISSING: " + src)
        return []
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", src)
    task.set_editor_property("destination_path", dest_path)
    if dest_name:
        task.set_editor_property("destination_name", dest_name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    try:
        task.set_editor_property("import_as_skeletal", "male-lead" in os.path.basename(src).lower())
    except Exception:
        pass
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = []
    try:
        imported = [str(p) for p in list(task.get_editor_property("imported_object_paths") or [])]
    except Exception:
        try:
            imported = [str(p) for p in list(task.imported_object_paths or [])]
        except Exception as e:
            log("imported_object_paths err: " + str(e))
    log("IMPORT %s -> %s | %s" % (os.path.basename(src), dest_path, imported))
    return imported

def list_mesh_assets(folder):
    out = []
    for ap in unreal.EditorAssetLibrary.list_assets(folder, recursive=True, include_folder=False):
        obj = unreal.EditorAssetLibrary.load_asset(ap)
        if obj is None:
            continue
        if isinstance(obj, (unreal.StaticMesh, unreal.SkeletalMesh)):
            out.append((ap, obj))
            log("FOUND_MESH %s (%s)" % (ap, type(obj).__name__))
    return out

def spawn_mesh_actor(mesh, name, loc, scale, rot=None):
    if mesh is None:
        log("skip spawn, no mesh: " + name)
        return None
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if rot is None:
        rot = unreal.Rotator(0, 0, 0)
    actor = None
    if isinstance(mesh, unreal.StaticMesh):
        actor = sub.spawn_actor_from_object(mesh, loc, rot)
    elif isinstance(mesh, unreal.SkeletalMesh):
        actor = sub.spawn_actor_from_class(unreal.SkeletalMeshActor, loc, rot)
        if actor:
            try:
                actor.skeletal_mesh_component.set_skeletal_mesh_asset(mesh)
            except Exception:
                try:
                    actor.skeletal_mesh_component.set_editor_property("skeletal_mesh_asset", mesh)
                except Exception as e:
                    log("set skeletal mesh: " + str(e))
    else:
        actor = sub.spawn_actor_from_object(mesh, loc, rot)
    if actor:
        actor.set_actor_label(name)
        actor.set_actor_scale3d(unreal.Vector(float(scale), float(scale), float(scale)))
        log("SPAWN %s at %s scale=%s" % (name, loc, scale))
    else:
        log("FAILED spawn " + name)
    return actor

def pick_by_name(meshes, keywords, exclude=None):
    exclude = exclude or []
    for ap, obj in meshes:
        low = ap.lower()
        if any(ex in low for ex in exclude):
            continue
        if any(k in low for k in keywords):
            return obj
    return None

def main():
    log("BEGIN setup_main v2")
    project_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
    log("project_dir=" + project_dir)

    try:
        # Imports
        import_file(os.path.join(STAGE, "Stadium", "stadium.fbx"), "/Game/Imported/Stadium", "SM_Stadium")
        import_file(os.path.join(STAGE, "Stadium", "stadium_basecolor.jpg"), "/Game/Imported/Stadium", "T_Stadium_BC")
        import_file(os.path.join(STAGE, "Beys", "red-lotus-tripo-v2.glb"), "/Game/Imported/Beys", "SM_RedLotus")
        import_file(os.path.join(STAGE, "Beys", "red-lotus_basecolor.jpg"), "/Game/Imported/Beys", "T_RedLotus_BC")
        import_file(os.path.join(STAGE, "Beys", "bey-b-tripo-v2.fbx"), "/Game/Imported/Beys", "SM_BeyB")
        import_file(os.path.join(STAGE, "Beys", "bey-b_basecolor.jpg"), "/Game/Imported/Beys", "T_BeyB_BC")
        import_file(os.path.join(STAGE, "Character", "male-lead-tripo-rigged-clean01.glb"), "/Game/Imported/Character", "SK_MaleLead")
        import_file(os.path.join(STAGE, "Character", "male-lead_basecolor.jpg"), "/Game/Imported/Character", "T_MaleLead_BC")

        unreal.EditorAssetLibrary.save_directory("/Game/Imported", only_if_is_dirty=False, recursive=True)

        stadium_meshes = list_mesh_assets("/Game/Imported/Stadium")
        bey_meshes = list_mesh_assets("/Game/Imported/Beys")
        char_meshes = list_mesh_assets("/Game/Imported/Character")

        stadium = pick_by_name(stadium_meshes, ["stadium"]) or (stadium_meshes[0][1] if stadium_meshes else None)
        red = pick_by_name(bey_meshes, ["red", "lotus"]) 
        beyb = pick_by_name(bey_meshes, ["bey", "beyb", "sm_beyb"], exclude=["red", "lotus"])
        if red is None and bey_meshes:
            red = bey_meshes[0][1]
        if beyb is None:
            for ap, obj in bey_meshes:
                if obj is not red:
                    beyb = obj
                    break
        male = pick_by_name(char_meshes, ["male", "lead", "sk_male"]) or (char_meshes[0][1] if char_meshes else None)

        log("RESOLVED stadium=%s" % (stadium.get_path_name() if stadium else None))
        log("RESOLVED red=%s" % (red.get_path_name() if red else None))
        log("RESOLVED beyb=%s" % (beyb.get_path_name() if beyb else None))
        log("RESOLVED male=%s" % (male.get_path_name() if male else None))

        level_path = "/Game/Maps/Main"
        # Create level
        created = False
        try:
            unreal.EditorLevelLibrary.new_level(level_path)
            created = True
            log("new_level OK EditorLevelLibrary")
        except Exception as e:
            log("EditorLevelLibrary.new_level: " + str(e))
        if not created:
            try:
                les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
                les.new_level(level_path)
                created = True
                log("new_level OK LevelEditorSubsystem")
            except Exception as e:
                log("LevelEditorSubsystem.new_level: " + str(e))
        if not created:
            try:
                unreal.EditorLevelLibrary.new_level_from_template(level_path, "/Engine/Maps/Templates/Template_Default")
                created = True
                log("new_level_from_template OK")
            except Exception as e:
                log("new_level_from_template: " + str(e))

        sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

        # Light
        light = sub.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(400, 600, 1200), unreal.Rotator(-50, -35, 0))
        if light:
            light.set_actor_label("Sun")
            try:
                comp = light.get_component_by_class(unreal.DirectionalLightComponent)
                if comp:
                    comp.set_intensity(10.0)
                    comp.set_cast_shadows(True)
            except Exception as e:
                log("light: " + str(e))
        try:
            sky = sub.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 100), unreal.Rotator(0, 0, 0))
            if sky:
                sky.set_actor_label("SkyLight")
        except Exception as e:
            log("skylight: " + str(e))

        # Ground
        cube = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
        if cube:
            ground = sub.spawn_actor_from_object(cube, unreal.Vector(0, 0, -7.5), unreal.Rotator(0, 0, 0))
            if ground:
                ground.set_actor_label("GroundFallback")
                ground.set_actor_scale3d(unreal.Vector(14.0, 14.0, 0.15))

        spawn_mesh_actor(stadium, "Stadium", g2u(0.0, 0.08, 0.0), 5.0)
        spawn_mesh_actor(red, "BeyA_RedLotus", g2u(-0.85, 0.55, 0.1), 2.666667)
        spawn_mesh_actor(beyb, "BeyB", g2u(0.85, 0.35, -0.1), 0.4)
        yaw_deg = math.degrees(math.atan2(-0.8, 3.1))
        spawn_mesh_actor(male, "MaleLead", g2u(-3.1, 0.08, -0.8), 1.732, unreal.Rotator(0.0, yaw_deg, 0.0))

        cam_loc = g2u(0.0, 6.2, 6.8)
        look_at = g2u(-0.5, 0.45, -0.4)
        cam = sub.spawn_actor_from_class(unreal.CameraActor, cam_loc, unreal.Rotator(0, 0, 0))
        if cam:
            cam.set_actor_label("BattleCamera")
            cam.set_actor_rotation((look_at - cam_loc).rotator(), False)
            try:
                cam.camera_component.set_field_of_view(44.0)
            except Exception:
                try:
                    comp = cam.get_component_by_class(unreal.CameraComponent)
                    if comp:
                        comp.set_field_of_view(44.0)
                except Exception as e:
                    log("fov: " + str(e))
            try:
                unreal.EditorLevelLibrary.pilot_level_actor(cam)
            except Exception as e:
                log("pilot: " + str(e))

        try:
            unreal.EditorLevelLibrary.save_current_level()
        except Exception as e:
            log("save_current_level: " + str(e))
        try:
            unreal.EditorAssetLibrary.save_asset(level_path)
        except Exception as e:
            log("save_asset level: " + str(e))
        unreal.EditorAssetLibrary.save_directory("/Game/Maps", only_if_is_dirty=False, recursive=True)
        unreal.EditorAssetLibrary.save_directory("/Game/Imported", only_if_is_dirty=False, recursive=True)
        log("SAVED " + level_path)

        # Screenshot
        shot_dir = os.path.join(project_dir, "screenshots")
        os.makedirs(shot_dir, exist_ok=True)
        shot_base = os.path.join(shot_dir, "main_visual_pass_01").replace("\\", "/")
        try:
            unreal.SystemLibrary.execute_console_command(None, 'HighResShot 3840x2160 filename="' + shot_base + '.png"')
            log("HighResShot queued " + shot_base + ".png")
        except Exception as e:
            log("HighResShot: " + str(e))
        try:
            if cam:
                unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, shot_base + "_auto", cam)
                log("Automation screenshot queued")
        except Exception as e:
            log("AutomationLibrary: " + str(e))

        # Also try EditorLevelLibrary screenshot
        try:
            unreal.EditorLevelLibrary.editor_set_game_view(True)
        except Exception:
            pass

        time.sleep(3.0)
        write_report(project_dir)
        log("DONE")
    except Exception as e:
        log("FATAL: " + str(e))
        import traceback
        log(traceback.format_exc())
        write_report(project_dir)
        raise

    # Quit after short delay so screenshots flush
    try:
        unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
    except Exception:
        pass

if __name__ == "__main__":
    main()