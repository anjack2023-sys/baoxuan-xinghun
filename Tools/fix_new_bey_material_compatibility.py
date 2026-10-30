import unreal,json
from pathlib import Path
sub=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem);report=[]
for name in ['Huangkai','Cuipan','Shuanghuan']:
 m=unreal.load_asset('/Game/Beyblade/Art/Tripo_v1/SM_'+name);settings=sub.get_nanite_settings(m);before=settings.enabled;settings.enabled=False;sub.set_nanite_settings(m,settings,True)
 assert not sub.get_nanite_settings(m).enabled;assert unreal.EditorAssetLibrary.save_loaded_asset(m,False);report.append({'mesh':m.get_path_name(),'nanite_before':before,'nanite_after':False,'material':m.static_materials[0].material_interface.get_path_name()})
Path('C:/BeybladeUE/Saved/new-beys-material-compatibility.json').write_text(json.dumps({'status':'PASS','meshes':report},indent=2))
