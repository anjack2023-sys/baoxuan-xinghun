"""Package the Blender review frames into a labeled GIF and contact sheet."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT=Path(__file__).resolve().parents[1]/'art/launch-review-v1'
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',22)
small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)

def labeled(frame):
    image=Image.open(OUT/f'frame-{frame:03}.png').convert('RGB')
    draw=ImageDraw.Draw(image)
    phase=('准备站姿' if frame<17 else '屈膝预备' if frame<32 else
           '右手拉绳' if frame<40 else '陀螺脱离 · 顺势收臂' if frame<55 else '回到准备姿势')
    draw.rectangle((0,0,720,76),fill=(17,25,36))
    draw.text((22,10),'发射骨骼动作 v1 · 简单人偶',font=font,fill='white')
    draw.text((22,44),f'{phase}   {frame/30:.2f}s',font=small,fill=(140,210,255))
    draw.rectangle((0,676,720,720),fill=(17,25,36))
    draw.text((22,686),'蓝色：左手持器    白色：右手拉绳    橙色：发射器',font=small,fill='white')
    return image

frames=[labeled(frame) for frame in range(1,97,2)]
durations=[67]*len(frames)
durations[0]=500;durations[-1]=700
frames[0].save(OUT/'launch-preview.gif',save_all=True,append_images=frames[1:],duration=durations,loop=0)
sheet=Image.new('RGB',(1080,720))
for i,frame in enumerate((1,25,33,39,47,89)):
    sheet.paste(labeled(frame).resize((360,360)),((i%3)*360,(i//3)*360))
sheet.save(OUT/'key-poses.jpg',quality=93)
assert len(frames)==48
with Image.open(OUT/'launch-preview.gif') as check:
    assert check.n_frames==48
print(OUT/'launch-preview.gif')
