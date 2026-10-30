from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import av,json
out=Path('C:/BeybladeUE/art/iron-wall-preview-v1');font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',24);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
files=[out/'frames'/f'frame-{f:04}.png' for f in range(1,85)];assert all(p.exists() for p in files)
def phase(f):
 if f<10:return '护盾展开'
 if f<32:return '铁壁持续 · 正常旋转'
 if f<49:return '受击反馈 · 波纹扩散'
 if f<61:return '铁壁持续'
 if f<78:return '护盾消退'
 return '效果结束'
def labeled(f):
 im=Image.open(files[f-1]).convert('RGB');d=ImageDraw.Draw(im)
 d.text((26,18),'壁垒 · 铁壁防御  /  护盾预览 v1',font=font,fill=(220,235,255),stroke_width=1,stroke_fill=(10,18,30))
 d.text((28,56),phase(f),font=small,fill=(125,190,255),stroke_width=1,stroke_fill=(10,18,30))
 d.text((26,510),'独立效果预览 · 尚未接入游戏',font=small,fill=(175,185,200),stroke_width=1,stroke_fill=(10,18,30))
 return im
video=out/'iron-wall-preview.mp4';c=av.open(str(video),'w');stream=c.add_stream('libx264',rate=24);stream.width=960;stream.height=540;stream.pix_fmt='yuv420p';stream.options={'crf':'18','preset':'medium'}
for f in range(1,85):
 for packet in stream.encode(av.VideoFrame.from_image(labeled(f))):c.mux(packet)
for packet in stream.encode():c.mux(packet)
c.close()
frames=[labeled(f).resize((640,360),Image.Resampling.LANCZOS) for f in range(1,85,2)]
frames[0].save(out/'iron-wall-preview.gif',save_all=True,append_images=frames[1:],duration=83,loop=0,optimize=True)
sheet=Image.new('RGB',(1440,540),(15,20,30))
for i,f in enumerate([1,10,25,35,45,70]):sheet.paste(labeled(f).resize((480,270)),((i%3)*480,(i//3)*270))
sheet.save(out/'iron-wall-keyframes.jpg',quality=94);labeled(35).save(out/'iron-wall-impact.jpg',quality=95)
c=av.open(str(video));s=c.streams.video[0];assert s.frames==84;assert abs(float(s.duration*s.time_base)-3.5)<.01
with Image.open(out/'iron-wall-preview.gif') as gif:assert gif.n_frames==42
(out/'delivery-check.json').write_text(json.dumps({'status':'PASS','video_frames':s.frames,'fps':24,'duration':3.5,'gif_frames':42,'size':[960,540],'has_sound':False,'game_integration':False},indent=2));c.close()
(out/'README.md').write_text('''# 铁壁防御护盾 · 独立预览 v1

用户要求：先看动画，确认后再接入游戏。此版本尚未接入 Unreal，未修改现有技能规则、数值或游戏包。

- iron-wall-preview.mp4：960×540，24 fps，3.5 秒，无音效。
- iron-wall-preview.gif：640×360 循环预览。
- iron-wall-keyframes.jpg：展开、持续、受击、消退关键帧。
- iron-wall-preview.blend：可编辑 3D 场景与动画，原壁垒模型纹理已打包。

复用模型：docs/P3-art-inbox/batch3-tripo-v1/BEY_bilei_DEFENSE_tripo_v1.glb。只绕竖轴旋转，未加入翻倒或变形。

视觉层次：蓝色半透明护罩、双层地面光环、少量六边形装甲线；单次受击在护盾前侧产生三层波纹及蓝色碎光；结束时消退。

受击帧是预览演示事件。正式接入时应由真实碰撞触发，持续长度跟随实际技能状态，不能把 3.5 秒预览长度写入技能规则。地面环需要对齐场地表面，避免穿盘；实际战斗镜头下应调整密度与亮度。

生成脚本：Tools/preview_iron_wall.py；打包脚本：Tools/package_iron_wall_preview.py。delivery-check.json 验证帧数、尺寸与时长。
''',encoding='utf-8')
print(video)
