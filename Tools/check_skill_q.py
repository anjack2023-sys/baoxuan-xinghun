import unreal,time,re,json,traceback
from pathlib import Path
out=Path('C:/BeybladeUE/Saved/SkillQCheck');out.mkdir(parents=True,exist_ok=True)
log=Path('C:/BeybladeUE/Saved/skill-q-pie.log')
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);assert levels.load_level('/Game/Maps/StadiumIndustrialPolish_v1')
s={'wall':time.monotonic(),'sent':set(),'shots':set()}
def inject(pc,key):
 sub=next(o for o in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if 'Default__' not in o.get_name())
 a=next(a for a in unreal.ObjectIterator(unreal.InputAction) if a.get_outer()==pc and any(str(k.get_editor_property('key_name'))==key for k in sub.query_keys_mapped_to_action(a)))
 sub.inject_input_vector_for_action(a,unreal.Vector(1,0,0),[],[])
def finish(status,error=None):
 (out/'report.json').write_text(json.dumps({'status':status,'error':error,'shots':list(s['shots'])},indent=2))
 unreal.unregister_slate_post_tick_callback(s['h']);levels.editor_request_end_play();unreal.SystemLibrary.quit_editor()
def shot(w,pc,name):
 s['shots'].add(name);unreal.SystemLibrary.execute_console_command(w,'HighResShot 1280x720 filename='+str(out/(name+'.png')).replace('\\','/'),pc)
def tick(dt):
 try:
  assert time.monotonic()-s['wall']<150,'timeout'
  worlds=unreal.EditorLevelLibrary.get_pie_worlds(False)
  if not worlds:return
  w=worlds[0];t=unreal.GameplayStatics.get_time_seconds(w);pc=unreal.GameplayStatics.get_player_controller(w,0)
  events=[(1,'Q'),(1.5,'SpaceBar'),(2.5,'One'),(3,'Two'),(3.5,'Three'),(4.2,'SpaceBar'),(5,'Q'),(5.5,'SpaceBar'),(10,'Q')]
  for i,(at,key) in enumerate(events):
   if t>=at and i not in s['sent']:inject(pc,key);s['sent'].add(i)
  text=log.read_text(encoding='utf-8',errors='replace') if log.exists() else ''
  hits=len(re.findall(r'BATTLE_CONTACT match=1 ',text))
  if hits>=1 and hits<5 and 'blocked_at' not in s:
   inject(pc,'Q');s['blocked_at']=t;shot(w,pc,'progress')
  if hits>=5 and t>11 and 'ready_at' not in s:
   assert 'SKILL_FIRE_BLOCKED' in text,'unready Q was not blocked';s['ready_at']=t;shot(w,pc,'ready')
  if 'ready_at' in s and t>s['ready_at']+.8 and 'fire_at' not in s:inject(pc,'Q');s['fire_at']=t
  if 'fire_at' in s and t>s['fire_at']+.4 and 'active' not in s['shots']:
   assert 'SKILL_FIRE id=chifeng' in text,'Q did not fire';shot(w,pc,'active');inject(pc,'Q')
  if 'fire_at' in s and t>s['fire_at']+1.2 and 'reset_at' not in s:
   assert text.count('SKILL_FIRE id=chifeng')==1,'repeated Q fired twice';inject(pc,'R');s['reset_at']=t
  if 'reset_at' in s and t>s['reset_at']+.8:shot(w,pc,'returned');finish('PASS')
  assert t<65,'never ready'
 except Exception:finish('FAIL',traceback.format_exc())
s['h']=unreal.register_slate_post_tick_callback(tick);levels.editor_request_begin_play()
