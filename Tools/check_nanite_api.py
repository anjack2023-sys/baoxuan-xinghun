import unreal
from pathlib import Path
sub=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
Path('C:/BeybladeUE/Saved/nanite-api.txt').write_text(str(sub.set_nanite_settings.__doc__)+'\n'+str(sub.get_nanite_settings.__doc__),encoding='utf-8')
