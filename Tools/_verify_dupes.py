from pathlib import Path
cpp=Path(r"C:\BeybladeUE\Source\BeybladePrototype\PrototypeBattle.cpp").read_text(encoding="utf-8")
# find all OpenCollection definitions
idx=0
while True:
    i=cpp.find("void APrototypeBattleMode::OpenCollection", idx)
    if i<0: break
    print("DEF at", i)
    print(cpp[i:i+200])
    print("---")
    idx=i+10
# FireActiveSkill defs
idx=0
while True:
    i=cpp.find("void APrototypeBattleMode::FireActiveSkill", idx)
    if i<0: break
    print("FIRE at", i)
    print(cpp[i:i+350])
    print("---")
    idx=i+10
# Tick hook
i=cpp.find("SkillShell.ObserveHits")
print("TICK context:\n", cpp[i-200:i+400])
# Fighting state set
i=cpp.find("SkillShell.ResetForBout")
print("RESET context:\n", cpp[i-120:i+200])
sk=Path(r"C:\BeybladeUE\Source\BeybladePrototype\SkillRuntime.h").read_text(encoding="utf-8")
print("LabelZh line:", [ln for ln in sk.splitlines() if "LabelZh" in ln])
