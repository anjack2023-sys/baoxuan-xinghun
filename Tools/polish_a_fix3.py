# -*- coding: utf-8 -*-
"""Fix BeyA stuck at origin; ensure both beys + labels placed; save; flag shot."""
import unreal
import os

def log(m):
    unreal.log("[BeyPolishFix3] " + str(m))
    print("[BeyPolishFix3] " + str(m))

def find_exact(label):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in sub.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None

def force_world_loc(actor, loc, scale=None, yaw=0.0):
    if not actor:
        return False
    # detach if any
    try:
        actor.detach_from_actor(unreal.DetachmentTransformRules.KEEP_WORLD_TRANSFORM)
    except Exception:
        try:
            root = actor.get_editor_property("root_component")
            if root:
                try:
                    root.detach_from_parent()
                except Exception:
                    pass
        except Exception:
            pass
    ok = False
    try:
        ok = bool(actor.set_actor_location(loc, False, True))  # teleport
    except Exception as e:
        log("set_actor_location: " + str(e))
    # also set via root component
    try:
        root = actor.root_component
        if root is None:
            root = actor.get_component_by_class(unreal.SceneComponent)
        if root:
            root.set_world_location(loc, False, True)
            ok = True
    except Exception as e:
        log("root set_world_location: " + str(e))
    try:
        actor.set_actor_rotation(unreal.Rotator(0.0, float(yaw), 0.0), False)
    except Exception:
        pass
    if scale is not None:
        actor.set_actor_scale3d(unreal.Vector(float(scale), float(scale), float(scale)))
    got = actor.get_actor_location()
    log("force %s -> want=(%.1f,%.1f,%.1f) got=(%.1f,%.1f,%.1f) ok=%s" % (
        actor.get_actor_label(), loc.x, loc.y, loc.z, got.x, got.y, got.z, ok))
    return abs(got.x - loc.x) < 1.0 and abs(got.y - loc.y) < 1.0 and abs(got.z - loc.z) < 1.0

def destroy_labels():
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in list(sub.get_all_level_actors()):
        if a.get_actor_label() in ("Label_P1", "Label_P2", "Player1Label", "Player2Label"):
            sub.destroy_actor(a)

def spawn_label(name, text, loc, color):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = sub.spawn_actor_from_class(unreal.TextRenderActor, loc, unreal.Rotator(0.0, 90.0, 0.0))
    if not actor:
        log("FAIL label " + name)
        return
    actor.set_actor_label(name)
    tr = actor.get_component_by_class(unreal.TextRenderComponent)
    if tr:
        tr.set_text(text)
        try:
            tr.set_world_size(120.0)
        except Exception:
            tr.set_editor_property("world_size", 120.0)
        try:
            tr.set_text_render_color(unreal.Color(int(color[0]*255), int(color[1]*255), int(color[2]*255), 255))
        except Exception:
            pass
        # keep facing +Y (camera)
        actor.set_actor_rotation(unreal.Rotator(0.0, 90.0, 0.0), False)
    log("LABEL %s at %s" % (name, loc))

def main():
    log("BEGIN fix3")
    project_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
    bey_a = find_exact("BeyA_RedLotus")
    bey_b = find_exact("BeyB")
    male = find_exact("MaleLead")
    cam = find_exact("BattleCamera")

    # Inspect attachment / mobility
    for a in (bey_a, bey_b):
        if not a:
            continue
        try:
            root = a.root_component
            mob = root.get_editor_property("mobility") if root else None
            log("%s mobility=%s class=%s" % (a.get_actor_label(), mob, a.get_class().get_name()))
            if root:
                try:
                    root.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
                    log("set MOVABLE " + a.get_actor_label())
                except Exception as e:
                    log("mobility: " + str(e))
        except Exception as e:
            log("inspect: " + str(e))
        # clear bad relative offset that confuses pivot (keep small Y pivot for redlotus mesh)
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        if smc and a.get_actor_label() == "BeyA_RedLotus":
            try:
                # Ensure mesh relative is only pivot fix, not world displace
                smc.set_editor_property("relative_location", unreal.Vector(0.0, 7.5, 0.0))
            except Exception:
                pass
        if smc:
            try:
                smc.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
            except Exception:
                pass
            smc.set_visibility(True, True)

    pos_a = unreal.Vector(-70.0, 90.0, 55.0)
    pos_b = unreal.Vector(70.0, 90.0, 55.0)
    ok_a = force_world_loc(bey_a, pos_a, scale=1.35, yaw=30.0)
    ok_b = force_world_loc(bey_b, pos_b, scale=1.1, yaw=-25.0)
    log("placed ok_a=%s ok_b=%s" % (ok_a, ok_b))

    # If still stuck, destroy and respawn from mesh asset
    if bey_a and not ok_a:
        log("BeyA still stuck — respawn")
        smc = bey_a.get_component_by_class(unreal.StaticMeshComponent)
        mesh = None
        mat = None
        if smc:
            try:
                mesh = smc.get_editor_property("static_mesh")
            except Exception:
                pass
            try:
                mat = smc.get_material(0)
            except Exception:
                pass
        sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        old_label = bey_a.get_actor_label()
        sub.destroy_actor(bey_a)
        if mesh is None:
            mesh = unreal.EditorAssetLibrary.load_asset("/Game/Imported/Beys/SM_RedLotus")
            if mesh is None:
                # try search
                for p in unreal.EditorAssetLibrary.list_assets("/Game/Imported", recursive=True, include_folder=False):
                    if "RedLotus" in p or "redlotus" in p.lower() or "Red_Lotus" in p:
                        log("cand " + p)
                        if p.endswith(".") or "StaticMesh" in str(type(unreal.EditorAssetLibrary.load_asset(p))):
                            asset = unreal.EditorAssetLibrary.load_asset(p)
                            if isinstance(asset, unreal.StaticMesh):
                                mesh = asset
                                log("use mesh " + p)
                                break
        new_a = sub.spawn_actor_from_class(unreal.StaticMeshActor, pos_a, unreal.Rotator(0.0, 30.0, 0.0))
        if new_a:
            new_a.set_actor_label("BeyA_RedLotus")
            new_a.set_actor_scale3d(unreal.Vector(1.35, 1.35, 1.35))
            nsmc = new_a.get_component_by_class(unreal.StaticMeshComponent)
            if nsmc:
                try:
                    nsmc.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
                except Exception:
                    pass
                if mesh:
                    nsmc.set_static_mesh(mesh)
                if mat is None:
                    mat = unreal.EditorAssetLibrary.load_asset("/Game/Imported/Beys/M_RedLotusSolid")
                if mat:
                    nsmc.set_material(0, mat)
                try:
                    nsmc.set_editor_property("relative_location", unreal.Vector(0.0, 7.5, 0.0))
                except Exception:
                    pass
            bey_a = new_a
            got = bey_a.get_actor_location()
            log("respawned BeyA at (%.1f,%.1f,%.1f)" % (got.x, got.y, got.z))

    if male:
        male_loc = unreal.Vector(-260.0, -40.0, 8.0)
        force_world_loc(male, male_loc, scale=None, yaw=0.0)
        look = unreal.MathLibrary.find_look_at_rotation(male_loc, unreal.Vector(0.0, 50.0, 40.0))
        male.set_actor_rotation(unreal.Rotator(0.0, look.yaw, 0.0), False)
        log("MaleLead yaw=%s" % look.yaw)

    destroy_labels()
    if bey_a:
        loc = bey_a.get_actor_location()
        spawn_label("Label_P1", "P1", unreal.Vector(loc.x, loc.y, loc.z + 110.0), (1.0, 0.25, 0.15))
    if bey_b:
        loc = bey_b.get_actor_location()
        spawn_label("Label_P2", "P2", unreal.Vector(loc.x, loc.y, loc.z + 110.0), (0.15, 0.45, 1.0))

    # Camera compose
    cam_loc = unreal.Vector(20.0, 720.0, 500.0)
    look_at = unreal.Vector(0.0, 40.0, 40.0)
    if cam:
        force_world_loc(cam, cam_loc)
        cam.set_actor_rotation((look_at - cam_loc).rotator(), False)
        try:
            cam.camera_component.set_field_of_view(56.0)
        except Exception:
            comp = cam.get_component_by_class(unreal.CameraComponent)
            if comp:
                comp.set_field_of_view(56.0)
        try:
            cam.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)
        except Exception as e:
            log("auto_act: " + str(e))

    # dump
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in sub.get_all_level_actors():
        lab = a.get_actor_label()
        if lab in ("BeyA_RedLotus", "BeyB", "Label_P1", "Label_P2", "BattleCamera", "MaleLead"):
            loc = a.get_actor_location()
            log("FINAL %s (%.1f,%.1f,%.1f) scale=%s" % (lab, loc.x, loc.y, loc.z, a.get_actor_scale3d()))

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    except Exception:
        unreal.EditorLevelLibrary.save_current_level()
    unreal.EditorAssetLibrary.save_directory("/Game/Maps", only_if_is_dirty=False, recursive=True)

    with open(os.path.join(project_dir, "Tools", "polish_a_fix3_report.txt"), "w", encoding="utf-8") as f:
        f.write("fix3 done\n")
        if bey_a:
            loc = bey_a.get_actor_location()
            f.write("BeyA %.1f %.1f %.1f\n" % (loc.x, loc.y, loc.z))
        if bey_b:
            loc = bey_b.get_actor_location()
            f.write("BeyB %.1f %.1f %.1f\n" % (loc.x, loc.y, loc.z))

    flag = os.path.join(project_dir, "Tools", "need_polish_shot.flag")
    with open(flag, "w", encoding="utf-8") as f:
        f.write("polish_a_fix3\n")
    try:
        os.remove(os.path.join(project_dir, "Tools", "polish_shot_ready.flag"))
    except Exception:
        pass
    log("DONE fix3")

if __name__ == "__main__":
    main()