import unreal
l=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);assert l.load_level('/Game/Maps/RankedArena_v1')
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
 if any(str(t) in ['ArenaScoreP1','ArenaScoreP2'] for t in a.tags):a.get_component_by_class(unreal.StaticMeshComponent).set_mobility(unreal.ComponentMobility.MOVABLE)
l.save_current_level()
