"""Read actual Main PIE actors and capture it; no runtime overrides."""
import json
import os
import unreal

root = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
assert world is not None, "Start Main Play first"
mode = unreal.GameplayStatics.get_game_mode(world)
assert mode.get_class().get_name() == "PrototypeBattleMode", mode.get_class().get_name()
controller = unreal.GameplayStatics.get_player_controller(world, 0)
assert controller.get_class().get_name() == "PrototypeBattleController"
assert controller.get_view_target().actor_has_tag("BattleCamera")
actors = {a.get_actor_label(): a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)}
for i, name in enumerate(["BeyA_RedLotus", "BeyB"]):
    bey = actors[name]
    assert bey.actor_has_tag("BattleP%d" % (i+1))
    mesh = bey.get_component_by_class(unreal.StaticMeshComponent)
    assert not mesh.is_simulating_physics()
    assert actors["Label_P%d" % (i+1)].get_attach_parent_actor() == bey
shot = os.path.join(root, "screenshots", "main_combat_PIE.png").replace("\\", "/")
unreal.SystemLibrary.execute_console_command(world, 'HighResShot 1280x720 filename="%s"' % shot, controller)
with open(os.path.join(root, "Tools", "combat_pie_verification.json"), "w", encoding="utf-8") as f:
    json.dump({"result":"PASS", "world":world.get_path_name(), "game_mode":mode.get_class().get_name(),
               "controller":controller.get_class().get_name(), "camera":controller.get_view_target().get_actor_label(),
               "labels":"attached", "chaos_simulation":False, "screenshot":shot}, f, indent=2)
unreal.log("COMBAT_PIE_VERIFICATION_PASS")
