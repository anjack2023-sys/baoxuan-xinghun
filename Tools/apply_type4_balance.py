# -*- coding: utf-8 -*-
"""Apply TYPE4 Balance source edits on this machine. Does not touch Feel constants."""
from pathlib import Path
import re, shutil, datetime

ROOT = Path(r"C:\BeybladeUE")
stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
bak = ROOT / "Saved" / "Backups" / f"before_type4_balance_{stamp}"
bak.mkdir(parents=True, exist_ok=True)
files = [
    ROOT/"Source/BeybladePrototype/BattleSimulation.h",
    ROOT/"Source/BeybladePrototype/Grade1Balance.h",
    ROOT/"Source/BeybladePrototype/ArtHUD.cpp",
    ROOT/"Source/BeybladePrototype/MatchFlow.h",
    ROOT/"Source/BeybladePrototype/BattleSimulationTest.cpp",
    ROOT/"Source/BeybladePrototype/PrototypeBattle.cpp",
]
for f in files:
    if f.exists():
        shutil.copy2(f, bak / f.name)
        print("backed", f.name)

# --- BattleSimulation.h ---
p = ROOT/"Source/BeybladePrototype/BattleSimulation.h"
t = p.read_text(encoding="utf-8")
t2 = t.replace(
"""enum class EBeyType : uint8
{
\tAttack = 0,
\tDefense = 1,
\tStamina = 2
};""",
"""enum class EBeyType : uint8
{
\tAttack = 0,
\tDefense = 1,
\tStamina = 2,
\tBalance = 3
};""")
# TypeLabel in FBeyLoadout
t2 = t2.replace(
"""\t\tswitch (Type)
\t\t{
\t\tcase EBeyType::Defense: return TEXT("DEFENSE");
\t\tcase EBeyType::Stamina: return TEXT("STAMINA");
\t\tdefault: return TEXT("ATTACK");
\t\t}""",
"""\t\tswitch (Type)
\t\t{
\t\tcase EBeyType::Defense: return TEXT("DEFENSE");
\t\tcase EBeyType::Stamina: return TEXT("STAMINA");
\t\tcase EBeyType::Balance: return TEXT("BALANCE");
\t\tdefault: return TEXT("ATTACK");
\t\t}""", 1)
# TypeLabel(int32) in FBattleSimulation - second occurrence
t2 = t2.replace(
"""\tswitch (Type[Index])
\t\t{
\t\tcase EBeyType::Defense: return TEXT("DEFENSE");
\t\tcase EBeyType::Stamina: return TEXT("STAMINA");
\t\tdefault: return TEXT("ATTACK");
\t\t}""",
"""\tswitch (Type[Index])
\t\t{
\t\tcase EBeyType::Defense: return TEXT("DEFENSE");
\t\tcase EBeyType::Stamina: return TEXT("STAMINA");
\t\tcase EBeyType::Balance: return TEXT("BALANCE");
\t\tdefault: return TEXT("ATTACK");
\t\t}""")
# Comment update
t2 = t2.replace(
"// Minimal data table: Grade1 x Attack/Defense/Stamina. Grade2/3 are stubs (slower decay only).",
"// Minimal data table: Grade1 x Attack/Defense/Stamina/Balance. Grade2/3 are stubs (slower decay only).")
if t2 == t:
    raise SystemExit("BattleSimulation.h: no changes applied")
p.write_text(t2, encoding="utf-8")
print("patched BattleSimulation.h")

# --- Grade1Balance.h ---
p = ROOT/"Source/BeybladePrototype/Grade1Balance.h"
t = p.read_text(encoding="utf-8")
t2 = t.replace(
"""\tinline FRow& MutableRow(EBeyType Type)
\t{
\t\tstatic FRow Rows[3] = {
\t\t\t{1.35, 0.85, 0.90, 0.163}, // Attack — mirrors CSV
\t\t\t{0.85, 1.35, 1.15, 0.122}, // Defense
\t\t\t{0.95, 1.05, 1.30, 0.103}, // Stamina
\t\t};
\t\tconst int32 Idx = (Type == EBeyType::Defense) ? 1 : (Type == EBeyType::Stamina ? 2 : 0);
\t\treturn Rows[Idx];
\t}""",
"""\tinline FRow& MutableRow(EBeyType Type)
\t{
\t\tstatic FRow Rows[4] = {
\t\t\t{1.35, 0.85, 0.90, 0.163}, // Attack — mirrors CSV
\t\t\t{0.85, 1.35, 1.15, 0.122}, // Defense
\t\t\t{0.95, 1.05, 1.30, 0.103}, // Stamina
\t\t\t{1.10, 1.10, 1.05, 0.135}, // Balance
\t\t};
\t\tint32 Idx = 0;
\t\tif (Type == EBeyType::Defense) Idx = 1;
\t\telse if (Type == EBeyType::Stamina) Idx = 2;
\t\telse if (Type == EBeyType::Balance) Idx = 3;
\t\treturn Rows[Idx];
\t}""")
# encoding may have replaced em-dash - try alternate if needed
if "Rows[4]" not in t2:
    # try with whatever dash is in file
    m = re.search(r"static FRow Rows\[3\] = \{.*?\};\s*const int32 Idx = .*?;\s*return Rows\[Idx\];", t, re.S)
    if not m:
        raise SystemExit("Grade1Balance MutableRow block not found")
    repl = """static FRow Rows[4] = {
\t\t\t{1.35, 0.85, 0.90, 0.163}, // Attack mirrors CSV
\t\t\t{0.85, 1.35, 1.15, 0.122}, // Defense
\t\t\t{0.95, 1.05, 1.30, 0.103}, // Stamina
\t\t\t{1.10, 1.10, 1.05, 0.135}, // Balance
\t\t};
\t\tint32 Idx = 0;
\t\tif (Type == EBeyType::Defense) Idx = 1;
\t\telse if (Type == EBeyType::Stamina) Idx = 2;
\t\telse if (Type == EBeyType::Balance) Idx = 3;
\t\treturn Rows[Idx];"""
    t2 = t[:m.start()] + repl + t[m.end():]

t2 = t2.replace(
"""\tif (S.Equals(TEXT("DEFENSE"), ESearchCase::IgnoreCase) || S.Equals(TEXT("DEF"), ESearchCase::IgnoreCase)) return EBeyType::Defense;
\t\tif (S.Equals(TEXT("STAMINA"), ESearchCase::IgnoreCase) || S.Equals(TEXT("STA"), ESearchCase::IgnoreCase)) return EBeyType::Stamina;
\t\treturn EBeyType::Attack;""",
"""\tif (S.Equals(TEXT("DEFENSE"), ESearchCase::IgnoreCase) || S.Equals(TEXT("DEF"), ESearchCase::IgnoreCase)) return EBeyType::Defense;
\t\tif (S.Equals(TEXT("STAMINA"), ESearchCase::IgnoreCase) || S.Equals(TEXT("STA"), ESearchCase::IgnoreCase)) return EBeyType::Stamina;
\t\tif (S.Equals(TEXT("BALANCE"), ESearchCase::IgnoreCase) || S.Equals(TEXT("BAL"), ESearchCase::IgnoreCase)) return EBeyType::Balance;
\t\treturn EBeyType::Attack;""")

# Applied >= 3 -> >= 4
t2 = t2.replace("return Applied >= 3;", "return Applied >= 4;")

# G1_BAL_* tunables
if "G1_BAL_Attack" not in t2:
    t2 = t2.replace(
"""\t\telse if (Key == TEXT("G1_STA_SpinDecay")) MutableRow(EBeyType::Stamina).SpinDecayPerSec = Value;
\t\telse if (Key == TEXT("G2_SpinDecayMul")) Grade2Mul() = Value;""",
"""\t\telse if (Key == TEXT("G1_STA_SpinDecay")) MutableRow(EBeyType::Stamina).SpinDecayPerSec = Value;
\t\telse if (Key == TEXT("G1_BAL_Attack")) MutableRow(EBeyType::Balance).Attack = Value;
\t\telse if (Key == TEXT("G1_BAL_Defense")) MutableRow(EBeyType::Balance).Defense = Value;
\t\telse if (Key == TEXT("G1_BAL_Mass")) MutableRow(EBeyType::Balance).Mass = Value;
\t\telse if (Key == TEXT("G1_BAL_SpinDecay")) MutableRow(EBeyType::Balance).SpinDecayPerSec = Value;
\t\telse if (Key == TEXT("G2_SpinDecayMul")) Grade2Mul() = Value;""")

# Log line include BAL
old_log = """\t\tUE_LOG(LogTemp, Display, TEXT("GRADE1_DATA loaded_from_csv=%d atk=(%.3f,%.3f,%.3f,k=%.3f) def=(%.3f,%.3f,%.3f,k=%.3f) sta=(%.3f,%.3f,%.3f,k=%.3f)"),
\t\t\tOk ? 1 : 0,
\t\t\tMutableRow(EBeyType::Attack).Attack, MutableRow(EBeyType::Attack).Defense, MutableRow(EBeyType::Attack).Mass, MutableRow(EBeyType::Attack).SpinDecayPerSec,
\t\t\tMutableRow(EBeyType::Defense).Attack, MutableRow(EBeyType::Defense).Defense, MutableRow(EBeyType::Defense).Mass, MutableRow(EBeyType::Defense).SpinDecayPerSec,
\t\t\tMutableRow(EBeyType::Stamina).Attack, MutableRow(EBeyType::Stamina).Defense, MutableRow(EBeyType::Stamina).Mass, MutableRow(EBeyType::Stamina).SpinDecayPerSec);"""
new_log = """\t\tUE_LOG(LogTemp, Display, TEXT("GRADE1_DATA loaded_from_csv=%d atk=(%.3f,%.3f,%.3f,k=%.3f) def=(%.3f,%.3f,%.3f,k=%.3f) sta=(%.3f,%.3f,%.3f,k=%.3f) bal=(%.3f,%.3f,%.3f,k=%.3f)"),
\t\t\tOk ? 1 : 0,
\t\t\tMutableRow(EBeyType::Attack).Attack, MutableRow(EBeyType::Attack).Defense, MutableRow(EBeyType::Attack).Mass, MutableRow(EBeyType::Attack).SpinDecayPerSec,
\t\t\tMutableRow(EBeyType::Defense).Attack, MutableRow(EBeyType::Defense).Defense, MutableRow(EBeyType::Defense).Mass, MutableRow(EBeyType::Defense).SpinDecayPerSec,
\t\t\tMutableRow(EBeyType::Stamina).Attack, MutableRow(EBeyType::Stamina).Defense, MutableRow(EBeyType::Stamina).Mass, MutableRow(EBeyType::Stamina).SpinDecayPerSec,
\t\t\tMutableRow(EBeyType::Balance).Attack, MutableRow(EBeyType::Balance).Defense, MutableRow(EBeyType::Balance).Mass, MutableRow(EBeyType::Balance).SpinDecayPerSec);"""
if old_log in t2:
    t2 = t2.replace(old_log, new_log)

# ResetLoadStateForTests
t2 = t2.replace(
"""\t\tMutableRow(EBeyType::Attack) = {1.35, 0.85, 0.90, 0.163};
\t\tMutableRow(EBeyType::Defense) = {0.85, 1.35, 1.15, 0.122};
\t\tMutableRow(EBeyType::Stamina) = {0.95, 1.05, 1.30, 0.103};""",
"""\t\tMutableRow(EBeyType::Attack) = {1.35, 0.85, 0.90, 0.163};
\t\tMutableRow(EBeyType::Defense) = {0.85, 1.35, 1.15, 0.122};
\t\tMutableRow(EBeyType::Stamina) = {0.95, 1.05, 1.30, 0.103};
\t\tMutableRow(EBeyType::Balance) = {1.10, 1.10, 1.05, 0.135};""")

p.write_text(t2, encoding="utf-8")
print("patched Grade1Balance.h")

# --- ArtHUD.cpp TypeName + BeyName ---
p = ROOT/"Source/BeybladePrototype/ArtHUD.cpp"
t = p.read_text(encoding="utf-8")
# TypeName - do not use 耐力
t2 = re.sub(
    r"const TCHAR\* TypeName\(EBeyType Type\)\s*\{.*?^\}",
    """const TCHAR* TypeName(EBeyType Type)
{
    switch (Type)
    {
    case EBeyType::Defense: return TEXT("防御型");
    case EBeyType::Stamina: return TEXT("持久型");
    case EBeyType::Balance: return TEXT("均衡型");
    default: return TEXT("攻击型");
    }
}""",
    t, count=1, flags=re.S|re.M)
t2 = re.sub(
    r"const TCHAR\* BeyName\(int32 Index\)\s*\{.*?^\}",
    """const TCHAR* BeyName(int32 Index)
{
    const TCHAR* Names[] = {TEXT("赤锋"), TEXT("壁垒"), TEXT("长旋"), TEXT("衡刃"), TEXT("炽纹")};
    return Names[FMath::Clamp(Index, 0, 4)];
}""",
    t2, count=1, flags=re.S|re.M)
# Portraits array: Chifeng, Bilei, Changxuan, Hengren, Chiwen (Chiwen may miss portrait - use Chifeng fallback or nullptr)
t2 = t2.replace(
    'const TCHAR* Portraits[] = {TEXT("PortraitChifeng"), TEXT("PortraitBilei"), TEXT("PortraitChangxuan"), nullptr, TEXT("PortraitBilei")};',
    'const TCHAR* Portraits[] = {TEXT("PortraitChifeng"), TEXT("PortraitBilei"), TEXT("PortraitChangxuan"), TEXT("PortraitHengren"), TEXT("PortraitChifeng")};')
# Preview hint for slot2 no longer "model pending"
t2 = t2.replace(
    'Text(Preview == 2 ? TEXT("立绘已就绪 · 三维模型待接入") : TEXT("陀螺展示"), FVector2D(1690, 738), 20, Cream, true);',
    'Text(TEXT("陀螺展示"), FVector2D(1690, 738), 20, Cream, true);')
# If encoding garbled the Chinese in replace, leave TypeName/BeyName from regex
if "均衡型" not in t2:
    raise SystemExit("ArtHUD TypeName patch failed")
p.write_text(t2, encoding="utf-8")
print("patched ArtHUD.cpp")

# --- MatchFlow.h pool ---
p = ROOT/"Source/BeybladePrototype/MatchFlow.h"
t = p.read_text(encoding="utf-8")
t2 = t.replace(
"""\tFPickPoolSlot Pool[PoolSize] = {
\t\t{TEXT("B0-ATK"), EBeyType::Attack},
\t\t{TEXT("B1-DEF"), EBeyType::Defense},
\t\t{TEXT("B2-STA"), EBeyType::Stamina},
\t\t{TEXT("B3-ATK"), EBeyType::Attack},
\t\t{TEXT("B4-DEF"), EBeyType::Defense},
\t};""",
"""\tFPickPoolSlot Pool[PoolSize] = {
\t\t{TEXT("ChiFeng-ATK"), EBeyType::Attack},
\t\t{TEXT("BiLei-DEF"), EBeyType::Defense},
\t\t{TEXT("ChangXuan-STA"), EBeyType::Stamina},
\t\t{TEXT("HengRen-BAL"), EBeyType::Balance},
\t\t{TEXT("ChiWen-ATK"), EBeyType::Attack},
\t};""")
if "HengRen-BAL" not in t2:
    raise SystemExit("MatchFlow pool patch failed")
p.write_text(t2, encoding="utf-8")
print("patched MatchFlow.h")

print("DONE backups at", bak)
print("NOTE: BattleSimulationTest + PrototypeBattle ApplyBeyArt patched by companion steps")
