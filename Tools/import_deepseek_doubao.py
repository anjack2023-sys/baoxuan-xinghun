import unreal, json, traceback
from pathlib import Path
root=Path(r'C:/Users/Administrator/Desktop/ai陀螺游戏/bey-art-refs/ai-avatar-button');tools=unreal.AssetToolsHelpers.get_asset_tools();lib=unreal.EditorAssetLibrary;report={}
try:
 unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
 for folder,label in [('new-character-1','DeepSeek'),('new-character-2','Doubao')]:
  dest='/Game/FeelLab/Characters/AIAvatars/'+label; t=unreal.AssetImportTask();t.filename=str(root/folder/'game_launch.fbx');t.destination_path=dest;t.destination_name='SK_'+label;t.automated=True;t.save=True;t.replace_existing=False;t.factory=unreal.FbxFactory()
  opt=unreal.FbxImportUI();opt.automated_import_should_detect_type=False;opt.import_as_skeletal=True;opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_SKELETAL_MESH;opt.import_mesh=True;opt.import_animations=True;opt.import_materials=True;opt.import_textures=True;opt.create_physics_asset=False;t.options=opt;tools.import_asset_tasks([t]);mesh=unreal.load_asset(dest+'/SK_'+label);assert mesh, list(t.imported_object_paths);lib.save_directory(dest,True,True);report[label]=list(t.imported_object_paths)
 report['status']='PASS'
except Exception:report={'status':'FAIL','error':traceback.format_exc()};unreal.log_error(report['error'])
(root/'new-character-import-report.json').write_text(json.dumps(report,indent=2),encoding='utf8');unreal.SystemLibrary.quit_editor()
