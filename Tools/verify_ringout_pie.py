"""Read the actual first 4242 ringout in Main PIE; never override transforms."""
import json
import os
import unreal

root = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
assert world and "UEDPIE" in world.get_path_name()
mode = unreal.GameplayStatics.get_game_mode(world)
assert mode.get_class().get_name() == "PrototypeBattleMode"
actors = {a.get_actor_label(): a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)}
loser = actors["BeyA_RedLotus"]
p = loser.get_actor_location()
assert abs(p.z - 0.5) < 0.01, "Wait for first seed 4242 ringout to land"
assert (p.x*p.x + p.y*p.y)**0.5 > 270, "Must clear rim with full bey diameter"
assert loser.get_component_by_class(unreal.StaticMeshComponent).is_simulating_physics() is False
assert actors["Label_P1"].get_attach_parent_actor() == loser
controller = unreal.GameplayStatics.get_player_controller(world, 0)
assert controller.get_view_target().actor_has_tag("BattleCamera")
shot = os.path.join(root, "screenshots", "main_ringout_landed_PIE.png").replace("\\", "/")
unreal.SystemLibrary.execute_console_command(world, 'HighResShot 1280x720 filename="%s"' % shot, controller)
with open(os.path.join(root, "Tools", "ringout_pie_verification.json"), "w", encoding="utf-8") as f:
    json.dump({"result":"PASS", "world":world.get_path_name(), "loser_location_cm":[p.x,p.y,p.z],
               "ground_contact_z_cm":0.5, "label_attached":True, "chaos_simulation":False, "screenshot":shot}, f, indent=2)
unreal.log("RINGOUT_PIE_VERIFICATION_PASS")
