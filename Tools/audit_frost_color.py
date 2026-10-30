import unreal,json
from pathlib import Path
name='Shuanghuan';mesh=unreal.load_asset('/Game/Beyblade/Art/Tripo_v1/SM_'+name);mat=mesh.static_materials[0].material_interface;mel=unreal.MaterialEditingLibrary
report={'class':mat.get_class().get_name(),'name':mat.get_path_name()}
if isinstance(mat,unreal.MaterialInstanceConstant):
 report['parent']=str(mat.get_editor_property('parent'));report['textures']={str(n):str(mel.get_material_instance_texture_parameter_value(mat,n)) for n in mel.get_texture_parameter_names(mat)};report['vectors']={str(n):str(mel.get_material_instance_vector_parameter_value(mat,n)) for n in mel.get_vector_parameter_names(mat)}
t=unreal.load_asset('/Game/Beyblade/Art/Tripo_v1/Shuanghuan/BEY_shuanghuan_BALANCE_side_tech_v1/Textures/Color');task=unreal.AssetExportTask();task.object=t;task.filename='C:/BeybladeUE/Saved/frost-source-color.png';task.automated=True;task.prompt=False;task.replace_identical=True;task.exporter=unreal.TextureExporterPNG();unreal.Exporter.run_asset_export_task(task)
Path('C:/BeybladeUE/Saved/frost-material-audit.json').write_text(json.dumps(report,indent=2))
