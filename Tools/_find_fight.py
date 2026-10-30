from pathlib import Path
cpp=Path(r"C:\BeybladeUE\Source\BeybladePrototype\PrototypeBattle.cpp").read_text(encoding="utf-8")
mf=Path(r"C:\BeybladeUE\Source\BeybladePrototype\MatchFlow.h").read_text(encoding="utf-8")
for s in ["Fighting","StartBattle","EnterFight","PrepLaunch","TryLaunch","BeginFight"]:
    print("---",s,"in cpp", cpp.count(s), "in mf", mf.count(s))

# Find Prep related transitions
import re
for m in re.finditer(r'.{0,40}Fighting.{0,40}', cpp):
    print("CPP:", m.group(0).replace("\n"," "))
for m in re.finditer(r'.{0,40}Fighting.{0,80}', mf):
    print("MF:", m.group(0).replace("\n"," "))

# Launch Prep path
i=cpp.find("EMatchFlowState::Prep")
print("Prep usages", cpp.count("EMatchFlowState::Prep"))
idx=0
while True:
    i=cpp.find("Prep", idx)
    if i<0: break
    if "PrepLaunch" in cpp[i:i+20] or "State == EMatchFlowState::Prep" in cpp[max(0,i-30):i+40]:
        print(cpp[max(0,i-80):i+200].replace("\n"," | "))
        print("====")
    idx=i+4
