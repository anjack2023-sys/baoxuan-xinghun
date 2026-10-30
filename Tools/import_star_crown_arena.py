import unreal,json,math,traceback
from pathlib import Path
out=Path(r'C:/Users/Administrator/Desktop/ai陀螺游戏/bey-art-refs/star-crown-battle-table');report={};dest='/Game/Beyblade/Arena/StarCrown_v1';levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);tools=unreal.AssetToolsHelpers.get_asset_tools();mel=unreal.MaterialEditingLibrary

def constant(mat,value,prop):
 n=mel.create_material_expression(mat,unreal.MaterialExpressionConstant);n.r=value;mel.connect_material_property(n,'',prop)
def main():
 meta=json.loads((out/'materials.json').read_text(encoding='utf-8'));mats={}
 for name,data in meta.items():
  mat=unreal.load_asset(dest+'/M_'+name) or tools.create_asset('M_'+name,dest,unreal.Material,unreal.MaterialFactoryNew());assert mat;mel.delete_all_material_expressions(mat)
  color=data['base']
  if name=='MAT_Trim_Gold' or name=='MAT_Emblem_Gold':color=[.55,.32,.09,1]
  if name=='MAT_Truss_Dark':color=[.026,.038,.055,1]
  base=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector);base.constant=unreal.LinearColor(*color);mel.connect_material_property(base,'',unreal.MaterialProperty.MP_BASE_COLOR)
  constant(mat,data['metal'],unreal.MaterialProperty.MP_METALLIC);constant(mat,data['rough'],unreal.MaterialProperty.MP_ROUGHNESS)
  if name=='MAT_Table_Silver':mat.set_editor_property('two_sided',True)
  if data['glass']:
   mat.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT);mat.set_editor_property('two_sided',True);constant(mat,.15,unreal.MaterialProperty.MP_OPACITY)
  for path in data['images']:
   path=Path(path);name_tex=path.stem
   if not path.exists():continue
   if not name_tex.endswith(('_Rough','_N')):continue
   tex=unreal.load_asset(dest+'/'+name_tex)
   if not tex:
    t=unreal.AssetImportTask();t.filename=str(path);t.destination_path=dest;t.destination_name=name_tex;t.automated=True;t.save=True;tools.import_asset_tasks([t]);tex=unreal.load_asset(dest+'/'+name_tex)
   assert tex;tex.set_editor_property('srgb',False)
   if name_tex.endswith('_N'):tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP)
   unreal.EditorAssetLibrary.save_loaded_asset(tex);node=mel.create_material_expression(mat,unreal.MaterialExpressionTextureSample);node.texture=tex
   node.sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if name_tex.endswith('_N') else unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR
   mel.connect_material_property(node,'RGB',unreal.MaterialProperty.MP_NORMAL if name_tex.endswith('_N') else unreal.MaterialProperty.MP_ROUGHNESS)
  if data['strength']>0:
   n=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector);n.constant=unreal.LinearColor(*[v*data['strength'] for v in data['emission'][:3]],1);mel.connect_material_property(n,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
  mel.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat);mats[name]=mat
 meshes={}
 for name in ['SM_StarCrown_Arena80','SM_ApprovedArena']+['SM_Score_'+str(i) for i in range(11)]:
  mesh=unreal.load_asset(dest+'/'+name)
  task=unreal.AssetImportTask();task.filename=str(out/(name+'.fbx'));task.destination_path=dest;task.destination_name=name;task.automated=True;task.save=True;task.replace_existing=True
  opt=unreal.FbxImportUI();opt.import_mesh=True;opt.import_materials=False;opt.import_textures=False;opt.import_as_skeletal=False;opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH;opt.static_mesh_import_data.combine_meshes=True;opt.static_mesh_import_data.auto_generate_collision=False;opt.static_mesh_import_data.generate_lightmap_u_vs=False;opt.static_mesh_import_data.transform_vertex_to_absolute=True
  task.options=opt;tools.import_asset_tasks([task]);mesh=unreal.load_asset(dest+'/'+name)
  assert mesh,name
  ns=mesh.get_editor_property('nanite_settings');ns.enabled=False;mesh.set_editor_property('nanite_settings',ns)
  for i,slot in enumerate(mesh.get_editor_property('static_materials')):
   matname=str(slot.material_slot_name);assert matname in mats,matname;mesh.set_material(i,mats[matname])
  body=mesh.get_editor_property('body_setup');body.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);body.set_editor_property('double_sided_geometry',True);unreal.EditorAssetLibrary.save_loaded_asset(mesh);meshes[name]=mesh
  report[name]={'bounds':str(mesh.get_bounds()),'material_count':len(mesh.get_editor_property('static_materials'))}
 assert levels.load_level('/Game/Maps/RankedArena_v1')
 # Rebuild only the isolated new map; retain its calibrated combat actors and camera.
 for a in list(actors.get_all_level_actors()):
  tags=[str(t) for t in a.tags];c=a.get_component_by_class(unreal.StaticMeshComponent)
  if c and not any(t in tags for t in ['BattleBowl','BattleP1','BattleP2','BattleGround']):actors.destroy_actor(a);continue
  if isinstance(a,(unreal.Light,unreal.PostProcessVolume,unreal.TextRenderActor)):actors.destroy_actor(a);continue
  if 'BattleBowl' in tags:
   c.set_static_mesh(meshes['SM_StarCrown_Arena80']);c.set_editor_property('override_materials',[]);a.set_actor_scale3d(unreal.Vector(1,1,1));a.set_actor_location_and_rotation(unreal.Vector(),unreal.Rotator(),False,True);c.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
   hit=c.line_trace_component(unreal.Vector(0,0,600),unreal.Vector(0,0,-200),True,False,False);assert hit and abs(hit[0].z-42)<1,str(hit)
  if 'BattleGround' in tags:
   a.set_actor_location(unreal.Vector(0,0,-5),False,True);a.set_actor_scale3d(unreal.Vector(30,30,.1));a.set_actor_hidden_in_game(True);c.set_collision_profile_name('BlockAll')
  if any(t in tags for t in ['ArenaScoreP1','ArenaScoreP2']):actors.destroy_actor(a);continue
  if 'BattleCamera' in tags:
   a.get_component_by_class(unreal.CameraComponent).set_editor_property('post_process_blend_weight',0.)
  if 'FaceCameraCharacter' in tags:
   report['male_original']={'location':str(a.get_actor_location()),'scale':str(a.get_actor_scale3d()),'rotation':str(a.get_actor_rotation())};a.set_actor_location(unreal.Vector(-275,0,11),False,True);a.set_actor_scale3d(unreal.Vector(1.84025,1.84025,1.84025))
 a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector());a.set_actor_label('ApprovedArenaEnvironment');a.tags=['RankedArena'];c=a.get_component_by_class(unreal.StaticMeshComponent);c.set_static_mesh(meshes['SM_ApprovedArena']);c.set_collision_profile_name('BlockAll')
 # Capsule obstacle affects walking only; spinning tops remain in the custom simulation.
 a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,60));a.set_actor_label('ArenaWalkBowlSafety');c=a.get_component_by_class(unreal.StaticMeshComponent);c.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cylinder'));c.set_collision_profile_name('BlockAll');a.set_actor_scale3d(unreal.Vector(3.8,3.8,1.2));a.set_actor_hidden_in_game(True)
 # Fixed, controlled exposure and physically motivated overhead illumination.
 a=actors.spawn_actor_from_class(unreal.PostProcessVolume,unreal.Vector());a.set_actor_label('ArenaExposure');a.set_editor_property('unbound',True);ps=a.get_editor_property('settings')
 for k,v in [('override_auto_exposure_min_brightness',True),('override_auto_exposure_max_brightness',True),('auto_exposure_min_brightness',8.),('auto_exposure_max_brightness',8.),('override_auto_exposure_bias',True),('auto_exposure_bias',-2.)]:ps.set_editor_property(k,v)
 a.set_editor_property('settings',ps)
 for i in range(8):
  t=i*math.tau/8;loc=unreal.Vector(700*math.cos(t),700*math.sin(t),570);aim=unreal.Vector(250*math.cos(t),250*math.sin(t),80)
  a=actors.spawn_actor_from_class(unreal.RectLight,loc);a.set_actor_label('ArenaKey_%02d'%i);a.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(loc,aim),False);c=a.get_component_by_class(unreal.RectLightComponent);c.set_editor_property('intensity_units',unreal.LightUnits.LUMENS);c.set_intensity(12000);c.set_editor_property('source_width',220);c.set_editor_property('source_height',150);c.set_editor_property('attenuation_radius',2200);c.set_light_color(unreal.LinearColor(.85,.92,1,1))
 a=actors.spawn_actor_from_class(unreal.RectLight,unreal.Vector(0,0,580));a.set_actor_rotation(unreal.Rotator(-90,0,0),False);c=a.get_component_by_class(unreal.RectLightComponent);c.set_editor_property('intensity_units',unreal.LightUnits.LUMENS);c.set_intensity(22000);c.set_editor_property('source_width',550);c.set_editor_property('source_height',550);c.set_editor_property('attenuation_radius',1200)
 for i,x in enumerate([-65,65]):
  a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(x,-615,359));a.set_actor_label('ArenaScoreP'+str(i+1));a.tags=['ArenaScoreP'+str(i+1)];c=a.get_component_by_class(unreal.StaticMeshComponent);c.set_static_mesh(meshes['SM_Score_0']);c.set_mobility(unreal.ComponentMobility.MOVABLE);c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);c.set_cast_shadow(False)
 assert levels.save_current_level();report['status']='PASS'
try:main()
except Exception:report.update(status='FAIL',error=traceback.format_exc())
Path('C:/BeybladeUE/Saved/star-crown-import-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')

