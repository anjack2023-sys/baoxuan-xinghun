import bpy,json
from pathlib import Path
p=Path(r'C:/Users/Administrator/Desktop/ai陀螺游戏/beyblade-unreal-prototype')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(next((p/'Saved/FeelRef60/work/LabSources/TripoMaleLauncher-v1').glob('*.fbx'))),use_anim=False)
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');m=o.data
adj=[[] for v in m.vertices]
for e in m.edges:a,b=e.vertices;adj[a].append(b);adj[b].append(a)
seen=set();parts=[]
for v in m.vertices:
 if v.index in seen:continue
 todo=[v.index];seen.add(v.index);ids=[]
 while todo:
  i=todo.pop();ids.append(i)
  for k in adj[i]:
   if k not in seen:seen.add(k);todo.append(k)
 if len(ids)>3:parts.append({'n':len(ids),'min':[min(m.vertices[i].co[k] for i in ids) for k in range(3)],'max':[max(m.vertices[i].co[k] for i in ids) for k in range(3)]})
print(json.dumps(sorted(parts,key=lambda x:-x['n'])[:30],indent=2))
