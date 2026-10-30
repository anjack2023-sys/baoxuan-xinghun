import unreal,json
from pathlib import Path
unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
dest='/Game/FeelLab/Characters/PortraitRefinedV3/Male';old=unreal.load_asset(dest+'/SK_MaleIdle')
s=unreal.FbxImportUI();s.automated_import_should_detect_type=False;s.import_as_skeletal=True;s.mesh_type_to_import=unreal.FBXImportType.FBXIT_SKELETAL_MESH;s.import_mesh=True;s.import_animations=False;s.import_materials=False;s.import_textures=False;s.create_physics_asset=False;s.skeleton=old.skeleton
s.skeletal_mesh_import_data.import_uniform_scale=.01;s.skeletal_mesh_import_data.normal_import_method=unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
s.skeletal_mesh_import_data.compute_weighted_normals=False
t=unreal.AssetImportTask();t.filename='C:/BeybladeUE/art/portrait-refine-v1/male-refined-idle-normals.fbx';t.destination_path=dest;t.destination_name='SK_MaleIdleLit';t.automated=True;t.save=True;t.replace_existing=True;t.options=s;t.factory=unreal.FbxFactory()
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);m=unreal.load_asset(dest+'/SK_MaleIdleLit');assert m and m.skeleton==old.skeleton
sys=unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem);settings=sys.get_lod_build_settings(m,0)
for key,value in [('recompute_normals',False),('recompute_tangents',False),('compute_weighted_normals',False),('remove_degenerates',False),('use_high_precision_tangent_basis',True)]:settings.set_editor_property(key,value)
sys.set_lod_build_settings(m,0,settings)
slots=m.materials
for i in range(len(slots)):
 slot=slots[i];slot.material_interface=unreal.load_asset(dest+'/M_Portrait');slots[i]=slot
m.materials=slots
assert abs(m.get_bounds().box_extent.z/old.get_bounds().box_extent.z-1)<.001
assert unreal.EditorAssetLibrary.save_loaded_asset(m,False)
Path('C:/BeybladeUE/Saved/idle-lit-import.json').write_text(json.dumps({'status':'PASS','mesh':m.get_path_name(),'settings':str(sys.get_lod_build_settings(m,0))},indent=2))
