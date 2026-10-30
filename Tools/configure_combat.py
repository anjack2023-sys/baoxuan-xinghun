"""Editor-only: persist battle references, actual bowl triangle collision and GameMode in Main."""
import json
import os
import unreal

root = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert levels.load_level("/Game/Maps/Main")
assert str(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_name()) == "Main"
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
by_label = {a.get_actor_label(): a for a in actors}
for label, tag in [("BeyA_RedLotus", "BattleP1"), ("BeyB", "BattleP2"),
                   ("SmoothBowl_v1", "BattleBowl"), ("BattleCamera", "BattleCamera"),
                   ("GroundFallback", "BattleGround")]:
    actor = by_label[label]
    tags = list(actor.tags)
    if unreal.Name(tag) not in tags:
        tags.append(unreal.Name(tag))
    actor.set_editor_property("tags", tags)
    if label.startswith("Bey"):
        mesh = actor.get_component_by_class(unreal.StaticMeshComponent)
        mesh.set_simulate_physics(False)
        mesh.set_mobility(unreal.ComponentMobility.MOVABLE)
        mesh.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)

bowl = by_label["SmoothBowl_v1"].get_component_by_class(unreal.StaticMeshComponent)
bowl.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
mesh = bowl.static_mesh
body = mesh.get_editor_property("body_setup")
body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
assert unreal.EditorAssetLibrary.save_loaded_asset(mesh)
mode = unreal.load_class(None, "/Script/BeybladePrototype.PrototypeBattleMode")
assert mode, "Build the C++ editor target first"
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
world.get_world_settings().set_editor_property("default_game_mode", mode)
assert levels.save_current_level()
with open(os.path.join(root, "Tools", "combat_setup.json"), "w", encoding="utf-8") as f:
    json.dump({"map": "/Game/Maps/Main", "mode": mode.get_path_name(),
               "bowl": mesh.get_path_name(), "collision": "visible triangle mesh, query only",
               "fixed_hz": 60, "SPIN_KICK": 1.3, "RESTITUTION": 0.9}, f, indent=2)
unreal.log("COMBAT_CONFIG_SAVED")
