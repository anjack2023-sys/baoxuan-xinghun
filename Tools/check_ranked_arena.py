import unreal,time,json,traceback,re
from pathlib import Path
out=Path('C:/BeybladeUE/Saved/RankedArenaCheck');out.mkdir(parents=True,exist_ok=True)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);assert levels.load_level('/Game/Maps/RankedArena_v1')
review=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.CameraActor,unreal.Vector());review.tags=['ScoreProofCamera'];s={'wall':time.monotonic(),'events':set(),'shots':set(),'phase':0}
def inject(pc,key):
 sub=next(o for o in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if 'Default__' not in o.get_name())
 action=next(a for a in unreal.ObjectIterator(unreal.InputAction) if a.get_outer()==pc and any(str(k.get_editor_property('key_name'))==key for k in sub.query_keys_mapped_to_action(a)))
 sub.inject_input_vector_for_action(action,unreal.Vector(1,0,0),[],[])
def finish(status,error=None):
 (out/'report.json').write_text(json.dumps({'status':status,'error':error,'checks':s.get('checks',{}),'shots':list(s['shots'])},indent=2));unreal.unregister_slate_post_tick_callback(s['h']);levels.editor_request_end_play();unreal.SystemLibrary.quit_editor()
def shot(w,pc,name):
 s['shots'].add(name);unreal.SystemLibrary.execute_console_command(w,'HighResShot 1280x720 filename='+str(out/(name+'.png')).replace('\\','/'),pc)
def tick(dt):
 try:
  assert time.monotonic()-s['wall']<180,'timeout'
  worlds=unreal.EditorLevelLibrary.get_pie_worlds(False)
  if not worlds:return
  w=worlds[0];t=unreal.GameplayStatics.get_time_seconds(w);pc=unreal.GameplayStatics.get_player_controller(w,0);mode=unreal.GameplayStatics.get_game_mode(w)
  if s['phase']==1:
   if 'StadiumIndustrialPolish' in w.get_name() and t>.8:
    shot(w,pc,'training_return');s['checks']['return_to_training_hall']=True;inject(pc,'E');s['phase']=2
   return
  if s['phase']==2:
   if 'RankedArena' in w.get_name() and t>1:
    assert pc.get_controlled_pawn() and 'ArenaWalker' in pc.get_controlled_pawn().get_class().get_name();s['checks']['hall_entry_E']=True;finish('PASS')
   return
  pawn=next((a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Character) if 'ArenaWalker' in a.get_class().get_name()),None)
  if t>1:assert pawn,'walking pawn missing'
  if t>1.5 and 'arrival' not in s['shots']:
   assert pc.get_controlled_pawn()==pawn and pc.get_view_target()==pawn;shot(w,pc,'arrival');s['checks']={'third_person':True}
  if 2<t<5:pawn.add_movement_input(unreal.Vector(0,-1,0),1,False)
  if t>5 and 'collision' not in s['shots']:
   p=pawn.get_actor_location();assert 220<p.y<335 and abs(p.z-106)<6,str(p);s['checks']['bowl_collision']=str(p);shot(w,pc,'collision')
  events=[(6,'E'),(7,'One'),(7.4,'Two'),(7.8,'Three'),(8.5,'SpaceBar'),(10,'SpaceBar')]
  for i,(at,key) in enumerate(events):
   if t>=at and i not in s['events']:inject(pc,key);s['events'].add(i)
  if t>9 and 'selection' not in s['shots']:shot(w,pc,'selection')
  if t>19 and 'battle' not in s['shots']:
   assert not pawn.get_actor_enable_collision(),'walker remains visible during match';assert pc.get_controlled_pawn()!=pawn;shot(w,pc,'battle');s['checks']['battle_transition']=True
  actors=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor)
  texts={str(tag):a.get_component_by_class(unreal.StaticMeshComponent) for a in actors for tag in a.tags if str(tag) in ['ArenaScoreP1','ArenaScoreP2']}
  assert len(texts)==2,'dynamic score displays missing'
  score=[int(texts['ArenaScoreP'+str(i+1)].static_mesh.get_name().rsplit('_',1)[1]) for i in range(2)]
  if sum(score)>0 and 'score_at' not in s:
   log=Path('C:/BeybladeUE/Saved/arena-pie.log').read_text(encoding='utf-8',errors='replace')
   assert 'target=8' in log,'arena did not use race to eight'
   if ('total=%d:%d'%tuple(score)) not in log:return
   s['checks']['real_scoreboard']=score;s['score_at']=t
   cam=next(a for a in actors if 'ScoreProofCamera' in [str(x) for x in a.tags]);pos=unreal.Vector(0,-150,390);cam.set_actor_location_and_rotation(pos,unreal.MathLibrary.find_look_at_rotation(pos,unreal.Vector(0,-640,365)),False,True);cam.get_component_by_class(unreal.CameraComponent).set_field_of_view(70);pc.set_view_target_with_blend(cam,0);unreal.SystemLibrary.execute_console_command(w,'showhud',pc)
  if 'score_at' in s and t>s['score_at']+.4 and 'scoreboard' not in s['shots']:shot(w,pc,'scoreboard')
  if 'score_at' in s and t>s['score_at']+1 and 'reset_issued' not in s:
   unreal.SystemLibrary.execute_console_command(w,'showhud',pc);inject(pc,'R');s['reset_issued']=t
  if 'score_at' in s and t>s['score_at']+2 and 'resumed' not in s['shots']:
   assert pc.get_controlled_pawn()==pawn and pawn.get_actor_enable_collision();shot(w,pc,'resumed');s['checks']['resume_exploration']=True
   assert all(c.static_mesh.get_name()=='SM_Score_0' for c in texts.values()),'score did not reset'
  if 'resumed' in s['shots'] and t>s['score_at']+3:inject(pc,'R');s['phase']=1
  assert t<100,'natural round or map return timeout'
 except Exception:finish('FAIL',traceback.format_exc())
s['h']=unreal.register_slate_post_tick_callback(tick);levels.editor_request_begin_play()

