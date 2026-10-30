import unreal,json
from pathlib import Path
root=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
paths=[]
for name in ['Count','Pull','Release']:
    task=unreal.AssetImportTask();task.filename=str(root/f'docs/P3-art-inbox/batch2/audio/SFX_launch_{name.lower()}_v1.wav')
    task.destination_path='/Game/Beyblade/Audio';task.destination_name='S_Launch'+name;task.automated=True;task.save=True
    stable=task.destination_path+'/'+task.destination_name
    if not unreal.EditorAssetLibrary.does_asset_exist(stable):unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    sound=unreal.load_asset(stable);assert isinstance(sound,unreal.SoundWave) and .1<sound.duration<1.
    paths.append(sound.get_path_name())
(root/'Saved/launch-audio-report.json').write_text(json.dumps(paths,indent=2))
unreal.SystemLibrary.quit_editor()
