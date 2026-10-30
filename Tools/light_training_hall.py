import unreal,json
from pathlib import Path
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert levels.load_level('/Game/Maps/StadiumIndustrialPolish_v1')
rows=[]
for a in actors.get_all_level_actors():
 if isinstance(a,unreal.PostProcessVolume):
  settings=a.get_editor_property('settings');old=settings.get_editor_property('auto_exposure_bias')
  if a.get_actor_label()=='GrokArtExposure':
   settings.set_editor_property('auto_exposure_bias',-2.6);a.set_editor_property('settings',settings)
  rows.append({'actor':a.get_actor_label(),'old_exposure':old,'new_exposure':a.get_editor_property('settings').get_editor_property('auto_exposure_bias')})
 if a.get_actor_label()=='CharacterSoftFill':a.get_component_by_class(unreal.RectLightComponent).set_intensity(1600)
def rect(name,loc,target,power,color):
 a=next((a for a in actors.get_all_level_actors() if a.get_actor_label()==name),None)
 if not a:a=actors.spawn_actor_from_class(unreal.RectLight,unreal.Vector(*loc));a.set_actor_label(name)
 a.set_actor_location(unreal.Vector(*loc),False,True);a.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*loc),unreal.Vector(*target)),False)
 c=a.get_component_by_class(unreal.RectLightComponent);c.set_mobility(unreal.ComponentMobility.MOVABLE);c.set_editor_property('intensity_units',unreal.LightUnits.LUMENS);c.set_intensity(power);c.set_light_color(unreal.LinearColor(*color,1));c.set_editor_property('source_width',260);c.set_editor_property('source_height',260);c.set_editor_property('attenuation_radius',1300)
 rows.append({'actor':name,'lumens':power,'location':loc})
rect('TrainingHall_MaleFace',(-120,180,260),(-410,-35,180),2400,(1,.94,.87))
rect('TrainingHall_FemaleFace',(140,220,260),(410,35,180),2400,(1,.94,.87))
rect('TrainingHall_EnvironmentFill',(0,600,650),(0,0,0),4500,(.78,.86,1))
assert levels.save_current_level()
Path('C:/BeybladeUE/Saved/training-lobby-lighting.json').write_text(json.dumps({'status':'PASS','changes':rows},indent=2))
