"""Batch-only: exercise real Enhanced Input and capture the art UI, then exit."""
import json
import re
import time
import traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT=ROOT/'screenshots/P3-UI'
OUT.mkdir(parents=True,exist_ok=True)
LOG=ROOT/'Saved/Logs/P3UIFlow.log'
SAVE=ROOT/'Saved/SaveGames/BeybladeSlot0.sav'
saved_slot=SAVE.read_bytes() if SAVE.exists() else None
LEVELS=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
UES=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ST={'phase':'boot','t':time.monotonic(),'start':time.monotonic(),'busy':False,'handle':None,
    'shots':{},'queue':[],'results':0,'blind_seen':False,'matches':0,'actions':[]}

def world():return UES.get_game_world()
def controller():return unreal.GameplayStatics.get_player_controller(world(),0)
def logs():return LOG.read_text(encoding='utf8',errors='replace')

def inject(name):
    pc=controller()
    subsystem=next((s for s in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem)
                    if s.get_outer().get_class().get_name()=='LocalPlayer'),None)
    assert subsystem,'No Enhanced Input subsystem'
    actions=sorted((a for a in unreal.ObjectIterator(unreal.InputAction) if a.get_outer()==pc),
                   key=lambda a:int(a.get_name().rsplit('_',1)[-1]))
    # SetupInputComponent creates these nine transient actions in this order.
    names=['launch_action','reset_action','mode_race5_action','mode_race8_action',
           'toggle_mode_action','pick3_action','pick4_action','pick5_action','click_action']
    assert len(actions)==len(names),[a.get_name() for a in actions]
    action=actions[names.index(name)]
    assert action,name
    subsystem.inject_input_vector_for_action(action,unreal.Vector(1,0,0),[],[])
    ST['actions'].append(name)

def capture(name):
    if name=='04_battle':
        camera=controller().get_view_target()
        assert camera.get_actor_location().z>1300,'Battle camera did not rise'
        assert camera.get_actor_rotation().pitch < -65,'Battle camera angle too low'
    path=str(OUT/(name+'.png')).replace('\\','/')
    unreal.SystemLibrary.execute_console_command(world(),'HighResShot 1600x900 filename="'+path+'"',controller())
    ST['shots'][name]=path

def plan(steps,next_phase):
    ST.update(phase='queue',queue=list(steps),after_queue=next_phase,t=time.monotonic())

def finish(ok):
    ST['status']='PASS' if ok else 'FAIL'
    report={k:v for k,v in ST.items() if k not in ('handle','busy','queue')}
    (OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    if saved_slot is not None:SAVE.write_bytes(saved_slot)
    elif SAVE.exists():SAVE.unlink()
    unreal.unregister_slate_post_tick_callback(ST['handle'])
    LEVELS.editor_request_end_play()
    unreal.SystemLibrary.quit_editor()

def pick_steps():
    return [(.5,'input','mode_race8_action'),(.6,'input','launch_action'),
        (.8,'shot','01_pick_empty'),(.7,'input','pick3_action'),(.5,'input','mode_race8_action'),
        (.5,'input','pick5_action'),(.8,'shot','02_pick_lineup'),(.8,'input','launch_action'),
        (.8,'shot','03_preparation'),(.8,'input','launch_action'),(2.,'shot','04_battle')]

def tick(dt):
    if ST['busy']:return
    ST['busy']=True
    try:
        now=time.monotonic();elapsed=now-ST['t']
        if now-ST['start']>240:raise RuntimeError('UI flow watchdog timeout')
        if ST['phase']=='boot' and elapsed>3:
            assert LEVELS.load_level('/Game/Maps/StadiumIndustrialPolish_v1')
            LEVELS.editor_request_begin_play();ST.update(phase='wait_pie',t=now)
        elif ST['phase']=='wait_pie' and elapsed>6:
            assert world(),'No PIE world'
            assert unreal.GameplayStatics.get_game_mode(world()).get_class().get_name()=='PrototypeBattleMode'
            plan([(.1,'shot','00_lobby')]+pick_steps(),'wait_result')
        elif ST['phase']=='queue' and ST['queue'] and elapsed>=ST['queue'][0][0]:
            delay,kind,arg=ST['queue'].pop(0)
            if kind=='input':inject(arg)
            elif kind=='shot':capture(arg)
            ST['t']=now
            if not ST['queue']:
                ST.update(phase=ST['after_queue'],t=now)
                if ST['phase']=='wait_result':unreal.GameplayStatics.set_global_time_dilation(world(),6.)
        elif ST['phase']=='wait_result' and elapsed>.5:
            text=logs()
            events=re.findall(r'M1_SCORE[^\r\n]+',text)
            if len(events)>ST['results']:
                ST['results']=len(events);ST['last_score']=events[-1]
                match='state=比赛结算' in events[-1]
                if match:
                    ST['matches']+=1
                    if ST['blind_seen']:
                        plan([(1.,'shot','08_match_settle')],'complete')
                    else:
                        assert ST['matches']<3,'Match ended before any blind phase in three attempts'
                        plan([(1.,'shot','08_match_settle'),(1.,'input','reset_action')]+pick_steps(),'wait_result')
                else:
                    name='05_round_settle' if '05_round_settle' not in ST['shots'] else 'round_latest'
                    plan([(1.,'shot',name),(1.,'input','launch_action')],'after_continue')
        elif ST['phase']=='after_continue' and elapsed>.8:
            next_lines=re.findall(r'P2_NEXT[^\r\n]+',logs())
            assert next_lines,'No next-round transition'
            if 'state=盲选' in next_lines[-1]:
                if not ST['blind_seen']:
                    ST['blind_seen']=True
                    # The regular lineup uses 2,1,4; slot 0 is available at the first blind pick.
                    plan([(.2,'shot','06_blind'),(.8,'input','mode_race5_action'),(.8,'shot','07_blind_selected'),
                          (.8,'input','launch_action'),(.8,'input','launch_action')],'wait_result')
                else:
                    plan([(.8,'input','launch_action'),(.8,'input','launch_action')],'wait_result')
            else:
                plan([(.2,'input','launch_action')],'wait_result')
        elif ST['phase']=='complete' and elapsed>3:
            required=['00_lobby','01_pick_empty','02_pick_lineup','03_preparation','04_battle',
                      '05_round_settle','06_blind','07_blind_selected','08_match_settle']
            assert all(name in ST['shots'] and Path(ST['shots'][name]).is_file() for name in required)
            assert 'P3_UI_MISSING' not in logs(),'UI texture missing'
            assert 'BATTLE_INIT_FAILED' not in logs(),'Battle init failed'
            finish(True)
    except Exception:
        ST['error']=traceback.format_exc()
        unreal.log_error(ST['error'])
        finish(False)
    finally:ST['busy']=False

ST['handle']=unreal.register_slate_post_tick_callback(tick)
