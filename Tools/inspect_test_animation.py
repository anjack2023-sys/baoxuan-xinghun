import unreal
actor=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkeletalMeshActor,unreal.Vector())
for name in ('DeepSeek','Doubao'):
 c=actor.skeletal_mesh_component;m=unreal.load_asset('/Game/FeelLab/Characters/AIAvatars/'+name+'/SK_'+name);a=unreal.load_asset('/Game/FeelLab/Characters/AIAvatars/'+name+'/A_LaunchTest');c.set_skeletal_mesh_asset(m);c.set_world_scale3d(unreal.Vector(1.8,1.8,1.8));c.play_animation(a,False);c.set_position(2.9,False);unreal.log_warning('TEST_NEW '+name+' '+str(c.get_socket_location('LaunchSocket')))
unreal.SystemLibrary.quit_editor()
