# -*- coding: utf-8 -*-
"""Polish A fix2: both beys visible + large P1/P2 labels + softer light + BattleCamera compose."""
import unreal
import os
import math

def log(m):
    unreal.log("[BeyPolishFix2] " + str(m))
    print("[BeyPolishFix2] " + str(m))

def g2u(x, y, z):
    return unreal.Vector(float(x) * 100.0, float(z) * 100.0, float(y) * 100.0)

def find_exact(label):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in sub.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None

def apply_mat(actor, mat):
    if not actor or not mat:
        return
    smc = actor.get_component_by_class(unreal.StaticMeshComponent)
    if smc:
        smc.set_material(0, mat)
        try:
            smc.set_editor_property("override_materials", [mat])
        except Exception:
            pass
        log("applied %s -> %s" % (mat.get_name(), actor.get_actor_label()))

def make_or_load_mat(path, rgb, roughness, name_hint):
    mat = unreal.EditorAssetLibrary.load_asset(path)
    if mat is None:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            path.rsplit("/", 1)[-1], path.rsplit("/", 1)[0], unreal.Material, unreal.MaterialFactoryNew()
        )
    # clear and rebuild simple color
    try:
        unreal.MaterialEditingLibrary.delete_all_material_expressions(mat)
    except Exception:
        pass
    bc = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 0)
    bc.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(bc, "", unreal.MaterialProperty.MP_BASE_COLOR)
    cr = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 120)
    cr.set_editor_property("r", float(roughness))
    unreal.MaterialEditingLibrary.connect_material_property(cr, "", unreal.MaterialProperty.MP_ROUGHNESS)
    cm = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 200)
    cm.set_editor_property("r", 0.0)
    unreal.MaterialEditingLibrary.connect_material_property(cm, "", unreal.MaterialProperty.MP_METALLIC)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    log("MATTE %s %s rgb=%s rough=%s" % (name_hint, path, rgb, roughness))
    return mat

def destroy_by_labels(labels):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in list(sub.get_all_level_actors()):
        if a.get_actor_label() in labels:
            sub.destroy_actor(a)

def spawn_label(sub, name, text, loc, color):
    actor = sub.spawn_actor_from_class(unreal.TextRenderActor, loc, unreal.Rotator(0, 90, 0))
    if not actor:
        log("FAIL label " + name)
        return None
    actor.set_actor_label(name)
    tr = actor.get_component_by_class(unreal.TextRenderComponent)
    if tr is None:
        try:
            tr = actor.text_render
        except Exception:
            tr = None
    if tr:
        tr.set_text(text)
        # alignment as int: 1=center horizontal, 1=center vertical (UE5 python may lack enum)
        try:
            tr.set_editor_property("horizontal_alignment", 1)
        except Exception as e:
            log("h_align: " + str(e))
        try:
            tr.set_editor_property("vertical_alignment", 1)
        except Exception as e:
            log("v_align: " + str(e))
        try:
            tr.set_world_size(110.0)
        except Exception:
            tr.set_editor_property("world_size", 110.0)
        try:
            tr.set_text_render_color(unreal.Color(int(color[0]*255), int(color[1]*255), int(color[2]*255), 255))
        except Exception:
            try:
                tr.set_editor_property("text_render_color", unreal.Color(int(color[0]*255), int(color[1]*255), int(color[2]*255), 255))
            except Exception as e:
                log("label color: " + str(e))
        # Face camera at +Y: TextRender faces +X locally -> yaw 90
        actor.set_actor_rotation(unreal.Rotator(0.0, 90.0, 0.0), False)
    log("LABEL %s '%s' at %s" % (name, text, loc))
    return actor

def dump_actors():
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in sub.get_all_level_actors():
        lab = a.get_actor_label()
        if any(k in lab for k in ("Bey", "Label", "Male", "Battle", "Smooth", "Ground", "Fill", "Rim", "Sky", "Sun", "Light", "Directional")):
            loc = a.get_actor_location()
            sc = a.get_actor_scale3d()
            log("ACTOR %s loc=(%.1f,%.1f,%.1f) scale=(%.2f,%.2f,%.2f) class=%s" % (
                lab, loc.x, loc.y, loc.z, sc.x, sc.y, sc.z, a.get_class().get_name()))

def main():
    log("BEGIN polish A fix2")
    project_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    dump_actors()

    mat_stad = make_or_load_mat("/Game/Imported/Stadium/M_StadiumMatte", (0.12, 0.13, 0.14), 0.94, "stadium")
    mat_red = make_or_load_mat("/Game/Imported/Beys/M_RedLotusSolid", (0.92, 0.05, 0.04), 0.5, "redlotus")
    mat_beyb = make_or_load_mat("/Game/Imported/Beys/M_BeyBSolid", (0.05, 0.35, 0.98), 0.5, "beyb")
    mat_ground = make_or_load_mat("/Game/Imported/Stadium/M_GroundMatte", (0.10, 0.105, 0.11), 0.96, "ground")

    bowl = find_exact("SmoothBowl_v1")
    bey_a = find_exact("BeyA_RedLotus")
    bey_b = find_exact("BeyB")
    male = find_exact("MaleLead")
    cam = find_exact("BattleCamera")
    ground = find_exact("GroundFallback")

    apply_mat(bowl, mat_stad)
    apply_mat(bey_a, mat_red)
    apply_mat(bey_b, mat_beyb)
    apply_mat(ground, mat_ground)

    # Place BOTH beys on near-side floor of bowl, clearly separated, raised above floor
    # Godot: x left/right, y up, z toward camera(+Y in UE)
    pos_a = g2u(-0.55, 0.50, 0.70)   # red left-near
    pos_b = g2u(0.55, 0.50, 0.70)    # blue right-near
    if bey_a:
        bey_a.set_actor_location(pos_a, False, False)
        bey_a.set_actor_scale3d(unreal.Vector(1.15, 1.15, 1.15))
        bey_a.set_actor_rotation(unreal.Rotator(0.0, 25.0, 0.0), False)
        smc = bey_a.get_component_by_class(unreal.StaticMeshComponent)
        if smc:
            # keep pivot fix + ensure unlit-ish visibility via emissive-ish not available; cast shadows
            try:
                smc.set_editor_property("relative_location", unreal.Vector(0.0, 7.5, 0.0))
            except Exception:
                pass
            smc.set_visibility(True, True)
            try:
                smc.set_editor_property("cast_shadow", True)
            except Exception:
                pass
        log("BeyA -> %s scale 1.15" % pos_a)
    if bey_b:
        bey_b.set_actor_location(pos_b, False, False)
        bey_b.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
        bey_b.set_actor_rotation(unreal.Rotator(0.0, -20.0, 0.0), False)
        smc = bey_b.get_component_by_class(unreal.StaticMeshComponent)
        if smc:
            smc.set_visibility(True, True)
        log("BeyB -> %s scale 1.0" % pos_b)

    if male:
        male_loc = g2u(-2.6, 0.08, -0.4)
        male.set_actor_location(male_loc, False, False)
        look = unreal.MathLibrary.find_look_at_rotation(male_loc, unreal.Vector(0.0, 40.0, 40.0))
        male.set_actor_rotation(unreal.Rotator(0.0, look.yaw, 0.0), False)
        log("MaleLead face bowl yaw=%s loc=%s" % (look.yaw, male_loc))

    # Soft lighting pass
    destroy_by_labels(["FillLight", "RimLight", "AmbientFill"])
    for a in sub.get_all_level_actors():
        lab = a.get_actor_label()
        cls = a.get_class().get_name()
        if "DirectionalLight" in cls or lab in ("Sun", "DirectionalLight", "Light Source"):
            try:
                a.set_actor_rotation(unreal.Rotator(-38.0, -30.0, 0.0), False)
                dc = a.get_component_by_class(unreal.DirectionalLightComponent)
                if dc:
                    dc.set_intensity(1.6)
                    dc.set_light_color(unreal.LinearColor(1.0, 0.97, 0.93, 1.0))
                    try:
                        dc.set_editor_property("shadow_amount", 0.4)
                    except Exception:
                        pass
                    try:
                        dc.set_editor_property("indirect_lighting_intensity", 1.4)
                    except Exception:
                        pass
                log("Sun softened")
            except Exception as e:
                log("sun: " + str(e))
        if "SkyLight" in cls or lab == "SkyLight":
            try:
                sc = a.get_component_by_class(unreal.SkyLightComponent)
                if sc:
                    sc.set_intensity(8.0)
                    sc.set_light_color(unreal.LinearColor(0.78, 0.84, 0.95, 1.0))
                    try:
                        sc.set_editor_property("lower_hemisphere_is_black", False)
                    except Exception:
                        pass
                    try:
                        sc.recapture_sky()
                    except Exception:
                        pass
                log("SkyLight fill")
            except Exception as e:
                log("sky: " + str(e))

    fill = sub.spawn_actor_from_class(unreal.RectLight, unreal.Vector(0.0, 520.0, 380.0), unreal.Rotator(-30.0, -90.0, 0.0))
    if fill:
        fill.set_actor_label("FillLight")
        fc = fill.get_component_by_class(unreal.RectLightComponent)
        if fc:
            fc.set_intensity(4500.0)
            fc.set_editor_property("source_width", 900.0)
            fc.set_editor_property("source_height", 500.0)
            fc.set_light_color(unreal.LinearColor(0.88, 0.92, 1.0, 1.0))
            try:
                fc.set_editor_property("attenuation_radius", 2500.0)
            except Exception:
                pass
            try:
                fc.set_editor_property("cast_shadows", False)
            except Exception:
                pass
        log("FillLight spawned")

    rim = sub.spawn_actor_from_class(unreal.PointLight, unreal.Vector(-180.0, -320.0, 300.0), unreal.Rotator(0, 0, 0))
    if rim:
        rim.set_actor_label("RimLight")
        pc = rim.get_component_by_class(unreal.PointLightComponent)
        if pc:
            pc.set_intensity(1800.0)
            pc.set_editor_property("attenuation_radius", 1600.0)
            pc.set_light_color(unreal.LinearColor(1.0, 0.95, 0.9, 1.0))
            try:
                pc.set_editor_property("cast_shadows", False)
            except Exception:
                pass
        log("RimLight spawned")

    # Extra soft overhead fill to kill bowl dead-black
    top = sub.spawn_actor_from_class(unreal.PointLight, unreal.Vector(0.0, 0.0, 520.0), unreal.Rotator(0, 0, 0))
    if top:
        top.set_actor_label("AmbientFill")
        pc = top.get_component_by_class(unreal.PointLightComponent)
        if pc:
            pc.set_intensity(2200.0)
            pc.set_editor_property("attenuation_radius", 1800.0)
            pc.set_light_color(unreal.LinearColor(0.9, 0.92, 1.0, 1.0))
            try:
                pc.set_editor_property("cast_shadows", False)
            except Exception:
                pass
        log("AmbientFill spawned")

    destroy_by_labels(["Label_P1", "Label_P2", "Player1Label", "Player2Label"])
    if bey_a:
        loc = bey_a.get_actor_location()
        spawn_label(sub, "Label_P1", "P1", unreal.Vector(loc.x, loc.y, loc.z + 95.0), (1.0, 0.3, 0.2))
    if bey_b:
        loc = bey_b.get_actor_location()
        spawn_label(sub, "Label_P2", "P2", unreal.Vector(loc.x, loc.y, loc.z + 95.0), (0.2, 0.5, 1.0))

    # Camera: closer, lower, include bowl + both beys + male; FOV flexible
    cam_loc = g2u(0.15, 5.4, 7.6)
    look_at = g2u(-0.15, 0.45, 0.35)
    if cam is None:
        cam = sub.spawn_actor_from_class(unreal.CameraActor, cam_loc, unreal.Rotator(0, 0, 0))
        if cam:
            cam.set_actor_label("BattleCamera")
    if cam:
        cam.set_actor_location(cam_loc, False, False)
        cam.set_actor_rotation((look_at - cam_loc).rotator(), False)
        fov = 56.0
        try:
            cam.camera_component.set_field_of_view(fov)
        except Exception:
            comp = cam.get_component_by_class(unreal.CameraComponent)
            if comp:
                comp.set_field_of_view(fov)
        # AutoActivate for PIE
        for cand in (unreal.AutoReceiveInput.PLAYER0 if hasattr(unreal, "AutoReceiveInput") else None, 1, "Player0"):
            if cand is None:
                continue
            try:
                cam.set_editor_property("auto_activate_for_player", cand)
                log("BattleCamera AutoActivate=%s" % cand)
                break
            except Exception as e:
                log("auto_act try %s: %s" % (cand, e))
        log("BattleCamera loc=%s fov=%s" % (cam_loc, fov))

    dump_actors()

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    except Exception:
        try:
            unreal.EditorLevelLibrary.save_current_level()
        except Exception:
            pass
    unreal.EditorAssetLibrary.save_directory("/Game/Maps", only_if_is_dirty=False, recursive=True)
    unreal.EditorAssetLibrary.save_directory("/Game/Imported", only_if_is_dirty=False, recursive=True)

    report = os.path.join(project_dir, "Tools", "polish_a_fix2_report.txt")
    with open(report, "w", encoding="utf-8") as f:
        f.write("polish A fix2 done\n")
        f.write("BeyA %s\n" % pos_a)
        f.write("BeyB %s\n" % pos_b)
        f.write("cam %s fov56\n" % cam_loc)

    flag = os.path.join(project_dir, "Tools", "need_polish_shot.flag")
    with open(flag, "w", encoding="utf-8") as f:
        f.write("polish_a_fix2\n")
    # clear ready so waiter waits fresh
    ready = os.path.join(project_dir, "Tools", "polish_shot_ready.flag")
    try:
        os.remove(ready)
    except Exception:
        pass
    log("DONE polish A fix2")

if __name__ == "__main__":
    main()