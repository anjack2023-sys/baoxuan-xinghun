import unreal,json,traceback,math
from pathlib import Path
root=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
report={"status":"FAIL"}
try:
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.load_level('/Game/Maps/StadiumIndustrialPolish_v1')
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    bowl=next(a for a in actors if unreal.Name('BattleBowl') in a.tags)
    comp=bowl.get_component_by_class(unreal.StaticMeshComponent)
    mats=[comp.get_material(i) for i in range(comp.get_num_materials())]
    task=unreal.AssetImportTask();task.filename=str(root/'_import_staging/StadiumIndustrial/industrial-bowl-80-lowwall.glb')
    task.destination_path='/Game/ArtPreview/Arena80LowWall';task.automated=True;task.save=True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    reg=unreal.AssetRegistryHelpers.get_asset_registry()
    meshes=[a.get_asset() for a in reg.get_assets_by_path(task.destination_path,recursive=True) if str(a.asset_class_path.asset_name)=='StaticMesh']
    assert len(meshes)==1,str(meshes)
    stable='/Game/ArtPreview/Arena80LowWall/SM_Arena80_LowWall'
    assert unreal.EditorAssetLibrary.duplicate_asset(meshes[0].get_path_name(),stable)
    mesh=unreal.load_asset(stable)
    body=mesh.get_editor_property('body_setup');body.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    assert unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    old=comp.static_mesh;old_extent=old.get_bounds().box_extent
    comp.set_static_mesh(mesh)
    for i,m in enumerate(mats):comp.set_material(i,m)
    comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
    hit=comp.line_trace_component(unreal.Vector(0,0,600),unreal.Vector(0,0,-200),True,False,False)
    assert hit and abs(hit[0].z-42.)<2.,str(hit)
    extent=mesh.get_bounds().box_extent
    assert abs(extent.x/old_extent.x-.8)<.005 and abs(extent.y/old_extent.y-.8)<.005
    report.update(mesh=stable,xy_scale=.8,center_z=hit[0].z,old_extent=str(old_extent),new_extent=str(extent))
    heights={}
    for radius in [140,170,190,210,225]:
        x=radius*.8/math.sqrt(2)
        h=comp.line_trace_component(unreal.Vector(x,x,600),unreal.Vector(x,x,-200),True,False,False)
        heights[str(radius*.8)]=h[0].z if h else None
    report['radial_height_cm']=heights
    assert levels.save_current_level()
    report['status']='PASS'
except Exception:
    report['error']=traceback.format_exc();unreal.log_error(report['error'])
(root/'Saved/Arena80LowWall-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
