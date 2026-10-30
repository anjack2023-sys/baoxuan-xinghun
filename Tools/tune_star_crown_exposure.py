import unreal
l=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);assert l.load_level('/Game/Maps/RankedArena_v1')
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
 if isinstance(a,unreal.PostProcessVolume):
  p=a.get_editor_property('settings');p.set_editor_property('override_auto_exposure_bias',True);p.set_editor_property('auto_exposure_bias',-3.5);a.set_editor_property('settings',p)
l.save_current_level()
