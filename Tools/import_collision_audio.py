import json,traceback
from pathlib import Path
import unreal

root=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
report={}
try:
    paths=[]
    for i in range(1,4):
        task=unreal.AssetImportTask()
        task.filename=str(root/f'docs/P3-art-inbox/batch2/audio/SFX_bey_contact_{i}_v1.wav')
        task.destination_path='/Game/Beyblade/Audio'
        task.destination_name=f'S_BeyContact{i}'
        task.automated=True;task.save=True;task.replace_existing=False
        stable=task.destination_path+'/'+task.destination_name
        if not unreal.EditorAssetLibrary.does_asset_exist(stable):
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        sound=unreal.load_asset(stable)
        assert isinstance(sound,unreal.SoundWave),stable
        assert .2<sound.duration<.3, sound.duration
        paths.append(sound.get_path_name())
    report={'status':'PASS','sounds':paths}
except Exception:
    report={'status':'FAIL','error':traceback.format_exc()};unreal.log_error(report['error'])
finally:
    (root/'Tools/collision_audio_import.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    unreal.SystemLibrary.quit_editor()
