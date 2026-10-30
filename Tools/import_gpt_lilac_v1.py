import json, traceback
from pathlib import Path
import unreal

dest = '/Game/FeelLab/Characters/AIAvatars/GPT'
lib = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
result = {}
try:
    task = unreal.AssetImportTask()
    task.filename = 'C:/Users/Administrator/Desktop/ai陀螺游戏/bey-art-refs/ai-avatar-lilac-v1/GPT_lilac.png'
    task.destination_path = dest
    task.destination_name = 'T_GPT_Lilac'
    task.automated = True
    task.save = True
    task.replace_existing = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.load_asset(dest + '/T_GPT_Lilac')
    assert texture
    texture.set_editor_property('max_texture_size', 8192)
    assert lib.save_loaded_asset(texture, False)
    mat = unreal.load_asset(dest + '/M_0')
    assert mat
    mel.delete_all_material_expressions(mat)
    mat.set_editor_property('two_sided', True)
    sample = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample)
    sample.texture = texture
    assert mel.connect_material_property(sample, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
    rough = mel.create_material_expression(mat, unreal.MaterialExpressionConstant)
    rough.r = .82
    assert mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(mat)
    assert lib.save_loaded_asset(mat, False)
    mesh = unreal.load_asset(dest + '/SK_GPT')
    assert mesh and mesh.skeleton and mesh.materials[0].material_interface == mat
    result = {'status':'PASS','texture':texture.get_path_name(),'mesh':mesh.get_path_name()}
except Exception:
    result = {'status':'FAIL','error':traceback.format_exc()}
    unreal.log_error(result['error'])
Path('C:/BeybladeUE/Saved/GPTLilacV1-report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
unreal.SystemLibrary.quit_editor()
