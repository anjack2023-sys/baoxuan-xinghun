import json, traceback
from pathlib import Path
import unreal

root = Path('C:/Users/Administrator/Desktop/ai陀螺游戏/bey-art-refs/ai-avatar-warm-v3')
dest = '/Game/FeelLab/Characters/AIAvatars/GPT'
lib = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
report = {}
try:
    task = unreal.AssetImportTask()
    task.filename = str(root / 'GPT_warm_albedo_v3.png')
    task.destination_path = dest
    task.destination_name = 'T_GPT_WarmV3'
    task.automated = True
    task.save = True
    task.replace_existing = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.load_asset(dest + '/T_GPT_WarmV3')
    assert texture
    texture.set_editor_property('max_texture_size', 2048)
    assert lib.save_loaded_asset(texture, False)
    mat = unreal.load_asset(dest + '/M_0')
    assert mat
    mel.delete_all_material_expressions(mat)
    mat.set_editor_property('two_sided', True)
    sample = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample)
    sample.texture = texture
    multiply = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply)
    factor = mel.create_material_expression(mat, unreal.MaterialExpressionConstant)
    factor.r = .76
    mel.connect_material_expressions(sample, 'RGB', multiply, 'A')
    mel.connect_material_expressions(factor, '', multiply, 'B')
    mel.connect_material_property(multiply, '', unreal.MaterialProperty.MP_BASE_COLOR)
    rough = mel.create_material_expression(mat, unreal.MaterialExpressionConstant)
    rough.r = .82
    mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(mat)
    assert lib.save_loaded_asset(mat, False)
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.load_level('/Game/Maps/RankedArena_v1')
    keys = center = exposure = 0
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if actor.get_actor_label() == 'ArenaExposure':
            settings = actor.get_editor_property('settings')
            settings.set_editor_property('auto_exposure_bias', -2.55)
            actor.set_editor_property('settings', settings)
            exposure += 1
        if isinstance(actor, unreal.RectLight):
            loc = actor.get_actor_location()
            is_key = actor.get_actor_label().startswith('ArenaKey_')
            is_center = abs(loc.x) < 1 and abs(loc.y) < 1 and abs(loc.z - 580) < 1
            if is_key or is_center:
                component = actor.get_component_by_class(unreal.RectLightComponent)
                component.set_intensity(8000 if is_key else 13500)
                component.set_editor_property('use_temperature', True)
                component.set_editor_property('temperature', 3500.)
                keys += int(is_key)
                center += int(is_center)
    assert (keys, center, exposure) == (8, 1, 1), (keys, center, exposure)
    assert levels.save_current_level()
    report.update(status='PASS', keys=keys, center=center, temperature=3500, exposure_bias=-2.55, material_factor=.76)
except Exception:
    report.update(status='FAIL', error=traceback.format_exc())
    unreal.log_error(report['error'])
(root / 'unreal-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
unreal.SystemLibrary.quit_editor()
