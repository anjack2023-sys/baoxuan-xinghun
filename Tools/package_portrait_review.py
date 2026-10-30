"""Review boards assembled from real 3D renders and the supplied illustrations."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps

OUT=Path(__file__).resolve().parents[1]/'art/portrait-refine-v1'
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',28)
small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',21)
board=Image.new('RGB',(1440,1110),(28,34,44));draw=ImageDraw.Draw(board)
for i,(who,title) in enumerate((('male','男主 · 精修 v1'),('female','女主 · 精修 v1'))):
    draw.text((i*720+26,16),title,font=font,fill='white')
    board.paste(Image.open(OUT/(who+'-body-after.png')).convert('RGB'),(i*720,62))
draw.text((24,1074),'真实 3D 模型渲染 · 原骨架、蒙皮与发射动作保留 · 独立精修预览',font=small,fill=(195,210,230))
board.save(OUT/'refined-pair.jpg',quality=95)

comparison=Image.new('RGB',(1280,1760),(28,34,44));draw=ImageDraw.Draw(comparison)
for row,(who,title) in enumerate((('male','男主'),('female','女主'))):
    top=row*880
    for col,(suffix,label) in enumerate((('face-before','原模型'),('face-after','精修 v1'))):
        draw.text((col*640+24,top+14),title+' · '+label,font=font,fill='white')
        comparison.paste(Image.open(OUT/(who+'-'+suffix+'.png')).convert('RGB'),(col*640,top+62))
comparison.save(OUT/'face-before-after.jpg',quality=95)

reference=Image.new('RGB',(1440,650),(28,34,44));draw=ImageDraw.Draw(reference)
for col,(who,title) in enumerate((('male','男主'),('female','女主'))):
    x=col*720
    for side,(name,label) in enumerate(((f'reference-{who}.png','立绘参考'),(f'{who}-body-after.png','3D 精修 v1'))):
        draw.text((x+side*360+16,16),title+' · '+label,font=small,fill='white')
        picture=Image.open(OUT/name).convert('RGB')
        picture=ImageOps.contain(picture,(360,560))
        reference.paste(picture,(x+side*360+(360-picture.width)//2,60+(560-picture.height)//2))
reference.save(OUT/'reference-comparison.jpg',quality=95)
assert (OUT/'refined-pair.jpg').stat().st_size>10000
