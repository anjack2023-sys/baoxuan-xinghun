"""Batch import only the UI assets used by the existing Canvas HUD."""
import json
from pathlib import Path
import unreal

root=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
approved=root/'docs/P3-art-inbox/approved'
batch=root/'docs/P3-art-inbox/batch2'
files={
    'Lobby':batch/'UI-01_lobby_background_v2.png',
    'Blind':batch/'UI-03_blind_card_back_v2.png',
    'Button':batch/'UI_btn_blank_v1.png',
    'PortraitChifeng':batch/'portraits/BEY_chifeng_portrait_v1.png',
    'PortraitChangxuan':batch/'portraits/BEY_changxuan_portrait_v1.png',
    'PortraitBilei':batch/'portraits/BEY_bilei_portrait_v1.png',
    'Race5':approved/'UI-09_race5_v2.png',
    'Race8':approved/'UI-09_race8_v2.png',
    'Start':approved/'UI_btn_start_v2.png',
    'Confirm':approved/'UI_btn_confirm_lineup_v2.png',
    'Rematch':approved/'UI_btn_rematch_v2.png',
    'LobbyButton':approved/'UI_btn_to_lobby_v2.png',
    'SlotEmpty':approved/'UI_bey_slot_empty_v2.png',
    'SlotSelected':approved/'UI_bey_slot_selected_v2.png',
    'SlotUsed':approved/'UI_bey_slot_used_v2.png',
    'RoundPanel':approved/'UI-07_round_panel_v2.png',
    'MatchPanel':approved/'UI-08_match_panel_v2.png',
    'Ringout':approved/'IC-01_ringout_banner_v2.png',
    'Spinout':approved/'IC-05_spinout_banner_v2.png',
    'Timeout':approved/'IC-06_timeout_momentum_banner_v2.png',
    'Draw':approved/'IC-07_draw_banner_v2.png',
    'XTR':approved/'IC-02_xtr_tag_v2.png',
}
for i in range(1,4): files[f'Order{i}']=approved/f'IC-09_order_{i}_v2.png'
for path in files.values(): assert path.is_file(),path
tasks=[]
dest='/Game/Beyblade/UI/P3'
for name,path in files.items():
    if unreal.EditorAssetLibrary.does_asset_exist(dest+'/T_'+name):continue
    task=unreal.AssetImportTask()
    task.filename=str(path);task.destination_path=dest;task.destination_name='T_'+name
    task.automated=True;task.save=True;task.replace_existing=False
    tasks.append(task)
if tasks:unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
rows=[]
for name,path in files.items():
    texture=unreal.load_asset(dest+'/T_'+name)
    assert isinstance(texture,unreal.Texture2D),name
    texture.set_editor_property('lod_group',unreal.TextureGroup.TEXTUREGROUP_UI)
    texture.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    texture.set_editor_property('mip_gen_settings',unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    texture.set_editor_property('srgb',True)
    texture.set_editor_property('never_stream',True)
    assert unreal.EditorAssetLibrary.save_loaded_asset(texture)
    rows.append({'name':name,'asset':texture.get_path_name(),'source':str(path)})
(root/'Tools/p3_ui_import.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
unreal.log('P3_UI_IMPORT_COMPLETE '+str(len(rows)))
