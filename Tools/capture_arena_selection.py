"""Reuse full flow QA and capture the two portraits over the live stadium."""
from pathlib import Path
import unreal

root=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
source=(root/'Tools/capture_p3_ui.py').read_text(encoding='utf8')
source=source.replace('screenshots/P3-UI','screenshots/Arena-Selection')
source=source.replace("(.7,'input','pick3_action'),(.5", "(.7,'input','pick3_action'),(1.,'shot','01b_changxuan'),(.5")
exec(compile(source,str(root/'Tools/capture_p3_ui.py'),'exec'),globals())
base_capture=capture

def capture(name):
    if name in ('01_pick_empty','01b_changxuan','02_pick_lineup'):
        camera=controller().get_view_target()
        assert abs(camera.get_actor_location().z-650)<5,'Selection did not use the stadium preparation view'
        for portrait in ('Chifeng','Changxuan','Bilei'):
            assert isinstance(unreal.load_asset('/Game/Beyblade/UI/P3/T_Portrait'+portrait),unreal.Texture2D)
    base_capture(name)
