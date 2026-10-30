import unreal,json
from pathlib import Path
rows=[]
for name in ['Chifeng','Bilei','Changxuan','Hengren','Chiwen','Huangkai','Cuipan','Shuanghuan']:
 m=unreal.load_asset('/Game/Beyblade/Art/Tripo_v1/SM_'+name);assert m,name
 n=m.get_editor_property('nanite_settings');before=n.enabled
 if before:
  n.enabled=False;m.set_editor_property('nanite_settings',n);assert unreal.EditorAssetLibrary.save_loaded_asset(m,False)
 rows.append({'name':name,'nanite_before':before,'nanite_after':m.get_editor_property('nanite_settings').enabled})
Path('C:/BeybladeUE/Saved/star-crown-top-material-compatibility.json').write_text(json.dumps({'status':'PASS','meshes':rows},indent=2))
