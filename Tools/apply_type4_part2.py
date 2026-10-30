# -*- coding: utf-8 -*-
from pathlib import Path
import re

ROOT = Path(r"C:\BeybladeUE")

# --- BattleSimulationTest.cpp: extend Grade1DataLanding ---
p = ROOT / "Source/BeybladePrototype/BattleSimulationTest.cpp"
t = p.read_text(encoding="utf-8")
needle = """\tconst FBeyLoadout Attack = MakeLoadout(EBeyType::Attack, EBeyGrade::Grade1);
\tconst FBeyLoadout Defense = MakeLoadout(EBeyType::Defense, EBeyGrade::Grade1);
\tconst FBeyLoadout Stamina = MakeLoadout(EBeyType::Stamina, EBeyGrade::Grade1);
\tTestTrue(TEXT("table ATK attack"), FMath::IsNearlyEqual(Attack.Attack, 1.35));
\tTestTrue(TEXT("table ATK def"), FMath::IsNearlyEqual(Attack.Defense, 0.85));
\tTestTrue(TEXT("table ATK mass"), FMath::IsNearlyEqual(Attack.Mass, 0.90));
\tTestTrue(TEXT("table ATK k"), FMath::IsNearlyEqual(Attack.SpinDecayPerSec, 0.163));
\tTestTrue(TEXT("table DEF attack"), FMath::IsNearlyEqual(Defense.Attack, 0.85));
\tTestTrue(TEXT("table DEF def"), FMath::IsNearlyEqual(Defense.Defense, 1.35));
\tTestTrue(TEXT("table DEF mass"), FMath::IsNearlyEqual(Defense.Mass, 1.15));
\tTestTrue(TEXT("table DEF k"), FMath::IsNearlyEqual(Defense.SpinDecayPerSec, 0.122));
\tTestTrue(TEXT("table STA attack"), FMath::IsNearlyEqual(Stamina.Attack, 0.95));
\tTestTrue(TEXT("table STA def"), FMath::IsNearlyEqual(Stamina.Defense, 1.05));
\tTestTrue(TEXT("table STA mass"), FMath::IsNearlyEqual(Stamina.Mass, 1.30));
\tTestTrue(TEXT("table STA k"), FMath::IsNearlyEqual(Stamina.SpinDecayPerSec, 0.103));"""
repl = """\tconst FBeyLoadout Attack = MakeLoadout(EBeyType::Attack, EBeyGrade::Grade1);
\tconst FBeyLoadout Defense = MakeLoadout(EBeyType::Defense, EBeyGrade::Grade1);
\tconst FBeyLoadout Stamina = MakeLoadout(EBeyType::Stamina, EBeyGrade::Grade1);
\tconst FBeyLoadout Balance = MakeLoadout(EBeyType::Balance, EBeyGrade::Grade1);
\tTestTrue(TEXT("table ATK attack"), FMath::IsNearlyEqual(Attack.Attack, 1.35));
\tTestTrue(TEXT("table ATK def"), FMath::IsNearlyEqual(Attack.Defense, 0.85));
\tTestTrue(TEXT("table ATK mass"), FMath::IsNearlyEqual(Attack.Mass, 0.90));
\tTestTrue(TEXT("table ATK k"), FMath::IsNearlyEqual(Attack.SpinDecayPerSec, 0.163));
\tTestTrue(TEXT("table DEF attack"), FMath::IsNearlyEqual(Defense.Attack, 0.85));
\tTestTrue(TEXT("table DEF def"), FMath::IsNearlyEqual(Defense.Defense, 1.35));
\tTestTrue(TEXT("table DEF mass"), FMath::IsNearlyEqual(Defense.Mass, 1.15));
\tTestTrue(TEXT("table DEF k"), FMath::IsNearlyEqual(Defense.SpinDecayPerSec, 0.122));
\tTestTrue(TEXT("table STA attack"), FMath::IsNearlyEqual(Stamina.Attack, 0.95));
\tTestTrue(TEXT("table STA def"), FMath::IsNearlyEqual(Stamina.Defense, 1.05));
\tTestTrue(TEXT("table STA mass"), FMath::IsNearlyEqual(Stamina.Mass, 1.30));
\tTestTrue(TEXT("table STA k"), FMath::IsNearlyEqual(Stamina.SpinDecayPerSec, 0.103));
\tTestTrue(TEXT("table BAL attack"), FMath::IsNearlyEqual(Balance.Attack, 1.10));
\tTestTrue(TEXT("table BAL def"), FMath::IsNearlyEqual(Balance.Defense, 1.10));
\tTestTrue(TEXT("table BAL mass"), FMath::IsNearlyEqual(Balance.Mass, 1.05));
\tTestTrue(TEXT("table BAL k"), FMath::IsNearlyEqual(Balance.SpinDecayPerSec, 0.135));
\tTestEqual(TEXT("type label BAL"), FString(Balance.TypeLabel()), FString(TEXT("BALANCE")));
\t// STA mass highest; decay order ATK > BAL > DEF > STA
\tTestTrue(TEXT("STA mass highest"), Stamina.Mass >= Defense.Mass && Stamina.Mass >= Balance.Mass && Stamina.Mass >= Attack.Mass);
\tTestTrue(TEXT("decay ATK>BAL"), Attack.SpinDecayPerSec > Balance.SpinDecayPerSec);
\tTestTrue(TEXT("decay BAL>DEF"), Balance.SpinDecayPerSec > Defense.SpinDecayPerSec);
\tTestTrue(TEXT("decay DEF>STA"), Defense.SpinDecayPerSec > Stamina.SpinDecayPerSec);"""
if needle not in t:
    raise SystemExit("Grade1 test needle not found")
t = t.replace(needle, repl)
p.write_text(t, encoding="utf-8")
print("patched BattleSimulationTest.cpp")

# --- ArtHUD TypeColor for Balance ---
p = ROOT / "Source/BeybladePrototype/ArtHUD.cpp"
t = p.read_text(encoding="utf-8")
if "EBeyType::Balance" not in t or "均衡型" not in t:
    raise SystemExit("ArtHUD missing Balance TypeName from part1")
old_color = """FLinearColor TypeColor(EBeyType Type)
{
    switch (Type)
    {
    case EBeyType::Defense: return FLinearColor(.26f, .66f, .95f);
    case EBeyType::Stamina: return FLinearColor(.31f, .79f, .52f);
    default: return FLinearColor(.96f, .35f, .24f);
    }
}"""
new_color = """FLinearColor TypeColor(EBeyType Type)
{
    switch (Type)
    {
    case EBeyType::Defense: return FLinearColor(.26f, .66f, .95f);
    case EBeyType::Stamina: return FLinearColor(.31f, .79f, .52f);
    case EBeyType::Balance: return FLinearColor(.85f, .72f, .28f);
    default: return FLinearColor(.96f, .35f, .24f);
    }
}"""
if old_color in t:
    t = t.replace(old_color, new_color)
    p.write_text(t, encoding="utf-8")
    print("patched ArtHUD TypeColor")
else:
    print("WARN ArtHUD TypeColor block not exact; checking Balance color")
    if "EBeyType::Balance: return FLinearColor" not in t:
        # insert before default
        t2 = t.replace(
            "case EBeyType::Stamina: return FLinearColor(.31f, .79f, .52f);\n    default: return FLinearColor(.96f, .35f, .24f);",
            "case EBeyType::Stamina: return FLinearColor(.31f, .79f, .52f);\n    case EBeyType::Balance: return FLinearColor(.85f, .72f, .28f);\n    default: return FLinearColor(.96f, .35f, .24f);",
        )
        if t2 == t:
            raise SystemExit("TypeColor insert failed")
        p.write_text(t2, encoding="utf-8")
        print("patched ArtHUD TypeColor via insert")

# --- PrototypeBattle ApplyBeyArt 5-slot ---
p = ROOT / "Source/BeybladePrototype/PrototypeBattle.cpp"
t = p.read_text(encoding="utf-8")
old_load = """        for (const TCHAR* Name : {TEXT("Chifeng"), TEXT("Bilei"), TEXT("Hengren")})
        {
            const FString Path = FString::Printf(TEXT("/Game/Beyblade/Art/Tripo_v1/SM_%s.SM_%s"), Name, Name);
            ImportedBeys.Add(LoadObject<UStaticMesh>(nullptr, *Path));
        }"""
new_load = """        // Pool slots 0..4: ChiFeng / BiLei / ChangXuan / HengRen / ChiWen (ChiWen may be missing -> nullptr ok)
        for (const TCHAR* Name : {TEXT("Chifeng"), TEXT("Bilei"), TEXT("Changxuan"), TEXT("Hengren"), TEXT("Chiwen")})
        {
            const FString Path = FString::Printf(TEXT("/Game/Beyblade/Art/Tripo_v1/SM_%s.SM_%s"), Name, Name);
            ImportedBeys.Add(LoadObject<UStaticMesh>(nullptr, *Path));
        }"""
if old_load not in t:
    raise SystemExit("ImportedBeys load block not found")
t = t.replace(old_load, new_load)
old_apply = """void APrototypeBattleMode::ApplyBeyArt()
{
    if (ImportedBeys.Num() != 3 || BeyArt.Num() != 2) return;
    const int32 P1 = MatchFlow.bBlindPhase && MatchFlow.BlindChoiceP1 >= 0 ? MatchFlow.BlindChoiceP1
        : MatchFlow.Pick.Count > MatchFlow.CurrentLineupIndex ? MatchFlow.Pick.Lineup[MatchFlow.CurrentLineupIndex] : 0;
    const int32 P2 = MatchFlow.bBlindPhase && MatchFlow.BlindChoiceP2 >= 0 ? MatchFlow.BlindChoiceP2 : 1;
    const int32 Slots[2] = {P1, P2};
    for (int32 I = 0; I < 2; ++I)
    {
        if (!Beys[I]) continue;
        auto* Original = Beys[I]->FindComponentByClass<UStaticMeshComponent>();
        if (!Original) continue;
        // Hengren is appearance-only in slot 4 until balance-type gameplay is defined.
        UStaticMesh* Mesh = Slots[I] == 2 ? nullptr : ImportedBeys[Slots[I] == 0 ? 0 : Slots[I] == 3 ? 2 : 1];"""
new_apply = """void APrototypeBattleMode::ApplyBeyArt()
{
    if (ImportedBeys.Num() < 5 || BeyArt.Num() != 2) return;
    const int32 P1 = MatchFlow.bBlindPhase && MatchFlow.BlindChoiceP1 >= 0 ? MatchFlow.BlindChoiceP1
        : MatchFlow.Pick.Count > MatchFlow.CurrentLineupIndex ? MatchFlow.Pick.Lineup[MatchFlow.CurrentLineupIndex] : 0;
    const int32 P2 = MatchFlow.bBlindPhase && MatchFlow.BlindChoiceP2 >= 0 ? MatchFlow.BlindChoiceP2 : 1;
    const int32 Slots[2] = {P1, P2};
    for (int32 I = 0; I < 2; ++I)
    {
        if (!Beys[I]) continue;
        auto* Original = Beys[I]->FindComponentByClass<UStaticMeshComponent>();
        if (!Original) continue;
        // Direct pool-slot -> ImportedBeys[slot]; missing mesh keeps original placeholder visible.
        const int32 Slot = FMath::Clamp(Slots[I], 0, ImportedBeys.Num() - 1);
        UStaticMesh* Mesh = ImportedBeys[Slot];"""
if old_apply not in t:
    raise SystemExit("ApplyBeyArt block not found")
t = t.replace(old_apply, new_apply)
p.write_text(t, encoding="utf-8")
print("patched PrototypeBattle.cpp ApplyBeyArt")

# Verify Grade1Balance has Balance
g = (ROOT / "Source/BeybladePrototype/Grade1Balance.h").read_text(encoding="utf-8")
assert "EBeyType::Balance" in g and "Rows[4]" in g and "G1_BAL_Attack" in g
b = (ROOT / "Source/BeybladePrototype/BattleSimulation.h").read_text(encoding="utf-8")
assert "Balance = 3" in b and 'TEXT("BALANCE")' in b
print("VERIFY_OK")
