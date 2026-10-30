import unreal,json,traceback
from pathlib import Path
root=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
report={"status":"FAIL"}
try:
    mesh=unreal.load_asset('/Game/ArtPreview/Arena80LowWall/SM_Arena80_LowWall')
    sub=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    options=unreal.StaticMeshReductionOptions(auto_compute_lod_screen_size=False,reduction_settings=[unreal.StaticMeshReductionSettings(percent_triangles=1.,screen_size=1.),unreal.StaticMeshReductionSettings(percent_triangles=.10,screen_size=.0001)])
    assert sub.set_lods(mesh,options)==2
    mesh.set_minimum_lod_for_platform('Android',1)
    assert mesh.get_minimum_lod_for_platform('Android')==1
    assert sub.get_lod_count(mesh)==2
    assert unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    report.update(status='PASS',android_min_lod=1,lod0_retained=True,reduction_target=.10)
except Exception:
    report['error']=traceback.format_exc();unreal.log_error(report['error'])
(root/'Saved/Mobile-arena-lod-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
unreal.SystemLibrary.quit_editor()
