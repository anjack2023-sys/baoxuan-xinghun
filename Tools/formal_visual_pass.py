"""Persist the visual pass in /Game/Maps/Main. No preview/runtime overrides."""
import json
import math
import os
import unreal

ROOT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def actor(label):
    matches = [a for a in SUB.get_all_level_actors() if a.get_actor_label() == label]
    assert len(matches) == 1, (label, len(matches))
    return matches[0]


def matte(name, color, roughness):
    path = "/Game/VisualPass/Materials/" + name
    material = unreal.load_asset(path)
    if material is None:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, "/Game/VisualPass/Materials", unreal.Material, unreal.MaterialFactoryNew())
    unreal.MaterialEditingLibrary.delete_all_material_expressions(material)
    base = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant3Vector)
    base.set_editor_property("constant", unreal.LinearColor(*color, 1))
    unreal.MaterialEditingLibrary.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    for prop, value in [(unreal.MaterialProperty.MP_ROUGHNESS, roughness),
                        (unreal.MaterialProperty.MP_METALLIC, 0.1),
                        (unreal.MaterialProperty.MP_SPECULAR, 0.2)]:
        constant = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant)
        constant.set_editor_property("r", value)
        unreal.MaterialEditingLibrary.connect_material_property(constant, "", prop)
    unreal.MaterialEditingLibrary.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_asset(path)
    return material


def import_centered(name):
    path = "/Game/VisualPass/Beys/" + name
    mesh = unreal.load_asset(path)
    if mesh is None:
        task = unreal.AssetImportTask()
        task.filename = os.path.join(ROOT, "_import_staging", "Normalized", name + ".fbx")
        task.destination_path = "/Game/VisualPass/Beys"
        task.destination_name = name
        task.automated = True
        task.save = True
        options = unreal.FbxImportUI()
        options.import_mesh = True
        options.import_materials = False
        options.import_textures = False
        options.import_as_skeletal = False
        options.static_mesh_import_data.combine_meshes = True
        task.options = options
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        mesh = unreal.load_asset(path)
    assert isinstance(mesh, unreal.StaticMesh), path
    return mesh


def set_material(target, material):
    component = target.get_component_by_class(unreal.StaticMeshComponent)
    for index in range(component.get_num_materials()):
        component.set_material(index, material)


def exposure():
    settings = unreal.PostProcessSettings()
    for key, value in {
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_MANUAL,
        "override_auto_exposure_apply_physical_camera_exposure": True,
        "auto_exposure_apply_physical_camera_exposure": False,
        "override_auto_exposure_bias": True, "auto_exposure_bias": -4.0,
        "override_bloom_intensity": True, "bloom_intensity": 0.0,
        "override_motion_blur_amount": True, "motion_blur_amount": 0.0,
    }.items():
        settings.set_editor_property(key, value)
    return settings


def main():
    assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name().startswith("/Game/Maps/Main")
    camera = actor("BattleCamera")
    camera.set_actor_location(unreal.Vector(20, 720, 540), False, True)
    target = unreal.Vector(-35, 15, 65)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), target), False)
    camera.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)
    camera.camera_component.set_field_of_view(50)
    camera.camera_component.set_editor_property("post_process_settings", exposure())
    camera.camera_component.set_editor_property("post_process_blend_weight", 1.0)
    pp = next((a for a in SUB.get_all_level_actors() if a.get_actor_label() == "VisualExposure"), None)
    if pp is None:
        pp = SUB.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector())
        pp.set_actor_label("VisualExposure")
    pp.set_editor_property("unbound", True)
    pp.set_editor_property("priority", 100)
    pp.set_editor_property("settings", exposure())

    set_material(actor("SmoothBowl_v1"), matte("M_Bowl", (0.09, 0.105, 0.125), 0.9))
    ground = actor("GroundFallback")
    set_material(ground, matte("M_Ground", (0.045, 0.052, 0.065), 0.96))
    ground.set_actor_scale3d(unreal.Vector(60, 60, 0.15))
    colors = [(0.65, 0.035, 0.025), (0.025, 0.22, 0.65)]
    placements = [(-75, 65), (75, 65)]
    widths = []
    for index, (label, mesh_name) in enumerate([("BeyA_RedLotus", "RedLotus_Centered"), ("BeyB", "BeyB_Centered")]):
        bey = actor(label)
        component = bey.get_component_by_class(unreal.StaticMeshComponent)
        component.set_mobility(unreal.ComponentMobility.MOVABLE)
        mesh = import_centered(mesh_name)
        component.set_static_mesh(mesh)
        bounds = mesh.get_bounds()
        diameter = max(bounds.box_extent.x, bounds.box_extent.y) * 2
        scale = 44.0 / diameter
        bey.set_actor_scale3d(unreal.Vector(scale, scale, scale))
        bey.set_actor_rotation(unreal.Rotator(), False)
        x, y = placements[index]
        bey.set_actor_location(unreal.Vector(x, y, 42.5 - (bounds.origin.z - bounds.box_extent.z) * scale), False, True)
        assert abs(bounds.origin.x) < 0.01 and abs(bounds.origin.y) < 0.01
        set_material(bey, matte("M_Player%d" % (index + 1), colors[index], 0.5))
        widths.append(diameter * scale)
        text_actor = actor("Label_P%d" % (index + 1))
        text = text_actor.get_component_by_class(unreal.TextRenderComponent)
        text.set_text("P%d" % (index + 1))
        text.set_world_size(23)
        text.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
        text.set_text_render_color(unreal.Color(255, 115, 90) if index == 0 else unreal.Color(95, 175, 255))
        text.set_cast_shadow(False)
        label_location = unreal.Vector(x, y, 42.5 + bounds.box_extent.z * 2 * scale + 24)
        text_actor.set_actor_location(label_location, False, True)
        text_actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(label_location, camera.get_actor_location()), False)
        text_actor.set_actor_scale3d(unreal.Vector(1, 1, 1))
        text_actor.attach_to_actor(bey, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD,
                                   unreal.AttachmentRule.KEEP_WORLD, False)
        text.set_absolute(False, True, True)
    assert abs(widths[0] - widths[1]) < 0.01

    male = actor("MaleLead")
    male.set_actor_location(unreal.Vector(-290, -35, 0), False, True)
    male.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(male.get_actor_location(), unreal.Vector(0, 0, 0)), False)
    actor("Sun").get_component_by_class(unreal.DirectionalLightComponent).set_intensity(3.0)
    actor("SkyLight").get_component_by_class(unreal.SkyLightComponent).set_intensity(0.6)
    for label, intensity in [("FillLight", 1200), ("RimLight", 350), ("AmbientFill", 400)]:
        actor(label).get_component_by_class(unreal.LightComponent).set_intensity(intensity)
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    report = {"map": "/Game/Maps/Main", "diameters_cm": widths,
              "exposure": "manual, physical camera off, bias -4", "camera_fov": 50,
              "labels": "23 cm, camera-facing, attached to bey, absolute rotation/scale",
              "combat": "not implemented; frozen reference constants untouched"}
    with open(os.path.join(ROOT, "Tools", "formal_visual_report.json"), "w", encoding="utf-8") as output:
        json.dump(report, output, indent=2)
    unreal.EditorLevelLibrary.pilot_level_actor(camera)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_set_game_view(True)
    unreal.EditorAssetLibrary.save_directory("/Game/VisualPass", only_if_is_dirty=True, recursive=True)
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    unreal.log("FORMAL_VISUAL_PASS_SAVED")


main()
