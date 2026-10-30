import unreal,json,traceback
from pathlib import Path
root=Path(r'C:/Users/Administrator/Desktop/ai陀螺游戏/bey-art-refs/ai-avatar-button');tools=unreal.AssetToolsHelpers.get_asset_tools();report={}
try:
 unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
 for folder,label in [('new-character-1','DeepSeek'),('new-character-2','Doubao')]:
  dest='/Game/FeelLab/Characters/AIAvatars/'+label;mesh=unreal.load_asset(dest+'/SK_'+label);assert mesh
  t=unreal.AssetImportTask();t.filename=str(root/folder/'only_animation.fbx');t.destination_path=dest;t.destination_name='A_LaunchTest';t.automated=True;t.save=True;t.factory=unreal.FbxFactory()
  opt=unreal.FbxImportUI();opt.automated_import_should_detect_type=False;opt.import_as_skeletal=True;opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_ANIMATION;opt.import_mesh=False;opt.import_animations=True;opt.skeleton=mesh.skeleton;opt.anim_sequence_import_data.set_editor_property('animation_length',unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME);t.options=opt;tools.import_asset_tasks([t]);anim=unreal.load_asset(dest+'/A_LaunchTest');assert anim,list(t.imported_object_paths);unreal.EditorAssetLibrary.save_directory(dest,True,True);report[label]={'animation':anim.get_path_name(),'length':anim.get_play_length(),'mesh':mesh.get_path_name()}
 report['status']='PASS'
except Exception:report={'status':'FAIL','error':traceback.format_exc()};unreal.log_error(report['error'])
(root/'new-character-animation-test-import.json').write_text(json.dumps(report,indent=2),encoding='utf8');unreal.SystemLibrary.quit_editor()


