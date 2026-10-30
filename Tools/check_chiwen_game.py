import unreal,time,json,re,traceback
from pathlib import Path
out=Path('C:/BeybladeUE/Saved/ChiwenCheck');out.mkdir(exist_ok=True);log=Path('C:/BeybladeUE/Saved/chiwen-pie.log')
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);assert levels.load_level('/Game/Maps/StadiumIndustrialPolish_v1')
cam=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.CameraActor,unreal.Vector());cam.tags=['ChiwenReviewCamera']
s={'wall':time.monotonic(),'t':0.,'prev':None,'sent':set(),'shots':set(),'samples':[],'fired':False,'replay':set()}
events=[(1,'SpaceBar'),(2,'Five'),(2.4,'One'),(2.8,'Two'),(3.3,'SpaceBar'),(5,'SpaceBar')]
def inject(pc,key):
 sub=next(o for o in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if 'Default__' not in o.get_name())
 action=next(a for a in unreal.ObjectIterator(unreal.InputAction) if a.get_outer()==pc and any(str(k.get_editor_property('key_name'))==key for k in sub.query_keys_mapped_to_action(a)))
 sub.inject_input_vector_for_action(action,unreal.Vector(1,0,0),[],[])
def finish(status,error=None):
 (out/'report.json').write_text(json.dumps({'status':status,'error':error,'fire_at':s.get('fire_at'),'impact_at':s.get('impact_at'),'natural_hits':s.get('hits',0),'move_level':120,'samples':s['samples']},indent=2))
 unreal.unregister_slate_post_tick_callback(s['h']);levels.editor_request_end_play();unreal.SystemLibrary.quit_editor()
def tick(dt):
 try:
  assert time.monotonic()-s['wall']<180,'PIE timeout'
  worlds=unreal.EditorLevelLibrary.get_pie_worlds(False)
  if not worlds:return
  world=worlds[0];now=unreal.GameplayStatics.get_time_seconds(world)
  if s['prev'] is not None:s['t']+=min(max(now-s['prev'],0),.1)
  s['prev']=now;t=s['t'];pc=unreal.GameplayStatics.get_player_controller(world,0);mode=unreal.GameplayStatics.get_game_mode(world)
  for i,(at,key) in enumerate(events):
   if t>=at and i not in s['sent']:inject(pc,key);s['sent'].add(i)
  actors=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor);bey=next(a for a in actors if 'BattleP1' in [str(x) for x in a.tags])
  text=log.read_text(encoding='utf-8',errors='replace') if log.exists() else '';s['hits']=len(re.findall(r'BATTLE_CONTACT match=1 ',text))
  if t>10 and not s['fired'] and s['hits']>=5:
   assert any(c.static_mesh and 'SM_Chiwen' in c.static_mesh.get_path_name() for c in bey.get_components_by_class(unreal.StaticMeshComponent))
   mode.fire_active_skill();s['fired']=True;s['fire_at']=t;s['hits_at_fire']=s['hits']
  if not s['fired']:assert t<65,'not enough natural collisions';return
  age=t-s['fire_at'];fx=next(c for c in bey.get_components_by_class(unreal.SceneComponent) if c.get_name()=='ChiwenEffect')
  parts={c.get_name():c for c in bey.get_components_by_class(unreal.StaticMeshComponent) if c.get_name().startswith('Chiwen')}
  assert len(parts)==4 and all(c.get_collision_enabled()==unreal.CollisionEnabled.NO_COLLISION for c in parts.values())
  assert (fx.get_world_location()-bey.get_actor_location()).length()<.01 and abs(fx.get_world_scale().x-1)<.001
  if 'CHIWEN_VFX_CONSUMED' in text and 'impact_at' not in s:s['impact_at']=t
  if 'reset_at' not in s:
   review=next(a for a in actors if 'ChiwenReviewCamera' in [str(x) for x in a.tags]);target=bey.get_actor_location()+unreal.Vector(0,0,15);pos=target+unreal.Vector(120,180,110)
   review.set_actor_location_and_rotation(pos,unreal.MathLibrary.find_look_at_rotation(pos,target),False,True);review.get_component_by_class(unreal.CameraComponent).set_field_of_view(50);pc.set_view_target_with_blend(review,0)
  if age>.2 and 'double' not in s:mode.fire_active_skill();s['double']=True
  phase=None
  if age>.10 and 'armed' not in s['shots'] and 'impact_at' not in s:phase='armed'
  if 'impact_at' in s and t-s['impact_at']>.025 and 'impact' not in s['shots']:phase='impact'
  if 'impact_at' in s and t-s['impact_at']>1 and 'expired' not in s['shots']:phase='expired'
  if phase:
   flame=parts['ChiwenFlames'].get_material(0).get_scalar_parameter_value('Opacity');hit=parts['ChiwenSparks'].get_material(0).get_scalar_parameter_value('Opacity')
   if phase=='armed':assert fx.is_visible() and flame>0 and not parts['ChiwenSparks'].is_visible()
   if phase=='impact':assert fx.is_visible() and hit>0 and s['hits']>s['hits_at_fire'],'next-hit burst not visible'
   if phase=='expired':assert not fx.is_visible() and flame==0 and hit==0
   s['samples'].append({'phase':phase,'age':age,'flame_opacity':flame,'hit_opacity':hit,'visible':fx.is_visible()});s['shots'].add(phase)
   unreal.SystemLibrary.execute_console_command(world,'HighResShot 1280x720 filename=C:/BeybladeUE/Saved/ChiwenCheck/'+phase+'.png',pc)
  if 'expired' in s['shots'] and 'reset_at' not in s:
   inject(pc,'R');s['reset_at']=t
   battlecam=next(a for a in actors if 'BattleCamera' in [str(x) for x in a.tags]);pc.set_view_target_with_blend(battlecam,0)
  if 'reset_at' in s:
   assert not fx.is_visible(),'effect remains after return to lobby';elapsed=t-s['reset_at']
   for i,(at,key) in enumerate([(1,'SpaceBar'),(2,'Five'),(2.4,'One'),(2.8,'Two'),(3.3,'SpaceBar'),(5,'SpaceBar')]):
    if elapsed>=at and i not in s['replay']:inject(pc,key);s['replay'].add(i)
   if elapsed>11:
    assert {'armed','impact','expired'}<=s['shots'] and text.count('CHIWEN_VFX_ARMED')==1 and text.count('CHIWEN_VFX_CONSUMED')==1
    assert 'SKILL_FIRE_BLOCKED' in text;finish('PASS')
  assert age<30,'charged collision never consumed'
 except Exception:finish('FAIL',traceback.format_exc())
s['h']=unreal.register_slate_post_tick_callback(tick);levels.editor_request_begin_play()
