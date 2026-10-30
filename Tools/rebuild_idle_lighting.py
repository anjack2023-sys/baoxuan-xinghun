import unreal,json,shutil
from pathlib import Path
root=Path('C:/BeybladeUE');file=root/'Content/FeelLab/Characters/PortraitRefinedV3/Male/SK_MaleIdle.uasset';backup=root/'Saved/Backups/before_training_lobby_20261028_185849/SK_MaleIdle.uasset'
if not backup.exists():shutil.copy2(file,backup)
sys=unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem);out=[]
for name in ['SK_MaleIdle','SK_MaleLaunch']:
 m=unreal.load_asset('/Game/FeelLab/Characters/PortraitRefinedV3/Male/'+name);settings=sys.get_lod_build_settings(m,0)
 out.append({'name':name,'materials':[str(x.material_interface) for x in m.materials],'build':str(settings)})
 if name=='SK_MaleIdle':
  settings.set_editor_property('recompute_normals',True);settings.set_editor_property('recompute_tangents',True);settings.set_editor_property('use_mikk_t_space',True)
  sys.set_lod_build_settings(m,0,settings);assert unreal.EditorAssetLibrary.save_loaded_asset(m,False)
(root/'Saved/idle-asset-settings.json').write_text(json.dumps(out,indent=2))
