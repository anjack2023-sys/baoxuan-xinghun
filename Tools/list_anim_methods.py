import unreal
for n in dir(unreal.AnimationLibrary):
 if any(x in n for x in ('bone','track','frame')):print('METHOD',n)
unreal.SystemLibrary.quit_editor()
