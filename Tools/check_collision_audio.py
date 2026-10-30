"""Run real player input until several physics contacts have active sound voices."""
from pathlib import Path
import unreal

root=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
source=(root/'Tools/capture_p3_ui.py').read_text(encoding='utf8').replace('screenshots/P3-UI','screenshots/Collision-Audio')
exec(compile(source,str(root/'Tools/capture_p3_ui.py'),'exec'),globals())
base_capture=capture

def capture(name):
    base_capture(name)
    if name=='04_battle':ST['after_queue']='audio_wait'

def audio_tick(dt):
    try:
        if ST['phase']!='audio_wait':return
        text=logs()
        assert 'COLLISION_AUDIO_MISSING' not in text,'Sound asset missing'
        events=re.findall(r'COLLISION_AUDIO hit=(\d+) variant=(\d+) volume=([\d.]+) playing=(\d)',text)
        if len(events)>=3:
            assert all(e[3]=='1' and .2<float(e[2])<=.75 for e in events),'Sound voice did not play'
            assert len({e[1] for e in events})==3,'Missing sound variants'
            ST['sound_events']=events
            ST['audio_check']='PASS'
            unreal.unregister_slate_post_tick_callback(audio_handle)
            finish(True)
        elif time.monotonic()-ST['t']>45:raise AssertionError('No collision audio voices within 45 seconds')
    except Exception:
        ST['error']=traceback.format_exc()
        unreal.unregister_slate_post_tick_callback(audio_handle)
        finish(False)

audio_handle=unreal.register_slate_post_tick_callback(audio_tick)
