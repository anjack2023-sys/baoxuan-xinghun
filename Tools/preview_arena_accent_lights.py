import json, traceback
from pathlib import Path
import unreal

source = '/Game/Maps/RankedArena_v1'
preview = '/Game/Maps/RankedArena_AccentPreview'
lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
result = {}
try:
    assert lib.does_asset_exist(preview), 'Preview copy missing.'
    assert levels.load_level(preview)
    lights = [
        ('Preview_Lavender_Left', (-550, 0, 290), (0.52, 0.30, 1.0), 2200, 600),
        ('Preview_Lavender_Right', (550, 0, 290), (0.52, 0.30, 1.0), 2200, 600),
        ('Preview_Blue_Far', (0, -720, 300), (0.20, 0.52, 1.0), 3200, 700),
        ('Preview_Blue_Near', (0, 720, 300), (0.20, 0.52, 1.0), 3200, 700),
    ]
    for name, pos, color, power, radius in lights:
        actor = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(*pos))
        assert actor
        actor.set_actor_label(name)
        component = actor.get_component_by_class(unreal.PointLightComponent)
        component.set_intensity(power)
        component.set_light_color(unreal.LinearColor(*color, 1))
        component.set_editor_property('attenuation_radius', radius)
        component.set_editor_property('source_radius', 120.)
        component.set_cast_shadows(False)
    assert levels.save_current_level()
    result = {'status': 'PASS', 'preview': preview, 'lights': [x[0] for x in lights]}
except Exception:
    result = {'status': 'FAIL', 'error': traceback.format_exc()}
    unreal.log_error(result['error'])
Path('C:/BeybladeUE/Saved/ArenaAccentPreview-report.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
unreal.SystemLibrary.quit_editor()
