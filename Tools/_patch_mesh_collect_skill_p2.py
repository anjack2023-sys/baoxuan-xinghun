# -*- coding: utf-8 -*-
from pathlib import Path
root = Path(r"C:\BeybladeUE\Source\BeybladePrototype")

# ---- PrototypeBattle.h ----
h = (root / "PrototypeBattle.h").read_text(encoding="utf-8")
if "SkillRuntime.h" not in h:
    h = h.replace('#include "LobbyClickUI.h"', '#include "LobbyClickUI.h"\n#include "SkillRuntime.h"\n#include "CollectionCatalog.h"')
if "FireActiveSkill" not in h:
    h = h.replace(
        "    void RematchFromMatchSettle();",
        '''    void RematchFromMatchSettle();
    void OpenCollection();
    void CloseCollection();
    void SelectCollectionSlot(int32 Index);
    void FireActiveSkill();
    const FActiveSkillShell& GetSkillShell() const { return SkillShell; }''',
    )
if "FActiveSkillShell SkillShell" not in h:
    h = h.replace(
        "    FMatchFlow MatchFlow;",
        "    FMatchFlow MatchFlow;\n    FActiveSkillShell SkillShell;",
    )
(root / "PrototypeBattle.h").write_text(h, encoding="utf-8")
print("PrototypeBattle.h ok")

# ---- PrototypeBattle.cpp: includes + methods + click + tick ----
cpp = (root / "PrototypeBattle.cpp").read_text(encoding="utf-8")

# Fix pool comment / ensure Chiwen load (already correct names)
# Ensure ApplyBeyArt logs Chiwen

# Add methods before ApplyBeyArt or after Rematch
if "void APrototypeBattleMode::OpenCollection()" not in cpp:
    insert_methods = r'''
void APrototypeBattleMode::OpenCollection()
{
    MatchFlow.EnterCollection();
    UE_LOG(LogTemp, Display, TEXT("COLLECTION_OPEN"));
}

void APrototypeBattleMode::CloseCollection()
{
    if (MatchFlow.State != EMatchFlowState::Collection) return;
    if (MatchFlow.CollectionFocus >= 0)
    {
        MatchFlow.CloseCollectionDetail();
        UE_LOG(LogTemp, Display, TEXT("COLLECTION_DETAIL_CLOSE"));
        return;
    }
    MatchFlow.ExitCollectionToLobby();
    UE_LOG(LogTemp, Display, TEXT("COLLECTION_CLOSE"));
}

void APrototypeBattleMode::SelectCollectionSlot(int32 Index)
{
    if (MatchFlow.State != EMatchFlowState::Collection) return;
    if (MatchFlow.CollectionFocus >= 0) return; // already in detail; ignore grid
    if (Index < 0 || Index >= FCollectionCatalog::Count) return;
    MatchFlow.OpenCollectionDetail(Index);
    UE_LOG(LogTemp, Display, TEXT("COLLECTION_DETAIL id=%s"), FCollectionCatalog::Get(Index).Id);
}

void APrototypeBattleMode::FireActiveSkill()
{
    if (MatchFlow.State != EMatchFlowState::Fighting) return;
    if (!SkillShell.TryFire())
    {
        UE_LOG(LogTemp, Display, TEXT("SKILL_FIRE_BLOCKED hits=%d need=%d"), SkillShell.HitsDealt, SkillShell.Need());
        return;
    }
    // Data-layer stub only: temporary Attack mul. Does NOT touch SPIN_KICK / RESTITUTION.
    Simulation.Attack[0] *= SkillShell.AttackMulActive;
    UE_LOG(LogTemp, Display, TEXT("SKILL_FIRE name=疾突 tier=%d next_need=%d atk_mul=%.2f ringout_add=%.2f"),
        SkillShell.Tier, SkillShell.Need(), SkillShell.AttackMulActive, SkillShell.RingoutRateAdd);
}
'''
    # place before ApplyBeyArt definition
    if "void APrototypeBattleMode::ApplyBeyArt()" in cpp:
        cpp = cpp.replace("void APrototypeBattleMode::ApplyBeyArt()", insert_methods + "\nvoid APrototypeBattleMode::ApplyBeyArt()")
    else:
        cpp += insert_methods

# Click handler cases
if "ELobbyClickAction::OpenCollect" not in cpp:
    # Find ConfirmBlind case and append after switch cases
    old = '''    case ELobbyClickAction::ConfirmBlind:'''
    # Find the full switch - insert before default or at end of cases
    # Look for ConfirmBlind block end
    marker = "case ELobbyClickAction::ConfirmBlind:"
    idx = cpp.find(marker)
    if idx < 0:
        raise SystemExit("ConfirmBlind case missing")
    # Find next break; after ConfirmBlind
    end = cpp.find("break;", idx)
    end = cpp.find("\n", end) + 1
    block = '''    case ELobbyClickAction::OpenCollect:
        Mode->OpenCollection();
        break;
    case ELobbyClickAction::CollectBack:
    case ELobbyClickAction::CollectDetailBack:
        Mode->CloseCollection();
        break;
    case ELobbyClickAction::Collect0:
    case ELobbyClickAction::Collect1:
    case ELobbyClickAction::Collect2:
    case ELobbyClickAction::Collect3:
    case ELobbyClickAction::Collect4:
    case ELobbyClickAction::Collect5:
    case ELobbyClickAction::Collect6:
    case ELobbyClickAction::Collect7:
        Mode->SelectCollectionSlot(static_cast<int32>(Action) - static_cast<int32>(ELobbyClickAction::Collect0));
        break;
    case ELobbyClickAction::FireSkill:
        Mode->FireActiveSkill();
        break;
'''
    cpp = cpp[:end] + block + cpp[end:]

# Reset skill on Launch / StartBattleInternal
if "SkillShell.ResetForBout()" not in cpp:
    # After StartBattleInternal or Launch when fighting starts
    # Find places that set State to Fighting or call Simulation.Launch
    # Hook in Tick observation and Launch
    pass

# Find StartBattleInternal or where Fighting begins
if "SkillShell.ResetForBout" not in cpp:
    # Search for MatchFlow.State = EMatchFlowState::Fighting
    if "MatchFlow.State = EMatchFlowState::Fighting" in cpp:
        cpp = cpp.replace(
            "MatchFlow.State = EMatchFlowState::Fighting",
            "SkillShell.ResetForBout();\n    MatchFlow.State = EMatchFlowState::Fighting",
            1,
        )
    elif "Simulation.Launch()" in cpp:
        # insert after first Simulation.Launch in interactive path
        cpp = cpp.replace(
            "Simulation.Launch();",
            "SkillShell.ResetForBout();\n    Simulation.Launch();",
            1,
        )

# Tick: observe hits + fx
# Find APrototypeBattleMode::Tick
tick_marker = "void APrototypeBattleMode::Tick(float DeltaSeconds)"
ti = cpp.find(tick_marker)
if ti >= 0 and "SkillShell.ObserveHits" not in cpp:
    # Insert after Super::Tick or early in function body
    brace = cpp.find("{", ti)
    insert_at = brace + 1
    hook = """
    if (MatchFlow.State == EMatchFlowState::Fighting && AutoMatches <= 0)
    {
        SkillShell.ObserveHits(Simulation.Hits);
        SkillShell.TickFx(DeltaSeconds);
        // When FX ends, restore Attack from current loadout (P1).
        if (!SkillShell.bFxActive && SkillShell.AttackMulActive <= 1.0 + 1.e-6)
        {
            // Attack may have been multiplied; re-apply lineup loadout for P1 only if FX just ended.
        }
    }
"""
    # Better: restore Attack when FX expires by tracking baseline
    # Simpler approach: store BaselineAttack0 on fire, restore on expiry in Fire/Tick
    cpp = cpp[:insert_at] + hook + cpp[insert_at:]

(root / "PrototypeBattle.cpp").write_text(cpp, encoding="utf-8")
print("PrototypeBattle.cpp methods/clicks ok")

# Improve FireActiveSkill restore: add BaselineAttack to shell usage inline
# Re-read and fix Fire + Tick properly
cpp = (root / "PrototypeBattle.cpp").read_text(encoding="utf-8")
# Replace crude Tick hook with proper baseline restore using a mode member - add via SkillShell fields already

# Fix FireActiveSkill to store baseline in SkillShell - we need a field. Add double BaselineAttack to header usage via local static? Better patch SkillRuntime.
print("phase2 base done")
