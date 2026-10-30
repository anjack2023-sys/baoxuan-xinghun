# -*- coding: utf-8 -*-
"""Visual polish A: matte stadium, soft fill, bey colors+labels, male faces bowl, BattleCamera compose."""
import unreal
import math
import os

LOG = []

def log(m):
    s = str(m)
    LOG.append(s)
    unreal.log("[BeyPolish] " + s)

def g2u(x, y, z):
    return unreal.Vector(float(x) * 100.0, float(z) * 100.0, float(y) * 100.0)

def write_report(project_dir):
    p = os.path.join(project_dir, "Tools", "polish_a_report.txt")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(LOG) + "\n")

def make_matte(path, rgb, roughness=0.88, name_hint=""):
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    pkg, name = path.rsplit("/", 1)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat = asset_tools.create_asset(name, pkg, unreal.Material, unreal.MaterialFactoryNew())
    if not mat:
        log("FAIL mat " + path)
        return None
    try:
        c3 = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 0)
        c3.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
        unreal.MaterialEditingLibrary.connect_material_property(c3, "", unreal.MaterialProperty.MP_BASE_COLOR)
        cr = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 160)
        cr.set_editor_property("r", float(roughness))
        unreal.MaterialEditingLibrary.connect_material_property(cr, "", unreal.MaterialProperty.MP_ROUGHNESS)
        cm = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 260)
        cm.set_editor_property("r", 0.0)
        unreal.MaterialEditingLibrary.connect_material_property(cm, "", unreal.MaterialProperty.MP_METALLIC)
        cs = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 360)
        cs.set_editor_property("r", 0.15)
        unreal.MaterialEditingLibrary.connect_material_property(cs, "", unreal.MaterialProperty.MP_SPECULAR)
        unreal.MaterialEditingLibrary.recompile_material(mat)
        unreal.EditorAssetLibrary.save_asset(path)
        log("MATTE %s %s rgb=%s rough=%s" % (name_hint, path, rgb, roughness))
    except Exception as e:
        log("mat err: " + str(e))
    return mat

def apply_mat(actor, mat):
    if not actor or not mat:
        return
    for c in actor.get_components_by_class(unreal.MeshComponent):
        try:
            c.set_material(0, mat)
        except Exception as e:
            log("apply: " + str(e))
    log("applied %s -> %s" % (mat.get_name(), actor.get_actor_label()))

def find_exact(label):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in sub.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None

def destroy_labels(sub):
    for a in list(sub.get_all_level_actors()):
        if a.get_actor_label() in ("Label_P1", "Label_P2", "Player1Label", "Player2Label"):
            try:
                sub.destroy_actor(a)
            except Exception:
                pass

def spawn_label(sub, name, text, loc, color):
    # TextRenderActor
    actor = sub.spawn_actor_from_class(unreal.TextRenderActor, loc, unreal.Rotator(0, 0, 0))
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
        tr.set_horizontal_alignment(unreal.TextRenderHorizontalAlignment.THA_CENTER)
        tr.set_vertical_alignment(unreal.TextRenderVerticalAlignment.TRVA_CENTER)
        try:
            tr.set_world_size(28.0)
        except Exception:
            try:
                tr.set_editor_property("world_size", 28.0)
            except Exception:
                pass
        try:
            tr.set_text_render_color(unreal.Color(int(color[0]*255), int(color[1]*255), int(color[2]*255), 255))
        except Exception:
            try:
                tr.set_editor_property("text_render_color", unreal.Color(int(color[0]*255), int(color[1]*255), int(color[2]*255), 255))
            except Exception as e:
                log("label color: " + str(e))
        # Face roughly toward BattleCamera (+Y side)
        actor.set_actor_rotation(unreal.Rotator(0, 180, 0), False)
    log("LABEL %s '%s' at %s" % (name, text, loc))
    return actor

def main():
    log("BEGIN polish A")
    project_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())

    # Materials: deep gray matte stadium; vivid bey colors (override noisy textures)
    mat_stad = make_matte("/Game/Imported/Stadium/M_StadiumMatte", (0.14, 0.15, 0.16), 0.92, "stadium")
    mat_red = make_matte("/Game/Imported/Beys/M_RedLotusSolid", (0.82, 0.08, 0.06), 0.55, "redlotus")
    mat_beyb = make_matte("/Game/Imported/Beys/M_BeyBSolid", (0.08, 0.42, 0.95), 0.55, "beyb")
    mat_ground = make_matte("/Game/Imported/Stadium/M_GroundMatte", (0.22, 0.23, 0.25), 0.95, "ground")

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level("/Game/Maps/Main")
    except Exception as e:
        log("load: " + str(e))

    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    bowl = find_exact("SmoothBowl_v1")
    bey_a = find_exact("BeyA_RedLotus")
    bey_b = find_exact("BeyB")
    male = find_exact("MaleLead")
    cam = find_exact("BattleCamera")
    ground = find_exact("GroundFallback")
    sun = find_exact("Sun")
    sky = find_exact("SkyLight")

    apply_mat(bowl, mat_stad)
    apply_mat(bey_a, mat_red)
    apply_mat(bey_b, mat_beyb)
    apply_mat(ground, mat_ground)

    # Reposition beys — both clearly on near half of bowl for camera on +Y
    # Bowl surface ~ bowl_y(0.85)≈0.42 flat-ish until 1.1; use r~0.9 height ~0.42 + lift
    pos_a = g2u(-0.75, 0.52, 0.55)   # left-near
    pos_b = g2u(0.75, 0.52, 0.55)    # right-near
    if bey_a:
        bey_a.set_actor_location(pos_a, False, False)
        bey_a.set_actor_scale3d(unreal.Vector(2.4, 2.4, 2.4))
        log("BeyA -> %s" % pos_a)
    if bey_b:
        bey_b.set_actor_location(pos_b, False, False)
        # BeyB mesh was tiny at 0.4 — bump for readability while keeping distinct
        bey_b.set_actor_scale3d(unreal.Vector(0.85, 0.85, 0.85))
        log("BeyB -> %s scale 0.85" % pos_b)

    # Keep red-lotus visual pivot offset
    if bey_a:
        smc = bey_a.get_component_by_class(unreal.StaticMeshComponent)
        if smc:
            try:
                smc.set_editor_property("relative_location", unreal.Vector(0.0, 7.5, 0.0))
            except Exception:
                pass

    # Male lead faces bowl center (origin)
    if male:
        male_loc = g2u(-3.1, 0.08, -0.8)
        male.set_actor_location(male_loc, False, False)
        look = unreal.MathLibrary.find_look_at_rotation(male_loc, unreal.Vector(0.0, 0.0, 60.0))
        # Keep upright: only yaw
        male.set_actor_rotation(unreal.Rotator(0.0, look.yaw, 0.0), False)
        log("MaleLead face bowl yaw=%s" % look.yaw)

    # Lighting: soft ambient, kill dead black
    # Remove old fill lights if any
    for a in list(sub.get_all_level_actors()):
        if a.get_actor_label() in ("FillLight", "RimLight", "AmbientFill", "SkyAtmosphereActor"):
            try:
                sub.destroy_actor(a)
            except Exception:
                pass

    if sun:
        try:
            sun.set_actor_rotation(unreal.Rotator(-42.0, -25.0, 0.0), False)
            dc = sun.get_component_by_class(unreal.DirectionalLightComponent)
            if dc:
                dc.set_intensity(2.2)
                dc.set_editor_property("indirect_lighting_intensity", 1.4)
                try:
                    dc.set_cast_shadows(True)
                    dc.set_editor_property("shadow_amount", 0.55)
                except Exception:
                    pass
                try:
                    dc.set_light_color(unreal.LinearColor(1.0, 0.97, 0.92, 1.0))
                except Exception:
                    pass
            log("Sun softened intensity=2.2")
        except Exception as e:
            log("sun: " + str(e))

    if sky:
        try:
            sc = sky.get_component_by_class(unreal.SkyLightComponent)
            if sc:
                sc.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
                sc.set_intensity(4.5)
                try:
                    sc.set_editor_property("lower_hemisphere_is_black", False)
                except Exception:
                    pass
                try:
                    sc.set_light_color(unreal.LinearColor(0.75, 0.82, 0.95, 1.0))
                except Exception:
                    pass
                try:
                    sc.recreate_capture_capture_scene()  # may not exist
                except Exception:
                    try:
                        sc.recapture_sky()
                    except Exception:
                        pass
            log("SkyLight fill intensity=4.5")
        except Exception as e:
            log("sky: " + str(e))
    else:
        sky = sub.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 200), unreal.Rotator(0, 0, 0))
        if sky:
            sky.set_actor_label("SkyLight")
            sc = sky.get_component_by_class(unreal.SkyLightComponent)
            if sc:
                sc.set_intensity(4.5)
            log("spawned SkyLight")

    # Soft fill from camera side (+Y)
    fill = sub.spawn_actor_from_class(unreal.RectLight, unreal.Vector(0.0, 650.0, 420.0), unreal.Rotator(-25.0, -90.0, 0.0))
    if fill:
        fill.set_actor_label("FillLight")
        fc = fill.get_component_by_class(unreal.RectLightComponent)
        if fc:
            try:
                fc.set_intensity(8.0)
                fc.set_editor_property("source_width", 600.0)
                fc.set_editor_property("source_height", 400.0)
                fc.set_cast_shadows(False)
                fc.set_light_color(unreal.LinearColor(0.85, 0.9, 1.0, 1.0))
            except Exception as e:
                log("fill props: " + str(e))
        log("FillLight added")

    # Subtle opposite bounce
    rim = sub.spawn_actor_from_class(unreal.PointLight, unreal.Vector(-200.0, -400.0, 350.0), unreal.Rotator(0, 0, 0))
    if rim:
        rim.set_actor_label("RimLight")
        pc = rim.get_component_by_class(unreal.PointLightComponent)
        if pc:
            try:
                pc.set_intensity(1200.0)
                pc.set_editor_property("attenuation_radius", 1200.0)
                pc.set_cast_shadows(False)
                pc.set_light_color(unreal.LinearColor(1.0, 0.95, 0.9, 1.0))
            except Exception as e:
                log("rim: " + str(e))

    # Labels above beys
    destroy_labels(sub)
    if bey_a:
        loc = bey_a.get_actor_location()
        spawn_label(sub, "Label_P1", "玩家1 / P1", unreal.Vector(loc.x, loc.y, loc.z + 55.0), (1.0, 0.35, 0.25))
    if bey_b:
        loc = bey_b.get_actor_location()
        spawn_label(sub, "Label_P2", "玩家2 / P2", unreal.Vector(loc.x, loc.y, loc.z + 55.0), (0.25, 0.55, 1.0))

    # BattleCamera — composition over FOV44: pull back, include bowl+bey+char
    cam_loc = g2u(0.0, 7.2, 9.5)          # farther than 6.2/6.8
    look_at = g2u(-0.35, 0.55, 0.15)
    if cam is None:
        cam = sub.spawn_actor_from_class(unreal.CameraActor, cam_loc, unreal.Rotator(0, 0, 0))
        if cam:
            cam.set_actor_label("BattleCamera")
    if cam:
        cam.set_actor_location(cam_loc, False, False)
        cam.set_actor_rotation((look_at - cam_loc).rotator(), False)
        fov = 52.0
        try:
            cam.camera_component.set_field_of_view(fov)
        except Exception:
            comp = cam.get_component_by_class(unreal.CameraComponent)
            if comp:
                comp.set_field_of_view(fov)
        # Runtime path: auto-activate for player 0 in PIE
        try:
            cam.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)
            log("BattleCamera AutoActivateForPlayer=Player0")
        except Exception as e:
            log("auto_activate: " + str(e))
            try:
                # enum as int fallback
                cam.set_editor_property("auto_activate_for_player", 1)
            except Exception as e2:
                log("auto_activate2: " + str(e2))
        log("BattleCamera loc=%s fov=%s" % (cam_loc, fov))

    # World settings: set game mode / default if needed — skip physics
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

    # Flag for BattleCamera / PIE shot helper
    flag = os.path.join(project_dir, "Tools", "need_polish_shot.flag")
    with open(flag, "w", encoding="utf-8") as f:
        f.write("polish_a\n")
    write_report(project_dir)
    log("DONE polish A")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        log("FATAL " + str(e))
        log(traceback.format_exc())
        write_report(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
        raise