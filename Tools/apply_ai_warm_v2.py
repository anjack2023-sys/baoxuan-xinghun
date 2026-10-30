import json, traceback
from pathlib import Path
import unreal

root = Path('C:/Users/Administrator/Desktop/ai陀螺游戏/bey-art-refs/ai-avatar-warm-v2')
dest = '/Game/FeelLab/Characters/AIAvatars/GPT'
lib = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
report = {}

def imported(path, name, options=None):
    task = unreal.AssetImportTask()
    task.filename = str(path)
    task.destination_path = dest
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = True
    if options:
        task.options = options
        task.factory = unreal.FbxFactory()
    tools.import_asset_tasks([task])
    asset = unreal.load_asset(dest + '/' + name)
    assert asset, (name, list(task.imported_object_paths))
    return asset

def main():
    unreal.SystemLibrary.execute_console_command(None, 'Interchange.FeatureFlags.Import.FBX 0')
    old = unreal.load_asset(dest + '/SK_GPT')
    assert old and old.skeleton
    skeleton = old.skeleton
    old_slots = {str(s.material_slot_name): s.material_interface for s in old.materials}
    opt = unreal.FbxImportUI()
    opt.automated_import_should_detect_type = False
    opt.import_as_skeletal = True
    opt.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
    opt.import_mesh = True
    opt.import_animations = False
    opt.import_materials = False
    opt.import_textures = False
    opt.create_physics_asset = False
    opt.skeleton = skeleton
    opt.skeletal_mesh_import_data.set_editor_property('update_skeleton_reference_pose', False)
    opt.skeletal_mesh_import_data.import_uniform_scale = 1.
    opt.skeletal_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
    mesh = imported(root / 'SK_GPT_warm_v2.fbx', 'SK_GPT', opt)
    assert mesh.skeleton == skeleton and 170 < mesh.get_bounds().box_extent.z * 2 < 190
    slots = mesh.materials
    for i, slot in enumerate(slots):
        assert str(slot.material_slot_name) in old_slots, str(slot.material_slot_name)
        slot.material_interface = old_slots[str(slot.material_slot_name)]
        slots[i] = slot
    mesh.materials = slots
    assert lib.save_loaded_asset(skeleton, False)
    assert lib.save_loaded_asset(mesh, False)

    texture = imported(root / 'GPT_warm_albedo.png', 'T_GPT_Warm')
    texture.set_editor_property('max_texture_size', 2048)
    assert lib.save_loaded_asset(texture, False)
    for name in ['M_0', 'M_1']:
        mat = unreal.load_asset(dest + '/' + name)
        assert mat
        mel.delete_all_material_expressions(mat)
        mat.set_editor_property('two_sided', True)
        if name == 'M_0':
            color = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample)
            color.texture = texture
            output = 'RGB'
        else:
            color = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector)
            color.constant = unreal.LinearColor(.76, .72, .67, 1)
            output = ''
        mel.connect_material_property(color, output, unreal.MaterialProperty.MP_BASE_COLOR)
        rough = mel.create_material_expression(mat, unreal.MaterialExpressionConstant)
        rough.r = .82
        mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
        mel.recompile_material(mat)
        assert lib.save_loaded_asset(mat, False)
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.load_level('/Game/Maps/RankedArena_v1')
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    keys = 0
    center = 0
    exposure = 0
    for actor in actors:
        label = actor.get_actor_label()
        if label == 'ArenaExposure':
            settings = actor.get_editor_property('settings')
            settings.set_editor_property('override_auto_exposure_bias', True)
            settings.set_editor_property('auto_exposure_bias', -2.25)
            actor.set_editor_property('settings', settings)
            exposure += 1
        if isinstance(actor, unreal.RectLight):
            loc = actor.get_actor_location()
            is_key = label.startswith('ArenaKey_')
            is_center = abs(loc.x) < 1 and abs(loc.y) < 1 and abs(loc.z - 580) < 1
            if is_key or is_center:
                component = actor.get_component_by_class(unreal.RectLightComponent)
                component.set_intensity(9500 if is_key else 16000)
                component.set_light_color(unreal.LinearColor(1, 1, 1, 1))
                component.set_editor_property('use_temperature', True)
                component.set_editor_property('temperature', 4300.)
                keys += int(is_key)
                center += int(is_center)
    assert (keys, center, exposure) == (8, 1, 1), (keys, center, exposure)
    assert levels.save_current_level()
    report.update(status='PASS', lights=keys, center=center, exposure_bias=-2.25, temperature=4300, skeleton=skeleton.get_path_name(), slots=list(old_slots))

try:
    main()
except Exception:
    report.update(status='FAIL', error=traceback.format_exc())
    unreal.log_error(report['error'])
(root / 'unreal-warm-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
unreal.SystemLibrary.quit_editor()
