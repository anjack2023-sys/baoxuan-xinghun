import unreal,json
from pathlib import Path
rows=[]
for name in ['Huangkai','Cuipan','Shuanghuan']:
 mesh=unreal.load_asset('/Game/Beyblade/Art/Tripo_v1/SM_'+name)
 mats=[]
 for slot in mesh.static_materials:
  mat=slot.material_interface
  mats.append({'material':mat.get_path_name(),'textures':[t.get_path_name() for t in unreal.MaterialEditingLibrary.get_used_textures(mat)] if isinstance(mat,unreal.Material) else []})
 rows.append({'name':name,'materials':mats})
Path('C:/BeybladeUE/Saved/new-beys-materials.json').write_text(json.dumps(rows,indent=2))
