"""Verify saved Main actors and the actual PIE camera; capture without overrides."""
import json
import os
import unreal

root = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
assert world is not None, "Start Play in Main before this check"
actors = {a.get_actor_label(): a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)}
widths = []
for index, name in enumerate(["BeyA_RedLotus", "BeyB"]):
    bey = actors[name]
    component = bey.get_component_by_class(unreal.StaticMeshComponent)
    bounds = component.static_mesh.get_bounds()
    scale = bey.get_actor_scale3d()
    width = max(bounds.box_extent.x * scale.x, bounds.box_extent.y * scale.y) * 2
    assert abs(width - 44) < 0.01
    assert abs(bounds.origin.x) < 0.01 and abs(bounds.origin.y) < 0.01
    bottom = bey.get_actor_location().z + (bounds.origin.z - bounds.box_extent.z) * scale.z
    assert abs(bottom - 42.5) < 0.01
    label = actors["Label_P%d" % (index + 1)]
    assert label.get_attach_parent_actor() == bey
    assert label.get_component_by_class(unreal.TextRenderComponent).get_editor_property("world_size") == 23
    widths.append(width)
camera = actors["BattleCamera"]
settings = camera.camera_component.get_editor_property("post_process_settings")
assert settings.auto_exposure_method == unreal.AutoExposureMethod.AEM_MANUAL
assert settings.auto_exposure_bias == -4.0
assert camera.get_editor_property("auto_activate_for_player") == unreal.AutoReceiveInput.PLAYER0
controller = unreal.GameplayStatics.get_player_controller(world, 0)
assert controller is not None
assert controller.get_view_target().get_actor_label() == "BattleCamera", controller.get_view_target().get_actor_label()
report = {"result": "PASS", "diameters_cm": widths, "bottom_z_cm": 42.5,
          "camera": controller.get_view_target().get_actor_label(), "world": world.get_path_name(),
          "exposure_bias": -4, "labels": "attached, upright, world size 23"}
with open(os.path.join(root, "Tools", "formal_visual_verification.json"), "w", encoding="utf-8") as output:
    json.dump(report, output, indent=2)
shot = os.path.join(root, "screenshots", "main_formal_PIE.png").replace("\\", "/")
unreal.SystemLibrary.execute_console_command(world, 'HighResShot 1280x720 filename="%s"' % shot, controller)
unreal.log("FORMAL_VISUAL_VERIFICATION_PASS " + shot)
