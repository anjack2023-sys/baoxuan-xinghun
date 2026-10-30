import unreal,json
from pathlib import Path
out=[]
for name in ['SK_MaleIdle','SK_MaleLaunch']:
 m=unreal.load_asset('/Game/FeelLab/Characters/PortraitRefinedV3/Male/'+name)
 out.append({'name':name,'materials':[str(x.material_interface) for x in m.materials],'lods':str(m.get_editor_property('lod_info'))})
Path('C:/BeybladeUE/Saved/idle-asset-settings.json').write_text(json.dumps(out,indent=2))
