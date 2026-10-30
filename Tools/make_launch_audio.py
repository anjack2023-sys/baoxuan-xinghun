import wave,math,random,struct
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'docs/P3-art-inbox/batch2/audio'
root.mkdir(parents=True,exist_ok=True)
for name,duration in [('Count',.15),('Pull',.9),('Release',.32)]:
    rng=random.Random(4242);samples=[];previous=0.
    for i in range(int(44100*duration)):
        t=i/44100.;noise=rng.uniform(-1,1);high=noise-previous;previous=noise
        if name=='Count':value=math.sin(2*math.pi*880*t)*math.sin(math.pi*t/duration)**2*.2
        elif name=='Pull':
            pulse=(t%(1/24))*24
            value=(high*.28+math.sin(2*math.pi*1800*t)*.12)*math.exp(-pulse*12)*math.sin(math.pi*t/duration)
        else:value=(high*.18+math.sin(2*math.pi*(700*t-700*t*t))*.08)*math.sin(math.pi*t/duration)*math.exp(-t*5)
        assert abs(value)<1
        samples.append(round(value*32767))
    with wave.open(str(root/f'SFX_launch_{name.lower()}_v1.wav'),'wb') as out:
        out.setparams((1,2,44100,len(samples),'NONE','not compressed'));out.writeframes(struct.pack('<'+'h'*len(samples),*samples))
    assert len(samples)>4000 and max(map(abs,samples))>1000
print('Three deterministic launch sounds generated and checked')
