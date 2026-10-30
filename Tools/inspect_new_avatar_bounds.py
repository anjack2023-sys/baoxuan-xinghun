import unreal
for name in ('DeepSeek','Doubao','GPT'):
 a=unreal.load_asset('/Game/FeelLab/Characters/AIAvatars/'+name+'/SK_'+name); unreal.log_warning('TEST_BOUNDS '+name+' '+str(a.get_bounds())+' '+str(a.get_editor_property('materials')))
unreal.SystemLibrary.quit_editor()
