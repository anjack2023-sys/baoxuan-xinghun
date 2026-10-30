import json
from pathlib import Path
import unreal

root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
source = root / 'docs/P3-art-inbox/batch2/portraits-20261027'
results = []
for name, filename in [('T_Lobby','T_Lobby_clean_v2.png'),('T_SkillAtlas','T_SkillAtlas.png')]:
    task = unreal.AssetImportTask()
    task.filename = str(source / filename)
    task.destination_path = '/Game/Beyblade/UI/P3'
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.save = False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    asset = unreal.load_asset(task.destination_path + '/' + name)
    assert isinstance(asset, unreal.Texture2D), name
    asset.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
    asset.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    asset.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    asset.set_editor_property('srgb', True)
    asset.set_editor_property('never_stream', True)
    assert unreal.EditorAssetLibrary.save_loaded_asset(asset), name
    results.append({'asset': asset.get_path_name(), 'source': task.filename})
(root / 'Saved/UISkillArtImport-20261027.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
unreal.log('UI_SKILL_ART_IMPORTED count=' + str(len(results)))
