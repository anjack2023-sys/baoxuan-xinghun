from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import av,json
out=Path('C:/BeybladeUE/art/huangkai-preview-v1');font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',24);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
files=[out/'frames'/f'frame-{f:04}.png' for f in range(1,85)];assert all(p.exists() for p in files)
def phase(f):
 if f<10:return '护盾展开'
 if f<32:return '金色护片 · 等待下一次碰螺'
 if f<49:return '受击吸收 · 金色回波'
 if f<61:return '反击波消散'
 if f<78:return '演示结束'
 return '效果结束'
def labeled(f):
 im=Image.open(files[f-1]).convert('RGB');d=ImageDraw.Draw(im)
 d.text((26,18),'煌铠 · 金障回击  /  独立预览 v1',font=font,fill=(220,235,255),stroke_width=1,stroke_fill=(10,18,30))
 d.text((28,56),phase(f),font=small,fill=(255,205,100),stroke_width=1,stroke_fill=(10,18,30))
 d.text((26,510),'独立效果预览 · 实战版见八选三入口',font=small,fill=(175,185,200),stroke_width=1,stroke_fill=(10,18,30))
 return im
video=out/'huangkai-preview.mp4';c=av.open(str(video),'w');stream=c.add_stream('libx264',rate=24);stream.width=960;stream.height=540;stream.pix_fmt='yuv420p';stream.options={'crf':'18','preset':'medium'}
for f in range(1,85):
 for packet in stream.encode(av.VideoFrame.from_image(labeled(f))):c.mux(packet)
for packet in stream.encode():c.mux(packet)
c.close()
frames=[labeled(f).resize((640,360),Image.Resampling.LANCZOS) for f in range(1,85,2)]
frames[0].save(out/'huangkai-preview.gif',save_all=True,append_images=frames[1:],duration=83,loop=0,optimize=True)
sheet=Image.new('RGB',(1440,540),(15,20,30))
for i,f in enumerate([1,10,25,35,45,70]):sheet.paste(labeled(f).resize((480,270)),((i%3)*480,(i//3)*270))
sheet.save(out/'huangkai-keyframes.jpg',quality=94);labeled(40).save(out/'huangkai-impact.jpg',quality=95)
c=av.open(str(video));s=c.streams.video[0];assert s.frames==84;assert abs(float(s.duration*s.time_base)-3.5)<.01
with Image.open(out/'huangkai-preview.gif') as gif:assert gif.n_frames==42
(out/'delivery-check.json').write_text(json.dumps({'status':'PASS','video_frames':s.frames,'fps':24,'duration':3.5,'gif_frames':42,'size':[960,540],'has_sound':False,'game_integration':False},indent=2));c.close()
