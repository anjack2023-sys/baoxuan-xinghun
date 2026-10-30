import bpy,json
from pathlib import Path
from mathutils import Vector
p=Path(r'C:/Users/Administrator/Desktop/ai陀螺游戏/beyblade-unreal-prototype/art/female-launch-v1')
bpy.ops.wm.open_mainfile(filepath=str(p/'female-rigged-source.blend'))
r=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');o=next(o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers))
r.animation_data_clear()
for b in r.pose.bones:b.matrix_basis.identity()
mat=o.data.materials[0]
im=next(n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and any(l.to_socket.name=='Base Color' for l in n.outputs['Color'].links))
sample=im.copy();sample.scale(512,512);pixels=list(sample.pixels);hits=[]
for f in o.data.polygons:
 uv=sum((o.data.uv_layers.active.data[i].uv for i in f.loop_indices),Vector((0,0)))/len(f.loop_indices)
 k=(min(511,max(0,int(uv.y*512)))*512+min(511,max(0,int(uv.x*512))))*4;red,green,blue=pixels[k:k+3]
 weight=sum(sum(g.weight for g in o.data.vertices[i].groups if o.vertex_groups[g.group].name=='R_Hand') for i in f.vertices)/len(f.vertices)
 pos=sum((o.data.vertices[i].co for i in f.vertices),Vector())/len(f.vertices)
 if weight>.5 and red>green*1.6 and red>blue*1.3:hits.append(list(pos))
print('RED',len(hits), sorted(hits,key=lambda x:x[2])[:5])
(p/'launcher-red-tip.json').write_text(json.dumps({'tip':sorted(hits,key=lambda x:x[2])[0],'hits':len(hits)}))

