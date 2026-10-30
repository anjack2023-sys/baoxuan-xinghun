import json, traceback
from pathlib import Path
import unreal

root=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
report={}
try:
    registry=unreal.AssetRegistryHelpers.get_asset_registry()
    for name,filename in [('Chifeng','BEY_chifeng_ATTACK_tripo_v1.glb'),
                          ('Bilei','BEY_bilei_DEFENSE_tripo_v1.glb'),
                          ('Hengren','BEY_hengblade_BALANCE_tripo_v1.glb')]:
        source=root/'docs/P3-art-inbox/batch3-tripo-v1'/filename
        assert source.is_file(),source
        destination='/Game/Beyblade/Art/Tripo_v1/'+name
        stable='/Game/Beyblade/Art/Tripo_v1/SM_'+name
        if not unreal.EditorAssetLibrary.does_asset_exist(stable):
            task=unreal.AssetImportTask()
            task.filename=str(source);task.destination_path=destination
            task.automated=True;task.save=True;task.replace_existing=False
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            meshes=[a.get_asset() for a in registry.get_assets_by_path(destination,recursive=True)
                    if str(a.asset_class_path.asset_name)=='StaticMesh']
            assert len(meshes)==1,[(m.get_path_name()) for m in meshes]
            assert unreal.EditorAssetLibrary.duplicate_asset(meshes[0].get_path_name(),stable)
        mesh=unreal.load_asset(stable)
        bounds=mesh.get_bounds()
        assert bounds.box_extent.z<max(bounds.box_extent.x,bounds.box_extent.y),'Top axis is not Z'
        assert mesh.get_material(0),'Missing imported material'
        assert unreal.EditorAssetLibrary.save_loaded_asset(mesh)
        report[name]={'mesh':mesh.get_path_name(),'extent':str(bounds.box_extent),'origin':str(bounds.origin)}
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.load_level('/Game/Maps/StadiumIndustrialPolish_v1')
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    person=next(a for a in actors if a.get_actor_label()=='MaleLead')
    tags=list(person.tags)
    if 'FaceCameraCharacter' not in [str(t) for t in tags]:
        tags.append('FaceCameraCharacter');person.tags=tags
    report['person_bounds']=str(person.get_actor_bounds(False))
    for actor in actors:
        if actor.get_actor_label() in ('Label_P1','Label_P2'):
            actor.tags=list(actor.tags)+(['BeyWorldLabel'] if 'BeyWorldLabel' not in [str(t) for t in actor.tags] else [])
    if not any(a.get_actor_label()=='FaceViewBackdrop' for a in actors):
        source=next(a for a in actors if a.get_actor_label()=='ArenaDistantBackdrop')
        component=source.get_component_by_class(unreal.StaticMeshComponent)
        actor_sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        plane=actor_sub.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(6000,500,800))
        plane.set_actor_label('FaceViewBackdrop');plane.tags=['FaceBackdrop']
        plane.set_actor_rotation(unreal.MathLibrary.make_rotation_from_axes(unreal.Vector(0,1,0),unreal.Vector(0,0,1),unreal.Vector(1,0,0)),False)
        plane.set_actor_scale3d(unreal.Vector(115,72,1))
        pc=plane.get_component_by_class(unreal.StaticMeshComponent)
        pc.set_static_mesh(component.static_mesh)
        pc.set_material(0,component.get_material(0))
        pc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);pc.set_cast_shadow(False)
        plane.set_actor_hidden_in_game(True)
    assert levels.save_current_level()
    report['status']='PASS'
except Exception:
    report['status']='FAIL';report['error']=traceback.format_exc();unreal.log_error(report['error'])
finally:
    (root/'Tools/tripo_import_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    unreal.SystemLibrary.quit_editor()
