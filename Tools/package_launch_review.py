"""Package the Blender review frames into a labeled GIF and contact sheet."""
from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont

OUT=Path(__file__).resolve().parents[1]/'art/launch-review-v2'
if '--male' in sys.argv:
    OUT=OUT.parent/'male-launch-review-v2'
if '--female' in sys.argv:
    OUT=OUT.parent/'female-rigged-launch-v1'
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',22)
small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)

def labeled(frame):
    image=Image.open(OUT/f'frame-{frame:03}.png').convert('RGB')
    draw=ImageDraw.Draw(image)
    phase=('右手持红绳 · 抬手' if frame<23 else '绳端对准孔位 · 插入发射器' if frame<49 else
           '准备站姿' if frame<65 else '屈膝预备' if frame<80 else
           '拉动红绳' if frame<88 else '陀螺脱离 · 顺势收臂' if frame<103 else '回到准备姿势 · 红绳留在右手')
    draw.rectangle((0,0,720,76),fill=(17,25,36))
    title='女主动作预览 · 原骨架与蒙皮' if '--female' in sys.argv else '男主动作预览 · 红绳装填与发射' if '--male' in sys.argv else '发射骨骼动作 v2 · 红绳装填与发射'
    draw.text((22,10),title,font=font,fill='white')
    draw.text((22,44),f'{phase}   {frame/30:.2f}s',font=small,fill=(140,210,255))
    draw.rectangle((0,676,720,720),fill=(17,25,36))
    draw.text((22,686),'右手握黑色拉柄 · 红绳与浅色绳端全程保留',font=small,fill='white')
    return image

frames=[labeled(frame) for frame in range(1,145,2)]
durations=[67]*len(frames)
durations[0]=500;durations[-1]=700
frames[0].save(OUT/'launch-preview.gif',save_all=True,append_images=frames[1:],duration=durations,loop=0)
sheet=Image.new('RGB',(1080,720))
for i,frame in enumerate((1,19,43,73,87,107)):
    sheet.paste(labeled(frame).resize((360,360)),((i%3)*360,(i//3)*360))
sheet.save(OUT/'key-poses.jpg',quality=93)
assert len(frames)==72
with Image.open(OUT/'launch-preview.gif') as check:
    assert check.n_frames==72
print(OUT/'launch-preview.gif')
