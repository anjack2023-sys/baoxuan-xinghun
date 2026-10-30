import unreal,json,traceback
from pathlib import Path
out=Path('C:/BeybladeUE/Saved/SixSlowTraps');dest='/Game/Beyblade/Arena/SixSlowTraps'
report={}
try:
 tools=unreal.AssetToolsHelpers.get_asset_tools();mel=unreal.MaterialEditingLibrary;mats=[]
 for name,color,metal,rough in [('TrapGold',(.58,.35,.105),.78,.3),('TrapNavy',(.018,.035,.065),.3,.7),('TrapRib',(.045,.065,.09),.4,.65)]:
  m=unreal.load_asset(dest+'/M_'+name) or tools.create_asset('M_'+name,dest,unreal.Material,unreal.MaterialFactoryNew())
  mel.delete_all_material_expressions(m)
  c=mel.create_material_expression(m,unreal.MaterialExpressionConstant3Vector);c.constant=unreal.LinearColor(*color,1);mel.connect_material_property(c,'',unreal.MaterialProperty.MP_BASE_COLOR)
  for value,prop in [(metal,unreal.MaterialProperty.MP_METALLIC),(rough,unreal.MaterialProperty.MP_ROUGHNESS)]:
   n=mel.create_material_expression(m,unreal.MaterialExpressionConstant);n.r=value;mel.connect_material_property(n,'',prop)
  m.set_editor_property('two_sided',True);mel.recompile_material(m);unreal.EditorAssetLibrary.save_loaded_asset(m);mats.append(m)
 task=unreal.AssetImportTask();task.filename=str(out/'SM_SixSlowTraps.fbx');task.destination_path=dest;task.destination_name='SM_SixSlowTraps';task.automated=True;task.save=True;task.replace_existing=True
 opt=unreal.FbxImportUI();opt.import_materials=False;opt.import_textures=False;opt.import_as_skeletal=False;opt.static_mesh_import_data.combine_meshes=True;opt.static_mesh_import_data.auto_generate_collision=False;opt.static_mesh_import_data.generate_lightmap_u_vs=False;task.options=opt;tools.import_asset_tasks([task])
 mesh=unreal.load_asset(dest+'/SM_SixSlowTraps');assert mesh
 mapping={str(m.get_name())[2:]:m for m in mats}
 for i,slot in enumerate(mesh.get_editor_property('static_materials')):mesh.set_material(i,mapping[str(slot.material_slot_name)])
 unreal.EditorAssetLibrary.save_loaded_asset(mesh)
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 assert levels.load_level('/Game/Maps/RankedArena_AccentPreview')
 for a in actors.get_all_level_actors():
  if a.get_actor_label()=='SixSlowTraps':actors.destroy_actor(a)
 a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector());a.set_actor_label('SixSlowTraps');c=a.get_component_by_class(unreal.StaticMeshComponent);c.set_static_mesh(mesh);c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);c.set_cast_shadow(False)
 assert levels.save_current_level();report={'status':'PASS','mesh':mesh.get_path_name(),'bounds':str(mesh.get_bounds())}
except Exception:report={'status':'FAIL','error':traceback.format_exc()};unreal.log_error(report['error'])
(out/'import-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
unreal.SystemLibrary.quit_editor()
