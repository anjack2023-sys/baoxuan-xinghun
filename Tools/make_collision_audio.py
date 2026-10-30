"""Create three original short metal/polymer impact sounds; no external samples."""
import math, random, struct, wave
from pathlib import Path

out=Path(__file__).resolve().parents[1]/'docs/P3-art-inbox/batch2/audio'
out.mkdir(parents=True,exist_ok=True)
rate=48000
for variant in range(3):
    rng=random.Random(8400+variant)
    samples=[]
    for i in range(int(rate*.24)):
        t=i/rate
        attack=min(1.,t/.0015)
        knock=.7*math.sin(2*math.pi*(180+variant*13)*t)*math.exp(-t*65)
        ring=sum(a*math.sin(2*math.pi*f*(1+variant*.035)*t)*math.exp(-t*d)
                 for f,a,d in [(970,.20,32),(1713,.19,38),(2891,.13,48),(4327,.07,65)])
        crack=(rng.random()*2-1)*.55*math.exp(-t*160)
        fade=min(1.,(.24-t)/.02)
        samples.append((knock+ring+crack)*attack*fade)
    peak=max(abs(s) for s in samples)
    samples=[s*.8/peak for s in samples]
    assert .03<math.sqrt(sum(s*s for s in samples)/len(samples))<.3
    assert max(abs(s) for s in samples)<=.801
    path=out/f'SFX_bey_contact_{variant+1}_v1.wav'
    with wave.open(str(path),'wb') as f:
        f.setparams((1,2,rate,len(samples),'NONE','not compressed'))
        f.writeframes(struct.pack('<'+'h'*len(samples),*(round(s*32767) for s in samples)))
    with wave.open(str(path),'rb') as f:
        assert f.getnframes()==11520 and f.getframerate()==rate
    print(path.name)
