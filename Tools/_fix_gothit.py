from pathlib import Path
p=Path(r"C:\BeybladeUE\Source\BeybladePrototype\SkillRuntime.h")
sk=p.read_text(encoding="utf-8")
for i,line in enumerate(sk.splitlines(),1):
    if "bWindowGotHit" in line or "WindowGot" in line:
        print(f"{i}:{line}")
# force replace any leftover
sk2=sk.replace("bWindowGotHit","bWindowGotBey")  # dangerous if already both
# better read and fix manually leftover
if "bWindowGotHit" in sk:
    lines=[]
    for line in sk.splitlines(True):
        if "bWindowGotHit" in line and "bWindowGotBey" not in line:
            print("LEFTOVER", line)
            continue  # drop orphan lines? or replace
        lines.append(line)
    # Actually replace leftover occurrences
    sk=sk.replace("bWindowGotHit = false","bWindowGotBey = bWindowGotWall = false")
    sk=sk.replace("bWindowGotHit","bWindowGotBey")  # remaining refs
    # may have duplicated Bey=Bey - check
p.write_text(sk, encoding="utf-8") if False else None
sk=p.read_text(encoding="utf-8")
print("--- after list ---")
for i,line in enumerate(sk.splitlines(),1):
    if "WindowGot" in line or "bWindowGotHit" in line:
        print(f"{i}:{line}")
