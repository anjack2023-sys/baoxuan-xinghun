import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(r'C:/Users/Administrator/Desktop/ai陀螺游戏/beyblade-unreal-prototype/art/female-launch-v1')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r'D:/Documents/Downloads/tripo_convert_199ec8da-7ed5-4fb8-8f2f-05cccec25483.glb')
o=next(o for o in bpy.context.scene.objects if o.type=='MESH')
coords=[o.matrix_world@v.co for v in o.data.vertices];lo=Vector(tuple(min(v[k] for v in coords) for k in range(3)));hi=Vector(tuple(max(v[k] for v in coords) for k in range(3)));print('BOUNDS',list(lo),list(hi),'verts',len(coords))
scale=1.72/(hi.z-lo.z)
for v in o.data.vertices:v.co=(o.matrix_world@v.co-Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z)))*scale
o.matrix_world.identity()
s=bpy.context.scene;s.world=bpy.data.worlds.new('World');s.world.color=(.12,.15,.2)
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=2.1;s.camera=cam
s.render.engine='BLENDER_WORKBENCH';s.display.shading.color_type='TEXTURE';s.display.shading.show_cavity=False;s.render.resolution_x=720;s.render.resolution_y=720;s.render.resolution_percentage=100
for name,location in [('front',(0,-4,1.4)),('back',(0,4,1.4)),('side',(4,0,1.4))]:
 cam.location=location;cam.rotation_euler=(Vector((0,0,.86))-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(root/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'female-source.blend'))
