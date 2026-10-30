from pathlib import Path
cpp_path=Path(r"C:\BeybladeUE\Source\BeybladePrototype\PrototypeBattle.cpp")
cpp=cpp_path.read_text(encoding="utf-8")

# Fix broken indentation from first replace
cpp=cpp.replace(
'''        SkillShell.ResetForBout();
    MatchFlow.State = EMatchFlowState::Fighting;''',
'''        SkillShell.ResetForBout();
        MatchFlow.State = EMatchFlowState::Fighting;'''
)

# Ensure interactive launch also resets - find all Fighting assignments
count=cpp.count("MatchFlow.State = EMatchFlowState::Fighting")
print("Fighting assigns", count)
# Add Reset before every Fighting assign if not already preceded by ResetForBout within 80 chars
import re
def ensure_reset(m):
    prev=cpp[max(0,m.start()-80):m.start()]
    if "SkillShell.ResetForBout" in prev:
        return m.group(0)
    return "SkillShell.ResetForBout();\n\t\t" + m.group(0)

# careful - only for interactive StartBattle
# Search StartBattleInternal / Prep launch path
for needle in ["StartBattleInternal", "void APrototypeBattleMode::Launch"]:
    i=cpp.find(needle)
    print(needle, "at", i)
    if i>=0:
        print(cpp[i:i+600])
        print("====")

cpp_path.write_text(cpp, encoding="utf-8")
print("indent fix applied")
