import unreal,time,json,re,traceback
from pathlib import Path
out=Path('C:/BeybladeUE/Saved/ChangxuanCheck');out.mkdir(exist_ok=True)
log=Path('C:/BeybladeUE/Saved/changxuan-pie.log')
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);assert levels.load_level('/Game/Maps/StadiumIndustrialPolish_v1')
cam=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.CameraActor,unreal.Vector());cam.tags=['ChangxuanReviewCamera']
state={'wall':time.monotonic(),'t':0.,'prev':None,'sent':set(),'shots':set(),'samples':[],'fired':False,'reset':False,'replay':set()}
events=[(1,'SpaceBar'),(2,'Three'),(2.4,'One'),(2.8,'Two'),(3.3,'SpaceBar'),(5,'SpaceBar')]
def inject(pc,key):
 subsystem=next(o for o in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if 'Default__' not in o.get_name())
 action=next(a for a in unreal.ObjectIterator(unreal.InputAction) if a.get_outer()==pc and any(str(k.get_editor_property('key_name'))==key for k in subsystem.query_keys_mapped_to_action(a)))
 subsystem.inject_input_vector_for_action(action,unreal.Vector(1,0,0),[],[])
def finish(status,error=None):
 (out/'report.json').write_text(json.dumps({'status':status,'error':error,'fire_at':state.get('fire_at'),'real_contact_count':state.get('contacts',0),'samples':state['samples']},indent=2))
 unreal.unregister_slate_post_tick_callback(state['h']);levels.editor_request_end_play();unreal.SystemLibrary.quit_editor()
def tick(dt):
 try:
  assert time.monotonic()-state['wall']<180,'PIE timeout'
  worlds=unreal.EditorLevelLibrary.get_pie_worlds(False)
  if not worlds:return
  world=worlds[0];now=unreal.GameplayStatics.get_time_seconds(world)
  if state['prev'] is not None:state['t']+=min(max(now-state['prev'],0),.1)
  state['prev']=now;t=state['t'];pc=unreal.GameplayStatics.get_player_controller(world,0);mode=unreal.GameplayStatics.get_game_mode(world)
  for index,(at,key) in enumerate(events):
   if t>=at and index not in state['sent']:inject(pc,key);state['sent'].add(index)
  actors=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor)
  bey=next(a for a in actors if 'BattleP1' in [str(x) for x in a.tags])
  text=log.read_text(encoding='utf-8',errors='replace') if log.exists() else ''
  state['contacts']=len(re.findall(r'BATTLE_CONTACT match=1 ',text))
  if t>7 and not state['fired'] and t>state.get('attempt_at',0)+.3:
   assert any(c.static_mesh and 'SM_Changxuan' in c.static_mesh.get_path_name() for c in bey.get_components_by_class(unreal.StaticMeshComponent)),'P1 is not Changxuan'
   state['attempt_at']=t;mode.fire_active_skill()
   active=next((c for c in bey.get_components_by_class(unreal.SceneComponent) if c.get_name()=='ChangxuanEffect'),None)
   if active and active.is_visible():state['fired']=True;state['fire_at']=t
  if not state['fired']:
   assert t<110,'no natural five-second quiet window';return
  age=t-state['fire_at']
  effect=next(c for c in bey.get_components_by_class(unreal.SceneComponent) if c.get_name()=='ChangxuanEffect')
  assert (effect.get_world_location()-bey.get_actor_location()).length()<.01,'recovery aura detached'
  assert abs(effect.get_world_scale().x-1)<.001,'recovery aura inherited spinning top scale'
  parts={c.get_name():c for c in bey.get_components_by_class(unreal.StaticMeshComponent) if c.get_name().startswith('Changxuan')}
  assert len(parts)==4,parts
  assert all(c.get_collision_enabled()==unreal.CollisionEnabled.NO_COLLISION for c in parts.values())
  if .6<age<4.9:
   review=next(a for a in actors if 'ChangxuanReviewCamera' in [str(x) for x in a.tags]);target=bey.get_actor_location()+unreal.Vector(0,0,12);pos=target+unreal.Vector(100,150,90)
   review.set_actor_location_and_rotation(pos,unreal.MathLibrary.find_look_at_rotation(pos,target),False,True);review.get_component_by_class(unreal.CameraComponent).set_field_of_view(45);pc.set_view_target_with_blend(review,0)
  if age>1. and 'double_fire' not in state:mode.fire_active_skill();state['double_fire']=True
  targets=[(.12,'deploy'),(.7,'sustain'),(4.15,'fade'),(4.6,'expired')]
  for at,name in targets:
   if age<at or name in state['shots']:continue
   opacity=parts['ChangxuanRing0'].get_material(0).get_scalar_parameter_value('Opacity')
   if name in ('deploy','sustain','impact'):assert effect.is_visible() and opacity>0,(name,opacity)
   if name=='expired':assert not effect.is_visible() and opacity==0,(name,opacity)
   if name=='sustain':
    tint=parts['ChangxuanRing0'].get_material(0).get_vector_parameter_value('Tint')
    assert tint.g>tint.r*10 and tint.b>tint.r*10,'recovery aura not teal'
    assert parts['ChangxuanMotes'].get_editor_property('relative_location').z>0,'motes below top'
   assert max(c.get_world_scale().x for c in parts.values())<.5,'effect scale too large'
   state['samples'].append({'phase':name,'age':age,'visible':effect.is_visible(),'opacity':opacity,'position':str(effect.get_world_location())});state['shots'].add(name)
   unreal.SystemLibrary.execute_console_command(world,'HighResShot 1280x720 filename=C:/BeybladeUE/Saved/ChangxuanCheck/'+name+'.png',pc)
  if age>5.0 and not state['reset']:
   inject(pc,'R');state['reset']=True
   battlecam=next(a for a in actors if 'BattleCamera' in [str(x) for x in a.tags]);pc.set_view_target_with_blend(battlecam,0)
  if age>5.:
   assert not effect.is_visible(),'recovery aura remains in lobby'
   for index,(at,key) in enumerate([(5.2,'SpaceBar'),(6.2,'Three'),(6.6,'One'),(7.,'Two'),(7.5,'SpaceBar'),(9.,'SpaceBar')]):
    if age>=at and index not in state['replay']:inject(pc,key);state['replay'].add(index)
   assert not effect.is_visible(),'recovery aura leaks into next round without a skill'
  if age>14.5:
   assert text.count('CHANGXUAN_VFX_BEGIN')==1,'skill retriggered while active'
   assert 'SKILL_FIRE_BLOCKED' in text
   assert {'deploy','sustain','fade','expired'}<=state['shots']
   finish('PASS')
 except Exception:finish('FAIL',traceback.format_exc())
state['h']=unreal.register_slate_post_tick_callback(tick);levels.editor_request_begin_play()
