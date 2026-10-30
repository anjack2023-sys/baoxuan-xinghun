import unreal
w=unreal.EditorLevelLibrary.get_editor_world();a=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkeletalMeshActor,unreal.Vector())
for name in ('DeepSeek','Doubao','GPT'):
 m=unreal.load_asset('/Game/FeelLab/Characters/AIAvatars/'+name+'/SK_'+name);c=a.skeletal_mesh_component;c.set_skeletal_mesh_asset(m);c.set_world_scale3d(unreal.Vector(1.8,1.8,1.8))
 for b in ('Root','L_Hand','R_Hand','LaunchSocket'):
  unreal.log_warning('TEST_POS '+name+' '+b+' '+str(c.get_socket_location(b)))
unreal.SystemLibrary.quit_editor()

