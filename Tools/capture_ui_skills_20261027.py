import json, time, traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT=ROOT/'screenshots/ui-skills-20261027'; OUT.mkdir(parents=True,exist_ok=True)
LEVELS=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
UES=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ST={'index':0,'time':time.monotonic(),'start':time.monotonic(),'shots':{}}
def world(): return UES.get_game_world()
def mode(): return unreal.GameplayStatics.get_game_mode(world())
def pc(): return unreal.GameplayStatics.get_player_controller(world(),0)
def inject(index):
    actions=sorted((a for a in unreal.ObjectIterator(unreal.InputAction) if a.get_outer()==pc()),key=lambda a:int(a.get_name().rsplit('_',1)[-1]))
    sub=next(s for s in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if s.get_outer().get_class().get_name()=='LocalPlayer')
    sub.inject_input_vector_for_action(actions[index],unreal.Vector(1,0,0),[],[])
def shot(name):
    path=str(OUT/(name+'.png')).replace('\\','/')
    unreal.SystemLibrary.execute_console_command(world(),'HighResShot 1600x900 filename="'+path+'"',pc())
    ST['shots'][name]=path
def boot():
    assert LEVELS.load_level('/Game/Maps/StadiumIndustrialPolish_v1')
    LEVELS.editor_request_begin_play()
def back():
    mode().close_collection();mode().close_collection()
def finish(ok):
    unreal.unregister_slate_post_tick_callback(ST['handle'])
    ST['status']='PASS' if ok else 'FAIL'
    (OUT/'report.json').write_text(json.dumps({k:v for k,v in ST.items() if k!='handle'},indent=2),encoding='utf-8')
    LEVELS.editor_request_end_play();unreal.SystemLibrary.quit_editor()
STEPS=[(2,boot),(6,lambda:shot('01_lobby')),(1,lambda:mode().open_collection()),
       (2,lambda:shot('02_collection_grid')),(1,lambda:mode().select_collection_slot(7)),
       (2,lambda:shot('03_collection_detail')),(1,back),(1,lambda:inject(0)),
       (2,lambda:shot('04_pick')),(1,lambda:inject(5)),(.5,lambda:inject(6)),(.5,lambda:inject(7)),
       (1,lambda:shot('05_pick_lineup')),(1,lambda:inject(0)),(2,lambda:shot('06_prep')),
       (1,lambda:inject(0)),(3,lambda:shot('07_fight_skill_shell')),(1,lambda:finish(True))]
def tick(dt):
    try:
        if time.monotonic()-ST['start']>150: raise RuntimeError('watchdog')
        delay,action=STEPS[ST['index']]
        if time.monotonic()-ST['time']<delay:return
        ST['index']+=1;ST['time']=time.monotonic();action()
    except Exception:
        ST['error']=traceback.format_exc();unreal.log_error(ST['error']);finish(False)
ST['handle']=unreal.register_slate_post_tick_callback(tick)
