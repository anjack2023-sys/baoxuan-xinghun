import unreal
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert levels.load_level('/Game/Maps/StadiumIndustrialPolish_v1')
for a in actors.get_all_level_actors():
 if a.get_actor_label() in ('TrainingHall_MaleFace','TrainingHall_FemaleFace'):
  c=a.get_component_by_class(unreal.RectLightComponent);c.set_cast_shadows(False)
  if a.get_actor_label()=='TrainingHall_FemaleFace':c.set_intensity(1100)
assert levels.save_current_level()
