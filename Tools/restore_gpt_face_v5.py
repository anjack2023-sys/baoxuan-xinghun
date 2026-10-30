import json, traceback
from pathlib import Path
import unreal

dest = '/Game/FeelLab/Characters/AIAvatars/GPT'
lib = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
report = {}
try:
    texture = unreal.load_asset(dest + '/T_0')
    mat = unreal.load_asset(dest + '/M_0')
    assert texture and mat
    texture.set_editor_property('max_texture_size', 8192)
    assert lib.save_loaded_asset(texture, False)
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
    report.update(status='PASS', texture=texture.get_path_name(), maximum_texture_size=8192, mesh=mesh.get_path_name())
except Exception:
    report.update(status='FAIL', error=traceback.format_exc())
    unreal.log_error(report['error'])
Path('C:/BeybladeUE/Saved/GPTFaceV5-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
unreal.SystemLibrary.quit_editor()
