# -*- coding: utf-8 -*-
"""smooth_bowl_v1 pass: import bowl, materials, dedupe stadium, red-lotus pivot, save Main."""
import unreal
import math
import os
import time

STAGE = r"C:\Users\Administrator\Desktop\beyblade-ue-import-src"
LOG = []

def log(m):
    s = str(m)
    LOG.append(s)
    unreal.log("[BeySmooth] " + s)

def write_report(project_dir):
    path = os.path.join(project_dir, "Tools", "smooth_bowl_report.txt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(LOG) + "\n")
    log("REPORT " + path)

def import_file(src, dest_path, dest_name=None):
    if not os.path.isfile(src):
        log("MISSING " + src)
        return []
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", src)
    task.set_editor_property("destination_path", dest_path)
    if dest_name:
        task.set_editor_property("destination_name", dest_name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = []
    try:
        imported = [str(p) for p in list(task.get_editor_property("imported_object_paths") or [])]
    except Exception:
        pass
    log("IMPORT %s -> %s" % (os.path.basename(src), imported))
    return imported

def ensure_texture(path):
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    return None

def create_textured_material(mat_path, texture_path, fallback_rgb=(0.55, 0.56, 0.58)):
    """Create a simple opaque material with base color texture or constant."""
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    pkg = mat_path.rsplit("/", 1)[0]
    name = mat_path.rsplit("/", 1)[-1]
    if unreal.EditorAssetLibrary.does_asset_exist(mat_path):
        unreal.EditorAssetLibrary.delete_asset(mat_path)
    factory = unreal.MaterialFactoryNew()
    mat = asset_tools.create_asset(name, pkg, unreal.Material, factory)
    if mat is None:
        log("FAILED create mat " + mat_path)
        return None
    tex = ensure_texture(texture_path) if texture_path else None
    try:
        if tex is not None:
            ts = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -350, 0)
            ts.set_editor_property("texture", tex)
            unreal.MaterialEditingLibrary.connect_material_property(ts, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
            # slight roughness
            const_r = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 200)
            const_r.set_editor_property("r", 0.65)
            unreal.MaterialEditingLibrary.connect_material_property(const_r, "", unreal.MaterialProperty.MP_ROUGHNESS)
            log("MAT textured " + mat_path + " <- " + texture_path)
        else:
            const3 = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 0)
            const3.set_editor_property("constant", unreal.LinearColor(fallback_rgb[0], fallback_rgb[1], fallback_rgb[2], 1.0))
            unreal.MaterialEditingLibrary.connect_material_property(const3, "", unreal.MaterialProperty.MP_BASE_COLOR)
            const_r = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 200)
            const_r.set_editor_property("r", 0.7)
            unreal.MaterialEditingLibrary.connect_material_property(const_r, "", unreal.MaterialProperty.MP_ROUGHNESS)
            log("MAT neutral constant " + mat_path)
        unreal.MaterialEditingLibrary.recompile_material(mat)
        unreal.EditorAssetLibrary.save_asset(mat_path)
    except Exception as e:
        log("MAT build error: " + str(e))
        # still save empty-ish material
        try:
            unreal.EditorAssetLibrary.save_asset(mat_path)
        except Exception:
            pass
    return mat

def set_mesh_material(mesh, mat, slot=0):
    if mesh is None or mat is None:
        return
    try:
        if isinstance(mesh, unreal.StaticMesh):
            # Set material in mesh asset
            mats = mesh.static_materials
            # Use EditorStaticMeshLibrary if available
            try:
                unreal.EditorStaticMeshLibrary.set_static_mesh_material(mesh, mat.get_path_name(), slot)
            except Exception:
                pass
            try:
                mesh.set_material(slot, mat)
            except Exception:
                pass
            # Proper way in UE5:
            smm = unreal.StaticMaterial(mat, unreal.Name("SmoothBowl"), unreal.Name("SmoothBowl"), unreal.Name("SmoothBowl"))
            # Fallback: create MIC override at actor level instead
            log("set_mesh_material attempted for " + mesh.get_path_name())
            unreal.EditorAssetLibrary.save_asset(mesh.get_path_name().split(".")[0])
    except Exception as e:
        log("set_mesh_material: " + str(e))

def apply_actor_material(actor, mat):
    if actor is None or mat is None:
        return
    try:
        comps = actor.get_components_by_class(unreal.MeshComponent)
        for c in comps:
            try:
                c.set_material(0, mat)
            except Exception:
                try:
                    c.set_editor_property("override_materials", [mat])
                except Exception as e:
                    log("comp mat: " + str(e))
        log("applied mat to actor " + actor.get_actor_label())
    except Exception as e:
        log("apply_actor_material: " + str(e))

def destroy_by_labels(labels):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    killed = 0
    for a in list(sub.get_all_level_actors()):
        if a.get_actor_label() in labels:
            try:
                sub.destroy_actor(a)
                killed += 1
                log("destroyed " + a.get_actor_label())
            except Exception as e:
                log("destroy fail: " + str(e))
    return killed

def find_actors(label_substr=None, exact=None):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    out = []
    for a in sub.get_all_level_actors():
        lab = a.get_actor_label()
        if exact is not None and lab == exact:
            out.append(a)
        elif label_substr is not None and label_substr.lower() in lab.lower():
            out.append(a)
    return out

def spawn_static(mesh, name, loc, scale=1.0, rot=None):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if rot is None:
        rot = unreal.Rotator(0, 0, 0)
    actor = sub.spawn_actor_from_object(mesh, loc, rot)
    if actor:
        actor.set_actor_label(name)
        actor.set_actor_scale3d(unreal.Vector(float(scale), float(scale), float(scale)))
        log("SPAWN %s at %s scale=%s" % (name, loc, scale))
    return actor

def g2u(x, y, z):
    return unreal.Vector(float(x) * 100.0, float(z) * 100.0, float(y) * 100.0)

def main():
    log("BEGIN smooth_bowl_v1 pass")
    project_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())

    # Import smooth bowl OBJ
    import_file(os.path.join(STAGE, "Stadium", "smooth_bowl_v1.obj"), "/Game/Imported/Stadium", "SM_SmoothBowl_v1")
    unreal.EditorAssetLibrary.save_directory("/Game/Imported/Stadium", only_if_is_dirty=False, recursive=True)

    # Find meshes / textures
    bowl = None
    for ap in unreal.EditorAssetLibrary.list_assets("/Game/Imported/Stadium", recursive=True, include_folder=False):
        if "smoothbowl" in ap.lower().replace("_", "") or "sm_smoothbowl" in ap.lower().replace("_", ""):
            o = unreal.EditorAssetLibrary.load_asset(ap)
            if isinstance(o, unreal.StaticMesh):
                bowl = o
                break
    if bowl is None:
        # fallback any newly named
        for ap in unreal.EditorAssetLibrary.list_assets("/Game/Imported/Stadium", recursive=True, include_folder=False):
            o = unreal.EditorAssetLibrary.load_asset(ap)
            if isinstance(o, unreal.StaticMesh) and "smooth" in ap.lower():
                bowl = o
                break
    log("bowl=%s" % (bowl.get_path_name() if bowl else None))

    tex_stad = ensure_texture("/Game/Imported/Stadium/T_Stadium_BC")
    tex_beyb = ensure_texture("/Game/Imported/Beys/T_BeyB_BC")
    log("tex_stad=%s tex_beyb=%s" % (tex_stad.get_path_name() if tex_stad else None, tex_beyb.get_path_name() if tex_beyb else None))

    mat_stad = create_textured_material("/Game/Imported/Stadium/M_StadiumNeutral", "/Game/Imported/Stadium/T_Stadium_BC", (0.52, 0.54, 0.56))
    mat_beyb = create_textured_material("/Game/Imported/Beys/M_BeyB", "/Game/Imported/Beys/T_BeyB_BC", (0.25, 0.55, 0.85))

    # Load Main
    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level("/Game/Maps/Main")
        log("loaded Main")
    except Exception as e:
        log("load Main: " + str(e))
        try:
            unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/Main")
        except Exception as e2:
            log("load_map: " + str(e2))

    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    # Deduplicate / remove FBX stadium actors (any label containing Stadium but not Smooth)
    for a in list(sub.get_all_level_actors()):
        lab = a.get_actor_label()
        if lab == "Stadium" or lab == "SM_Stadium" or (lab.startswith("Stadium") and "Smooth" not in lab):
            try:
                sub.destroy_actor(a)
                log("removed old stadium actor: " + lab)
            except Exception as e:
                log("remove stadium: " + str(e))
        if "SmoothBowl" in lab or lab == "SmoothBowl_v1":
            try:
                sub.destroy_actor(a)
                log("removed prior smooth bowl: " + lab)
            except Exception:
                pass

    # Spawn ONE smooth bowl at world origin (vertices already in UE cm / Godot world mapping)
    bowl_actor = None
    if bowl is not None:
        bowl_actor = spawn_static(bowl, "SmoothBowl_v1", unreal.Vector(0, 0, 0), 1.0)
        apply_actor_material(bowl_actor, mat_stad)
        # Enable complex collision as default for static mesh
        try:
            body = bowl_actor.static_mesh_component
            body.set_editor_property("collision_complexity", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        except Exception as e:
            log("collision flag: " + str(e))
    else:
        log("ERROR no bowl mesh")

    # BeyB material
    for a in find_actors(exact="BeyB"):
        apply_actor_material(a, mat_beyb)

    # Also try assign on mesh asset for BeyB
    beyb_mesh = unreal.EditorAssetLibrary.load_asset("/Game/Imported/Beys/SM_BeyB")
    if beyb_mesh and mat_beyb:
        try:
            # slot 0 override via StaticMeshSourceModel is hard; actor override is enough
            pass
        except Exception:
            pass

    # Red lotus pivot: Godot center.z ≈ -0.075m → move visual by +0.075m Godot Z = +7.5cm UE Y
    for a in find_actors(exact="BeyA_RedLotus"):
        try:
            # Offset mesh component, keep actor transform as sim center
            smc = a.get_component_by_class(unreal.StaticMeshComponent)
            if smc:
                # Relative location in actor space; actor forward may vary — Godot Z maps to UE Y
                smc.set_editor_property("relative_location", unreal.Vector(0.0, 7.5, 0.0))
                log("red-lotus visual pivot offset +7.5cm UE Y (Godot +Z 0.075)")
            else:
                # fallback move actor (affects sim center too — noted)
                loc = a.get_actor_location()
                a.set_actor_location(unreal.Vector(loc.x, loc.y + 7.5, loc.z), False, False)
                log("red-lotus actor Y += 7.5 (fallback)")
        except Exception as e:
            log("pivot fix: " + str(e))

    # Ensure BattleCamera still present with fov 44
    cams = find_actors(exact="BattleCamera")
    if not cams:
        cam_loc = g2u(0.0, 6.2, 6.8)
        look_at = g2u(-0.5, 0.45, -0.4)
        cam = sub.spawn_actor_from_class(unreal.CameraActor, cam_loc, unreal.Rotator(0, 0, 0))
        if cam:
            cam.set_actor_label("BattleCamera")
            cam.set_actor_rotation((look_at - cam_loc).rotator(), False)
            try:
                cam.camera_component.set_field_of_view(44.0)
            except Exception:
                pass
            log("recreated BattleCamera")
    else:
        cam = cams[0]
        try:
            cam.camera_component.set_field_of_view(44.0)
        except Exception:
            try:
                comp = cam.get_component_by_class(unreal.CameraComponent)
                if comp:
                    comp.set_field_of_view(44.0)
            except Exception:
                pass
        log("BattleCamera ok fov set")

    # Count stadium-like actors
    stad_count = 0
    for a in sub.get_all_level_actors():
        lab = a.get_actor_label().lower()
        if "stadium" in lab or "smoothbowl" in lab:
            stad_count += 1
            log("stadium-like actor: " + a.get_actor_label())
    log("stadium-like count=%d (want 1)" % stad_count)

    try:
        unreal.EditorLevelLibrary.save_current_level()
    except Exception:
        pass
    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    except Exception:
        pass
    unreal.EditorAssetLibrary.save_directory("/Game/Maps", only_if_is_dirty=False, recursive=True)
    unreal.EditorAssetLibrary.save_directory("/Game/Imported", only_if_is_dirty=False, recursive=True)

    # Write init script flag for camera shot on next interactive open
    flag = os.path.join(project_dir, "Tools", "need_battlecam_shot.flag")
    with open(flag, "w", encoding="utf-8") as f:
        f.write("1\n")
    log("flag " + flag)

    write_report(project_dir)
    log("DONE")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        log("FATAL " + str(e))
        log(traceback.format_exc())
        project_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
        write_report(project_dir)
        raise