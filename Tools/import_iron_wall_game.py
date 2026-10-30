import unreal,json
from pathlib import Path
root=Path('C:/BeybladeUE');src=root/'art/iron-wall-preview-v1/game-assets';dest='/Game/Beyblade/FX/IronWall';tools=unreal.AssetToolsHelpers.get_asset_tools();mel=unreal.MaterialEditingLibrary
unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
for name in ['SM_IronWallField','SM_IronWallLines','SM_IronWallGround','SM_IronWallRipple','S_IronWallStart']:
 t=unreal.AssetImportTask();t.filename=str(src/(name+('.wav' if name.startswith('S_') else '.fbx')));t.destination_path=dest;t.destination_name=name;t.automated=True;t.save=True;t.replace_existing=True
 if name.startswith('SM_'):
  s=unreal.FbxImportUI();s.automated_import_should_detect_type=False;s.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH;s.import_as_skeletal=False;s.import_materials=False;s.import_textures=False;s.static_mesh_import_data.combine_meshes=True;s.static_mesh_import_data.auto_generate_collision=False;t.options=s;t.factory=unreal.FbxFactory()
 tools.import_asset_tasks([t]);assert unreal.load_asset(dest+'/'+name),name
for name,is_field in [('M_IronWallField',True),('M_IronWallLines',False)]:
 m=unreal.load_asset(dest+'/'+name) or tools.create_asset(name,dest,unreal.Material,unreal.MaterialFactoryNew());mel.delete_all_material_expressions(m);m.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT);m.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT);m.set_editor_property('two_sided',True)
 color=mel.create_material_expression(m,unreal.MaterialExpressionVectorParameter);color.set_editor_property('parameter_name','Tint');color.set_editor_property('default_value',unreal.LinearColor(.025,.24,1,1))
 strength=mel.create_material_expression(m,unreal.MaterialExpressionScalarParameter);strength.set_editor_property('parameter_name','Strength');strength.set_editor_property('default_value',3.0 if is_field else 3.5)
 mul=mel.create_material_expression(m,unreal.MaterialExpressionMultiply);assert mel.connect_material_expressions(color,'',mul,'A');assert mel.connect_material_expressions(strength,'',mul,'B');assert mel.connect_material_property(mul,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
 opacity=mel.create_material_expression(m,unreal.MaterialExpressionScalarParameter);opacity.set_editor_property('parameter_name','Opacity');opacity.set_editor_property('default_value',0.)
 if is_field:
  f=mel.create_material_expression(m,unreal.MaterialExpressionFresnel);f.set_editor_property('exponent',3.);f.set_editor_property('base_reflect_fraction',.035)
  a=mel.create_material_expression(m,unreal.MaterialExpressionMultiply);mel.connect_material_expressions(f,'',a,'A');mel.connect_material_expressions(opacity,'',a,'B');assert mel.connect_material_property(a,'',unreal.MaterialProperty.MP_OPACITY)
 else:assert mel.connect_material_property(opacity,'',unreal.MaterialProperty.MP_OPACITY)
 mel.recompile_material(m);assert unreal.EditorAssetLibrary.save_loaded_asset(m,False)
report=[]
for name in ['SM_IronWallField','SM_IronWallLines','SM_IronWallGround','SM_IronWallRipple']:
 m=unreal.load_asset(dest+'/'+name);mat=unreal.load_asset(dest+('/M_IronWallField' if name.endswith('Field') else '/M_IronWallLines'))
 for i in range(len(m.static_materials)):m.set_material(i,mat)
 assert unreal.EditorAssetLibrary.save_loaded_asset(m,False);report.append({'mesh':m.get_path_name(),'bounds':str(m.get_bounds())})
(root/'Saved/iron-wall-import.json').write_text(json.dumps({'status':'PASS','assets':report},indent=2))
