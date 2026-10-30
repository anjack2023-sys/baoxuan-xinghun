from pathlib import Path
root=Path(r"C:\BeybladeUE\Source\BeybladePrototype")
for n in ["MatchFlow.h","LobbyClickUI.h","PrototypeBattle.h","SkillRuntime.h","CollectionCatalog.h"]:
    t=(root/n).read_text(encoding="utf-8")
    print("====",n,"lines",t.count("\n")+1)
    checks={
    "MatchFlow.h":["Collection = 7","EnterCollection","CollectionFocus"],
    "LobbyClickUI.h":["OpenCollect","FireSkill","CollectPos","SkillBtnPos","EMatchFlowState::Collection","EMatchFlowState::Fighting"],
    "PrototypeBattle.h":["FireActiveSkill","SkillShell","OpenCollection","GetSkillShell"],
    "SkillRuntime.h":["TryFire","ObserveHits","bPendingRestore","NeedSeq"],
    "CollectionCatalog.h":["炽纹","煌铠","翠磐","霜环","Count = 8"],
    }
    for c in checks.get(n,[]):
        print(" ",c, "OK" if c in t else "MISSING")
cpp=(root/"PrototypeBattle.cpp").read_text(encoding="utf-8")
for c in ["OpenCollection","FireActiveSkill","SKILL_FIRE","SkillShell.ResetForBout","SkillShell.ObserveHits","OpenCollect","FireSkill"]:
    print("cpp",c, cpp.count(c))
hud=(root/"ArtHUD.cpp").read_text(encoding="utf-8")
for c in ["Collection","SkillBtnPos","CollectPos","疾突","陀螺收集","PortraitChiwen"]:
    print("hud",c, c in hud)
# MatchFlow EnterCollection placement sanity
mf=(root/"MatchFlow.h").read_text(encoding="utf-8")
print("EnterCollection near ResetMatchPool", "EnterCollection" in mf and "ResetMatchPool" in mf)
idx=mf.find("EnterCollection")
print(mf[idx:idx+400] if idx>=0 else "no enter")
