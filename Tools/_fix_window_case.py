from pathlib import Path
p=Path(r"C:\BeybladeUE\Source\BeybladePrototype\SkillRuntime.h")
sk=p.read_text(encoding="utf-8")
old='''\t\tcase ESkillCondition::WindowHitSec:
\t\t\tWindowSec += Dt;
\t\t\tif (bContact) bWindowGotHit = true;
\t\t\tif (!bWindowGotHit && WindowSec > Need())
\t\t\t{
\t\t\t\t// Missed window — restart
\t\t\t\tWindowSec = 0.0;
\t\t\t\tbWindowGotBey = bWindowGotWall = false;
\t\t\t}
\t\t\tbreak;'''
new='''\t\tcase ESkillCondition::WindowHitSec:
\t\t\t// CSV window_hit_bey_and_wall: bey AND wall each >=1 within N seconds.
\t\t\tWindowSec += Dt;
\t\t\tif (Delta > 0) bWindowGotBey = true;
\t\t\tif (bWall) bWindowGotWall = true;
\t\t\tif (!(bWindowGotBey && bWindowGotWall) && WindowSec > Need())
\t\t\t{
\t\t\t\tWindowSec = 0.0;
\t\t\t\tbWindowGotBey = bWindowGotWall = false;
\t\t\t}
\t\t\tbreak;'''
if old not in sk:
    # try without comment line variants
    import re
    m=re.search(r'\t\tcase ESkillCondition::WindowHitSec:\n(?:.*\n)*?\t\t\tbreak;', sk)
    if not m:
        raise SystemExit('block not found')
    print('FOUND via regex:\n', m.group(0))
    sk=sk[:m.start()]+new+sk[m.end():]
else:
    sk=sk.replace(old,new)
    print('exact replace ok')
assert 'bWindowGotHit' not in sk
p.write_text(sk, encoding='utf-8')
print('clean')
