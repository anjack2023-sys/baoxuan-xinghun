import unreal,time,json,re,traceback
from pathlib import Path
mode_name=re.search(r'-ExtraFx=(gold|stone|frost)',unreal.SystemLibrary.get_command_line()).group(1)
cfg={'gold':('Six','SM_Huangkai','GoldFxEffect','Gold_IronWallLines','IRON_WALL_VFX_BEGIN',None,0,5),'stone':('Seven','SM_Cuipan','StoneFxEffect','Stone_ChangxuanRing0','CHANGXUAN_VFX_BEGIN',5.,0,4),'frost':('Eight','SM_Shuanghuan','FrostFxEffect','Frost_HengrenAttackRing','HENGREN_VFX_BEGIN',3.,1,4)}[mode_name]
key,mesh_name,fx_name,main_name,begin,duration,target_index,part_count=cfg
out=Path('C:/BeybladeUE/Saved/EightBeyCheck')/mode_name;out.mkdir(parents=True,exist_ok=True);log=Path('C:/BeybladeUE/Saved/extra-'+mode_name+'-pie.log')
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);assert levels.load_level('/Game/Maps/StadiumIndustrialPolish_v1')
cam=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.CameraActor,unreal.Vector());cam.tags=['ExtraReviewCamera']
s={'wall':time.monotonic(),'t':0.,'prev':None,'sent':set(),'shots':set(),'samples':[],'fired':False,'replay':set()}
events=[(1,'SpaceBar'),(2,key),(2.4,'One'),(2.8,'Two'),(3.5,'SpaceBar'),(5,'SpaceBar')]
def inject(pc,key):
 sub=next(o for o in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if 'Default__' not in o.get_name())
 action=next(a for a in unreal.ObjectIterator(unreal.InputAction) if a.get_outer()==pc and any(str(k.get_editor_property('key_name'))==key for k in sub.query_keys_mapped_to_action(a)))
 sub.inject_input_vector_for_action(action,unreal.Vector(1,0,0),[],[])
def finish(status,error=None):
 (out/'report.json').write_text(json.dumps({'status':status,'error':error,'mode':mode_name,'fire_at':s.get('fire_at'),'consume_at':s.get('consume_at'),'natural_hits':s.get('hits',0),'samples':s['samples']},indent=2))
 unreal.unregister_slate_post_tick_callback(s['h']);levels.editor_request_end_play();unreal.SystemLibrary.quit_editor()
def shot(world,pc,name):
 s['shots'].add(name);unreal.SystemLibrary.execute_console_command(world,'HighResShot 1280x720 filename='+str(out/(name+'.png')).replace('\\','/'),pc)
def tick(dt):
 try:
  assert time.monotonic()-s['wall']<180,'PIE timeout'
  worlds=unreal.EditorLevelLibrary.get_pie_worlds(False)
  if not worlds:return
  world=worlds[0];now=unreal.GameplayStatics.get_time_seconds(world)
  if s['prev'] is not None:s['t']+=min(max(now-s['prev'],0),.1)
  s['prev']=now;t=s['t'];pc=unreal.GameplayStatics.get_player_controller(world,0);mode=unreal.GameplayStatics.get_game_mode(world)
  for i,(at,k) in enumerate(events):
   if t>=at and i not in s['sent']:inject(pc,k);s['sent'].add(i)
  if t>3 and 'roster' not in s['shots']:shot(world,pc,'roster')
  actors=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor);p1=next(a for a in actors if 'BattleP1' in [str(x) for x in a.tags]);target=next(a for a in actors if 'BattleP'+str(target_index+1) in [str(x) for x in a.tags])
  text=log.read_text(encoding='utf-8',errors='replace') if log.exists() else '';s['hits']=len(re.findall(r'BATTLE_CONTACT match=1 ',text))
  if t>10 and not s['fired'] and t>s.get('attempt',0)+.25 and (mode_name!='gold' or s['hits']>=5):
   assert any(c.static_mesh and mesh_name in c.static_mesh.get_path_name() for c in p1.get_components_by_class(unreal.StaticMeshComponent)),'wrong roster mesh'
   s['attempt']=t;mode.fire_active_skill();active=next((c for c in target.get_components_by_class(unreal.SceneComponent) if c.get_name()==fx_name),None)
   if active and active.is_visible():s['fired']=True;s['fire_at']=t
  if not s['fired']:assert t<70,'no real charging condition';return
  age=t-s['fire_at'];fx=next(c for c in target.get_components_by_class(unreal.SceneComponent) if c.get_name()==fx_name)
  assert (fx.get_world_location()-target.get_actor_location()).length()<.01,'effect attached to wrong top'
  assert abs(fx.get_world_scale().x-1)<.001
  parts={c.get_name():c for c in fx.get_children_components(True) if isinstance(c,unreal.StaticMeshComponent)}
  assert len(parts)==part_count and all(c.get_collision_enabled()==unreal.CollisionEnabled.NO_COLLISION for c in parts.values())
  if mode_name=='gold' and 'IRON_WALL_VFX_HIT' in text and 'consume_at' not in s:s['consume_at']=t
  if 'reset_at' not in s:
   review=next(a for a in actors if 'ExtraReviewCamera' in [str(x) for x in a.tags]);aim=target.get_actor_location()+unreal.Vector(0,0,14);pos=aim+unreal.Vector(130,190,120)
   review.set_actor_location_and_rotation(pos,unreal.MathLibrary.find_look_at_rotation(pos,aim),False,True);review.get_component_by_class(unreal.CameraComponent).set_field_of_view(50);pc.set_view_target_with_blend(review,0)
  if age>.2 and 'double' not in s:mode.fire_active_skill();s['double']=True
  phase=None
  if age>.1 and 'active' not in s['shots']:phase='active'
  if mode_name=='gold' and 'consume_at' in s and t-s['consume_at']>.025 and 'impact' not in s['shots']:phase='impact'
  ended=(t-s['consume_at']>1 if mode_name=='gold' and 'consume_at' in s else duration is not None and age>duration+.7)
  if ended and 'expired' not in s['shots']:phase='expired'
  if phase:
   alpha=parts[main_name].get_material(0).get_scalar_parameter_value('Opacity')
   if phase=='active':assert fx.is_visible() and alpha>0
   if phase=='impact':assert parts['Gold_IronWallRipple'].get_material(0).get_scalar_parameter_value('Opacity')>0
   if phase=='expired':assert not fx.is_visible() and alpha==0
   s['samples'].append({'phase':phase,'age':age,'visible':fx.is_visible(),'opacity':alpha,'target':target_index+1});shot(world,pc,phase)
  if ended and 'reset_at' not in s:
   inject(pc,'R');s['reset_at']=t;pc.set_view_target_with_blend(next(a for a in actors if 'BattleCamera' in [str(x) for x in a.tags]),0)
  if 'reset_at' in s:
   assert not fx.is_visible(),'effect remains in lobby/next bout';elapsed=t-s['reset_at']
   for i,(at,k) in enumerate([(1,'SpaceBar'),(2,key),(2.4,'One'),(2.8,'Two'),(3.5,'SpaceBar'),(5,'SpaceBar')]):
    if elapsed>=at and i not in s['replay']:inject(pc,k);s['replay'].add(i)
   if elapsed>11:
    assert text.count(begin)==1 and 'SKILL_FIRE_BLOCKED' in text
    assert {'roster','active','expired'}<=s['shots']
    if mode_name=='gold':assert 'impact' in s['shots']
    finish('PASS')
  assert age<30,'effect not expired or consumed'
 except Exception:finish('FAIL',traceback.format_exc())
s['h']=unreal.register_slate_post_tick_callback(tick);levels.editor_request_begin_play()
