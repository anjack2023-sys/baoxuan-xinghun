import unreal,json,traceback
from pathlib import Path
root=Path(r'C:/Users/Administrator/Desktop/ai陀螺游戏/bey-art-refs/ai-avatar-button');report={};tools=unreal.AssetToolsHelpers.get_asset_tools();lib=unreal.EditorAssetLibrary;mel=unreal.MaterialEditingLibrary
unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
def task(file,dest,name,opt=None):
 t=unreal.AssetImportTask();t.filename=str(file);t.destination_path=dest;t.destination_name=name;t.automated=True;t.save=True;t.replace_existing=True
 if opt:t.options=opt;t.factory=unreal.FbxFactory()
 tools.import_asset_tasks([t]);a=unreal.load_asset(dest+'/'+name);assert a,(name,list(t.imported_object_paths));assert lib.save_loaded_asset(a,False),name;return a
def main():
 for label in ['GPT','GROK']:
  folder=root/label;meta=json.loads((folder/'asset-report.json').read_text(encoding='utf-8'));dest='/Game/FeelLab/Characters/AIAvatars/'+label
  opt=unreal.FbxImportUI();opt.automated_import_should_detect_type=False;opt.import_as_skeletal=True;opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_SKELETAL_MESH
  opt.import_mesh=True;opt.import_animations=False;opt.import_materials=False;opt.import_textures=False;opt.create_physics_asset=False
  opt.skeletal_mesh_import_data.set_editor_property('update_skeleton_reference_pose',True);opt.skeletal_mesh_import_data.import_uniform_scale=1.;opt.skeletal_mesh_import_data.normal_import_method=unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS;opt.skeletal_mesh_import_data.compute_weighted_normals=False
  mesh=task(folder/('SK_'+label+'.fbx'),dest,'SK_'+label,opt)
  assert mesh.skeleton and lib.save_loaded_asset(mesh.skeleton,False)
  assert Path(unreal.Paths.project_content_dir(),'FeelLab/Characters/AIAvatars',label,mesh.skeleton.get_name()+'.uasset').is_file()
  assert 170<mesh.get_bounds().box_extent.z*2<190,str(mesh.get_bounds())
  mats={}
  for i,source_name in enumerate(meta['body_materials']+meta['gun_materials']):
   mat=unreal.load_asset(dest+'/M_'+str(i)) or tools.create_asset('M_'+str(i),dest,unreal.Material,unreal.MaterialFactoryNew());assert mat;mel.delete_all_material_expressions(mat);mat.set_editor_property('two_sided',True)
   path=meta['textures'].get(source_name)
   if path:
    texture=unreal.load_asset(dest+'/T_'+str(i)) or task(path,dest,'T_'+str(i));texture.set_editor_property('max_texture_size',2048);lib.save_loaded_asset(texture)
    color=mel.create_material_expression(mat,unreal.MaterialExpressionTextureSample);color.texture=texture;output='RGB'
   else:
    color=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector);color.constant=unreal.LinearColor(.85,.83,.9,1);output=''
   mel.connect_material_property(color,output,unreal.MaterialProperty.MP_BASE_COLOR)
   rough=mel.create_material_expression(mat,unreal.MaterialExpressionConstant);rough.r=.72;mel.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
   soft=mel.create_material_expression(mat,unreal.MaterialExpressionMultiply);gain=mel.create_material_expression(mat,unreal.MaterialExpressionConstant);gain.r=.10;mel.connect_material_expressions(gain,'',soft,'B');mel.connect_material_expressions(color,output,soft,'A');mel.connect_material_property(soft,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
   mel.recompile_material(mat);lib.save_loaded_asset(mat);mats[source_name.replace('.','_')]=mat
  slots=mesh.materials;slot_report=[]
  for i,slot in enumerate(slots):
   name=str(slot.material_slot_name).replace('.','_');mat=mats.get(name)
   if not mat:mat=next((m for key,m in mats.items() if name.startswith(key) or key.startswith(name)),None)
   assert mat,(name,list(mats))
   slot.material_interface=mat;slots[i]=slot;slot_report.append(name)
  mesh.materials=slots
  system=unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem);settings=system.get_lod_build_settings(mesh,0)
  for k,v in [('recompute_normals',False),('recompute_tangents',False),('compute_weighted_normals',False),('remove_degenerates',False),('use_high_precision_tangent_basis',True)]:settings.set_editor_property(k,v)
  system.set_lod_build_settings(mesh,0,settings);lib.save_loaded_asset(mesh)
  clips={}
  for name in ['Idle','Walk','Run','LaunchR','LaunchL']:
   opt=unreal.FbxImportUI();opt.automated_import_should_detect_type=False;opt.import_as_skeletal=True;opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_ANIMATION;opt.import_mesh=False;opt.import_animations=True;opt.import_materials=False;opt.import_textures=False;opt.skeleton=mesh.skeleton
   opt.anim_sequence_import_data.set_editor_property('animation_length',unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
   opt.anim_sequence_import_data.import_uniform_scale=1.
   a=task(folder/('A_'+name+'.fbx'),dest,'A_'+name,opt);assert isinstance(a,unreal.AnimSequence) and a.get_editor_property('skeleton')==mesh.skeleton
   expected=meta['actions'][name]['duration'];assert abs(a.get_play_length()-expected)<.04,(name,a.get_play_length(),expected)
   clips[name]=a.get_play_length()
  lib.save_directory(dest,True,True)
  report[label]={'skeleton':mesh.skeleton.get_path_name(),'mesh':mesh.get_path_name(),'bounds':str(mesh.get_bounds()),'materials':slot_report,'animations':clips}
 report['status']='PASS'
try:main()
except Exception:report.update(status='FAIL',error=traceback.format_exc());unreal.log_error(report['error'])
(root/'unreal-import-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');unreal.SystemLibrary.quit_editor()

