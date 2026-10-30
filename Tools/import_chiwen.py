import unreal,json
from pathlib import Path
dest='/Game/Beyblade/FX/Chiwen';unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
for name in ['SM_ChiwenFlames']:
 t=unreal.AssetImportTask();t.filename='C:/BeybladeUE/art/chiwen-v1/'+name+'.fbx';t.destination_path=dest;t.destination_name=name;t.automated=True;t.save=True;t.replace_existing=True
 s=unreal.FbxImportUI();s.automated_import_should_detect_type=False;s.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH;s.import_as_skeletal=False;s.import_materials=False;s.import_textures=False;s.static_mesh_import_data.combine_meshes=True;s.static_mesh_import_data.auto_generate_collision=False;t.options=s;t.factory=unreal.FbxFactory()
 unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);m=unreal.load_asset(dest+'/'+name);assert m
 assert m.get_bounds().box_extent.x>20 and m.get_bounds().box_extent.x<150
 m.set_material(0,unreal.load_asset('/Game/Beyblade/FX/IronWall/M_IronWallLines'));assert unreal.EditorAssetLibrary.save_loaded_asset(m,False)
Path('C:/BeybladeUE/Saved/chiwen-import.json').write_text(json.dumps({'status':'PASS','bounds':str(m.get_bounds())}))