import unreal,json
from pathlib import Path
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert levels.load_level('/Game/Maps/StadiumIndustrialPolish_v1')
a=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if 'FaceCameraCharacter' in [str(t) for t in a.tags])
r={'transform':str(a.get_actor_transform()),'forward':str(a.get_actor_forward_vector()),'right':str(a.get_actor_right_vector()),'actor':a.get_actor_label(),'class':a.get_class().get_name(),'components':[]}
for c in a.get_components_by_class(unreal.MeshComponent):
 d={'class':c.get_class().get_name()}
 if isinstance(c,unreal.StaticMeshComponent):d['mesh']=str(c.static_mesh.get_path_name())
 if isinstance(c,unreal.SkeletalMeshComponent):d['points']={b:str(c.get_socket_location(b)) for b in ['Head','L_Hand','R_Hand','L_Upperarm','R_Upperarm','Pelvis','L_Foot']};d['bones']=[str(c.get_bone_name(i)) for i in range(c.get_num_bones())]
 r['components'].append(d)
Path('C:/BeybladeUE/Saved/launch-character.json').write_text(json.dumps(r,indent=2))
unreal.SystemLibrary.quit_editor()

