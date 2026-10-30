"""Read Main, then import the original industrial stadium into an isolated preview folder."""
import json
from pathlib import Path
import unreal

root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
report = {}
def save():
    (root/'Tools/stadium_preview_inventory.json').write_text(json.dumps(report,indent=2),encoding='utf8')

try:
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.load_level('/Game/Maps/Main')
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    report['actors']=[]
    for a in actors:
        mesh=a.get_component_by_class(unreal.StaticMeshComponent)
        item={'label':a.get_actor_label(),'tags':[str(t) for t in a.tags],
              'location':str(a.get_actor_location()),'rotation':str(a.get_actor_rotation()),'scale':str(a.get_actor_scale3d())}
        if mesh:
            item.update(mesh=mesh.static_mesh.get_path_name() if mesh.static_mesh else None,
                        materials=[mesh.get_material(i).get_path_name() if mesh.get_material(i) else None for i in range(mesh.get_num_materials())])
        report['actors'].append(item)
    report['trace_docs']=str(getattr(unreal.PrimitiveComponent,'line_trace_component',None))
    report['trace_single_docs']=unreal.SystemLibrary.line_trace_single.__doc__
    report['status']='importing'
    save()
    dest='/Game/ArtPreview/IndustrialGame_v1'
    registry=unreal.AssetRegistryHelpers.get_asset_registry()
    available=[x for x in registry.get_assets_by_path(dest,recursive=True) if str(x.asset_class_path.asset_name)=='StaticMesh']
    if not available:
        task=unreal.AssetImportTask()
        task.filename=str(root/'_import_staging/StadiumIndustrial/industrial-bowl-original.glb')
        task.destination_path=dest
        task.automated=True
        task.save=True
        task.replace_existing=False
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        report['imported_paths']=list(task.imported_object_paths)
        available=[x for x in registry.get_assets_by_path(dest,recursive=True) if str(x.asset_class_path.asset_name)=='StaticMesh']
    assert available, 'No imported static mesh'
    report['meshes']=[]
    for data in available:
        mesh=data.get_asset()
        bounds=mesh.get_bounds()
        report['meshes'].append({'path':mesh.get_path_name(),'origin':str(bounds.origin),'extent':str(bounds.box_extent),
            'materials':[mesh.get_material(i).get_path_name() if mesh.get_material(i) else None for i in range(len(mesh.static_materials))]})
    report['status']='ready'
    save()
    unreal.log('STADIUM_PREVIEW_IMPORT_READY')
except Exception as e:
    import traceback
    report['error']=traceback.format_exc();report['status']='failed';save()
    unreal.log_error(report['error'])
