import unreal,json,math,traceback
from pathlib import Path
out=Path('C:/BeybladeUE/Saved/ArenaImport');dest='/Game/Beyblade/Arena/Ranked_v1';levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);tools=unreal.AssetToolsHelpers.get_asset_tools();mel=unreal.MaterialEditingLibrary
report={}
def constant(mat,value,prop):
 n=mel.create_material_expression(mat,unreal.MaterialExpressionConstant);n.r=value;mel.connect_material_property(n,'',prop)
def main():
 task=unreal.AssetImportTask();task.filename=str(out/'SM_RankedArena.fbx');task.destination_path=dest;task.destination_name='SM_RankedArena';task.automated=True;task.save=True
 opt=unreal.FbxImportUI();opt.import_mesh=True;opt.import_materials=False;opt.import_textures=False;opt.import_as_skeletal=False;opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH
 opt.static_mesh_import_data.combine_meshes=True;opt.static_mesh_import_data.generate_lightmap_u_vs=False;opt.static_mesh_import_data.auto_generate_collision=False
 task.options=opt;tools.import_asset_tasks([task]);mesh=unreal.load_asset(dest+'/SM_RankedArena');assert mesh
 settings=mesh.get_editor_property('nanite_settings');settings.enabled=False;mesh.set_editor_property('nanite_settings',settings)
 metadata=json.loads((out/'materials.json').read_text(encoding='utf-8'));mats={}
 for name,data in metadata.items():
  mat=tools.create_asset('M_'+name,dest,unreal.Material,unreal.MaterialFactoryNew());assert mat
  constant(mat,data['metal'],unreal.MaterialProperty.MP_METALLIC);constant(mat,data['rough'],unreal.MaterialProperty.MP_ROUGHNESS)
  base=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector);base.constant=unreal.LinearColor(*data['base']);mel.connect_material_property(base,'',unreal.MaterialProperty.MP_BASE_COLOR)
  for path in data['images']:
   path=Path(path);texname=path.stem
   if not unreal.EditorAssetLibrary.does_asset_exist(dest+'/'+texname):
    t=unreal.AssetImportTask();t.filename=str(path);t.destination_path=dest;t.destination_name=texname;t.automated=True;t.save=True;tools.import_asset_tasks([t])
   tex=unreal.load_asset(dest+'/'+texname);assert tex,path
   if texname.endswith(('_Rough','_AO')):tex.set_editor_property('srgb',False)
   if texname.endswith('_N'):tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP);tex.set_editor_property('srgb',False)
   unreal.EditorAssetLibrary.save_loaded_asset(tex)
   node=mel.create_material_expression(mat,unreal.MaterialExpressionTextureSample);node.texture=tex
   prop=None
   if texname.endswith('_BC'):prop=unreal.MaterialProperty.MP_BASE_COLOR
   if texname.endswith('_Rough'):prop=unreal.MaterialProperty.MP_ROUGHNESS;node.sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR
   if texname.endswith('_AO'):prop=unreal.MaterialProperty.MP_AMBIENT_OCCLUSION;node.sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR
   if texname.endswith('_N'):prop=unreal.MaterialProperty.MP_NORMAL;node.sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
   if prop:mel.connect_material_property(node,'RGB',prop)
  if data['strength']>0:
   n=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector);n.constant=unreal.LinearColor(*[v*data['strength']*4 for v in data['emission'][:3]],1);mel.connect_material_property(n,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
  mel.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat);mats[name]=mat
 slots=mesh.get_editor_property('static_materials');report['materials']=[]
 for i,slot in enumerate(slots):
  name=str(slot.material_slot_name);assert name in mats,name;mesh.set_material(i,mats[name]);report['materials'].append(name)
 unreal.EditorAssetLibrary.save_loaded_asset(mesh)
 assert unreal.EditorAssetLibrary.duplicate_asset('/Game/Maps/StadiumIndustrialPolish_v1','/Game/Maps/RankedArena_v1')
 assert levels.load_level('/Game/Maps/RankedArena_v1')
 old=[]
 for a in actors.get_all_level_actors():
  tags=[str(t) for t in a.tags];label=a.get_actor_label();c=a.get_component_by_class(unreal.StaticMeshComponent)
  old.append({'label':label,'tags':tags,'location':str(a.get_actor_location())})
  if c and not any(t in tags for t in ['BattleBowl','BattleP1','BattleP2','BattleGround']):actors.destroy_actor(a)
  if 'BattleGround' in tags:
   a.set_actor_location(unreal.Vector(0,0,-5),False,True);a.set_actor_scale3d(unreal.Vector(30,30,.1));a.set_actor_hidden_in_game(True);c.set_collision_profile_name('BlockAll')
 report['old_actors']=old
 a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector());a.set_actor_label('RankedArenaEnvironment');a.tags=['RankedArena'];c=a.get_component_by_class(unreal.StaticMeshComponent);c.set_static_mesh(mesh);c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
 report['bounds']=str(a.get_actor_bounds(False))
 # Separate, predictable collision avoids a convex hull filling the entire stadium.
 def blocker(name,loc,scale,shape='/Engine/BasicShapes/Cube'):
  a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc));a.set_actor_label(name);c=a.get_component_by_class(unreal.StaticMeshComponent);c.set_static_mesh(unreal.load_asset(shape));c.set_collision_profile_name('BlockAll');a.set_actor_scale3d(unreal.Vector(*scale));a.set_actor_hidden_in_game(True);return a
 blocker('ArenaBowlSafety',(0,0,100),(5.1,5.1,2),'/Engine/BasicShapes/Cylinder')
 for i in range(32):
  angle=i*math.tau/32;a=blocker('ArenaWalkBoundary_%02d'%i,(720*math.cos(angle),720*math.sin(angle),110),(.3,1.5,2.4));a.set_actor_rotation(unreal.Rotator(0,math.degrees(angle),0),False)
 for i in range(8):
  angle=i*math.tau/8;loc=unreal.Vector(750*math.cos(angle),750*math.sin(angle),620);aim=unreal.Vector(200*math.cos(angle),200*math.sin(angle),100)
  a=actors.spawn_actor_from_class(unreal.RectLight,loc);a.set_actor_label('ArenaSoftLight_%02d'%i);a.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(loc,aim),False);c=a.get_component_by_class(unreal.RectLightComponent);c.set_intensity(16000);c.set_editor_property('attenuation_radius',2200);c.set_editor_property('source_width',240);c.set_editor_property('source_height',180);c.set_light_color(unreal.LinearColor(.8,.9,1,1))
 assert levels.save_current_level();report['status']='PASS'
try:main()
except Exception:report['status']='FAIL';report['error']=traceback.format_exc()
(out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
