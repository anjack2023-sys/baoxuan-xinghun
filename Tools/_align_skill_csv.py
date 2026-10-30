# -*- coding: utf-8 -*-
"""Align BALANCE 0.130 + Chiwen ExtraKick skill shell; append tests."""
from pathlib import Path

root = Path(r"C:\BeybladeUE\Source\BeybladePrototype")

# --- Grade1Balance embed 0.130 ---
g1 = (root / "Grade1Balance.h").read_text(encoding="utf-8")
g1 = g1.replace("{1.10, 1.10, 1.05, 0.135}, // Balance", "{1.10, 1.10, 1.05, 0.130}, // Balance")
g1 = g1.replace("MutableRow(EBeyType::Balance) = {1.10, 1.10, 1.05, 0.135};", "MutableRow(EBeyType::Balance) = {1.10, 1.10, 1.05, 0.130};")
(root / "Grade1Balance.h").write_text(g1, encoding="utf-8")
print("Grade1Balance 0.130", "0.130" in (root/"Grade1Balance.h").read_text(encoding="utf-8"))

# --- BattleSimulation: PendingExtraKickMul consume on Collide (no SPIN_KICK change) ---
bs = (root / "BattleSimulation.h").read_text(encoding="utf-8")
if "PendingExtraKickMul" not in bs:
    bs = bs.replace(
        "\tESimScoreTag ScoreTag = ESimScoreTag::None;",
        "\tESimScoreTag ScoreTag = ESimScoreTag::None;\n\t// Skill shell data-layer: next-hit Extra mul (Chiwen). Does not change SPIN_KICK constant.\n\tdouble PendingExtraKickMul[2] = {1.0, 1.0};",
    )
    bs = bs.replace(
        "\t\tDashHits.Reset();\n\t\tScoreTag = ESimScoreTag::None;",
        "\t\tDashHits.Reset();\n\t\tScoreTag = ESimScoreTag::None;\n\t\tPendingExtraKickMul[0] = PendingExtraKickMul[1] = 1.0;",
    )
    # Multiply ExtraOnto by pending mul and consume
    old = "\t\tconst double ExtraOnto1 = ExtraKickBase * Attack[0] * DefScaleOn1;\n\t\tconst double ExtraOnto0 = ExtraKickBase * Attack[1] * DefScaleOn0;"
    new = (
        "\t\tconst double ExtraOnto1 = ExtraKickBase * Attack[0] * DefScaleOn1 * PendingExtraKickMul[0];\n"
        "\t\tconst double ExtraOnto0 = ExtraKickBase * Attack[1] * DefScaleOn0 * PendingExtraKickMul[1];\n"
        "\t\tPendingExtraKickMul[0] = PendingExtraKickMul[1] = 1.0;"
    )
    if old not in bs:
        raise SystemExit("Collide ExtraOnto block missing")
    bs = bs.replace(old, new)
    (root / "BattleSimulation.h").write_text(bs, encoding="utf-8")
    print("PendingExtraKickMul wired")
else:
    print("PendingExtraKickMul already present")

# --- Rewrite SkillRuntime for Chifeng vs Chiwen modes ---
(root / "SkillRuntime.h").write_text(r'''#pragma once
#include "CoreMinimal.h"
#include "BattleSimulation.h"

/**
 * Active skill HUD shell (Grade1 v2 / skills-grade1.csv).
 * Condition progress / gray / ready. No time-gate 0-3s / CD8s.
 * Feel / SPIN_KICK / RESTITUTION untouched.
 */
enum class ESkillButtonState : uint8
{
	Progress = 0,
	Ready = 1,
	ActiveFx = 2
};

enum class EActiveSkillKind : uint8
{
	None = 0,
	ChifengBurst = 1, // Attack*1.20 for 3s + RingoutRateAdd 0.10
	ChiwenNextExtra = 2 // next valid hit ExtraKickMul 1.35
};

struct FActiveSkillShell
{
	static constexpr int32 SeqLen = 4;
	int32 NeedSeq[SeqLen] = {5, 10, 15, 20};
	int32 HitsDealt = 0;
	int32 Tier = 0;
	bool bFxActive = false;
	double FxRemainSec = 0.0;
	double AttackMulActive = 1.0;
	double RingoutRateAdd = 0.0;
	double ExtraKickMulPending = 1.0;
	double BaselineAttack = 1.0;
	bool bPendingRestore = false;
	int32 LastSeenHits = 0;
	EActiveSkillKind Kind = EActiveSkillKind::ChifengBurst;
	const TCHAR* DisplayName = TEXT("疾突");

	static constexpr double ChifengAttackMul = 1.20;
	static constexpr double ChifengRingoutAdd = 0.10;
	static constexpr double ChifengDurationSec = 3.0;
	static constexpr double ChiwenExtraMul = 1.35;

	void ConfigureForPoolSlot(int32 PoolSlot, EBeyType Type)
	{
		// Pool: 0 ChiFeng ATK, 4 ChiWen ATK (MatchFlow). Others keep Chifeng-like shell label for demo.
		if (PoolSlot == 4 || (Type == EBeyType::Attack && PoolSlot == 4))
		{
			Kind = EActiveSkillKind::ChiwenNextExtra;
			DisplayName = TEXT("炽焰斩");
		}
		else
		{
			Kind = EActiveSkillKind::ChifengBurst;
			DisplayName = TEXT("赤芒一闪");
		}
	}

	void ResetForBout()
	{
		HitsDealt = 0;
		Tier = 0;
		bFxActive = false;
		FxRemainSec = 0.0;
		AttackMulActive = 1.0;
		RingoutRateAdd = 0.0;
		ExtraKickMulPending = 1.0;
		BaselineAttack = 1.0;
		bPendingRestore = false;
		LastSeenHits = 0;
	}

	int32 Need() const { return NeedSeq[FMath::Clamp(Tier, 0, SeqLen - 1)]; }

	ESkillButtonState State() const
	{
		if (bFxActive) return ESkillButtonState::ActiveFx;
		if (HitsDealt >= Need()) return ESkillButtonState::Ready;
		return ESkillButtonState::Progress;
	}

	bool CanFire() const { return State() == ESkillButtonState::Ready; }

	void ObserveHits(int32 SimHits)
	{
		if (SimHits > LastSeenHits)
		{
			const int32 Delta = SimHits - LastSeenHits;
			if (!bFxActive) HitsDealt += Delta;
		}
		LastSeenHits = SimHits;
	}

	void TickFx(double Dt)
	{
		if (!bFxActive) return;
		if (Kind == EActiveSkillKind::ChiwenNextExtra)
		{
			// Chiwen: FX ends when next hit consumes PendingExtraKickMul (driven by battle mode).
			return;
		}
		FxRemainSec -= Dt;
		if (FxRemainSec <= 0.0)
		{
			bFxActive = false;
			FxRemainSec = 0.0;
			AttackMulActive = 1.0;
			RingoutRateAdd = 0.0;
			bPendingRestore = true;
		}
	}

	void NotifyExtraConsumed()
	{
		if (Kind != EActiveSkillKind::ChiwenNextExtra) return;
		bFxActive = false;
		ExtraKickMulPending = 1.0;
		FxRemainSec = 0.0;
	}

	bool TryFire()
	{
		if (!CanFire()) return false;
		HitsDealt = 0;
		Tier = FMath::Min(Tier + 1, SeqLen - 1);
		bFxActive = true;
		if (Kind == EActiveSkillKind::ChiwenNextExtra)
		{
			ExtraKickMulPending = ChiwenExtraMul;
			AttackMulActive = 1.0;
			RingoutRateAdd = 0.0;
			FxRemainSec = 0.0; // waiting for next hit
		}
		else
		{
			AttackMulActive = ChifengAttackMul;
			RingoutRateAdd = ChifengRingoutAdd;
			ExtraKickMulPending = 1.0;
			FxRemainSec = ChifengDurationSec;
		}
		return true;
	}

	const TCHAR* LabelZh() const { return DisplayName; }
};
''', encoding="utf-8")
print("SkillRuntime rewritten")

# --- Wire FireActiveSkill for Chiwen PendingExtraKickMul ---
cpp_path = root / "PrototypeBattle.cpp"
cpp = cpp_path.read_text(encoding="utf-8")

# Configure skill on StartBattleInternal based on P1 slot
old_start = '''void APrototypeBattleMode::StartBattleInternal()
{
    ApplyCurrentLoadouts();
    SkillShell.ResetForBout();
    Simulation.Reset();
    Simulation.Launch(); ++Match; Accumulator = 0;'''
new_start = '''void APrototypeBattleMode::StartBattleInternal()
{
    ApplyCurrentLoadouts();
    SkillShell.ResetForBout();
    {
        const int32 P1Slot = MatchFlow.bBlindPhase && MatchFlow.BlindChoiceP1 >= 0 ? MatchFlow.BlindChoiceP1
            : (MatchFlow.Pick.Count > MatchFlow.CurrentLineupIndex ? MatchFlow.Pick.Lineup[MatchFlow.CurrentLineupIndex] : 0);
        const EBeyType P1Type = MatchFlow.Pick.Pool[FMath::Clamp(P1Slot, 0, FPickRegular::PoolSize - 1)].Type;
        SkillShell.ConfigureForPoolSlot(P1Slot, P1Type);
    }
    Simulation.Reset();
    Simulation.Launch(); ++Match; Accumulator = 0;'''
if old_start in cpp:
    cpp = cpp.replace(old_start, new_start, 1)
    print("StartBattleInternal configure ok")
else:
    print("WARN StartBattleInternal block missing")

# Replace FireActiveSkill body
import re
m = re.search(r'void APrototypeBattleMode::FireActiveSkill\(\)\s*\{.*?\n\}\n', cpp, flags=re.S)
if not m:
    raise SystemExit("FireActiveSkill missing")
new_fire = '''void APrototypeBattleMode::FireActiveSkill()
{
    if (MatchFlow.State != EMatchFlowState::Fighting) return;
    SkillShell.BaselineAttack = Simulation.Attack[0];
    if (!SkillShell.TryFire())
    {
        UE_LOG(LogTemp, Display, TEXT("SKILL_FIRE_BLOCKED hits=%d need=%d"), SkillShell.HitsDealt, SkillShell.Need());
        return;
    }
    if (SkillShell.Kind == EActiveSkillKind::ChiwenNextExtra)
    {
        Simulation.PendingExtraKickMul[0] = SkillShell.ExtraKickMulPending;
        UE_LOG(LogTemp, Display, TEXT("SKILL_FIRE chiwen next_extra=%.2f tier=%d next_need=%d"), SkillShell.ExtraKickMulPending, SkillShell.Tier, SkillShell.Need());
    }
    else
    {
        // Chifeng: temporary Attack mul + ringout add (data layer). Does NOT touch SPIN_KICK / RESTITUTION.
        Simulation.Attack[0] = SkillShell.BaselineAttack * SkillShell.AttackMulActive;
        UE_LOG(LogTemp, Display, TEXT("SKILL_FIRE chifeng atk_mul=%.2f ringout_add=%.2f tier=%d next_need=%d"), SkillShell.AttackMulActive, SkillShell.RingoutRateAdd, SkillShell.Tier, SkillShell.Need());
    }
}
'''
cpp = cpp[:m.start()] + new_fire + cpp[m.end():]

# Tick: detect Chiwen extra consume (PendingExtraKickMul reset to 1 after collide)
old_tick = '''    if (MatchFlow.State == EMatchFlowState::Fighting && AutoMatches <= 0)
    {
        SkillShell.ObserveHits(Simulation.Hits);
        SkillShell.TickFx(DeltaSeconds);
        if (SkillShell.bPendingRestore)
        {
            Simulation.Attack[0] = SkillShell.BaselineAttack;
            SkillShell.bPendingRestore = false;
            UE_LOG(LogTemp, Display, TEXT("SKILL_FX_END restore_atk=%.3f"), Simulation.Attack[0]);
        }
    }
'''
new_tick = '''    if (MatchFlow.State == EMatchFlowState::Fighting && AutoMatches <= 0)
    {
        const int32 HitsBefore = SkillShell.LastSeenHits;
        SkillShell.ObserveHits(Simulation.Hits);
        if (SkillShell.Kind == EActiveSkillKind::ChiwenNextExtra && SkillShell.bFxActive
            && SkillShell.LastSeenHits > HitsBefore
            && Simulation.PendingExtraKickMul[0] <= 1.0 + 1.e-9)
        {
            SkillShell.NotifyExtraConsumed();
            UE_LOG(LogTemp, Display, TEXT("SKILL_FX_END chiwen_extra_consumed"));
        }
        SkillShell.TickFx(DeltaSeconds);
        if (SkillShell.bPendingRestore)
        {
            Simulation.Attack[0] = SkillShell.BaselineAttack;
            SkillShell.bPendingRestore = false;
            UE_LOG(LogTemp, Display, TEXT("SKILL_FX_END restore_atk=%.3f"), Simulation.Attack[0]);
        }
    }
'''
if old_tick in cpp:
    cpp = cpp.replace(old_tick, new_tick)
    print("Tick chiwen consume ok")
else:
    print("WARN tick block not exact; trying fuzzy")
    if "SkillShell.ObserveHits" in cpp and "NotifyExtraConsumed" not in cpp:
        cpp = cpp.replace(
            "SkillShell.ObserveHits(Simulation.Hits);",
            '''const int32 HitsBefore = SkillShell.LastSeenHits;
        SkillShell.ObserveHits(Simulation.Hits);
        if (SkillShell.Kind == EActiveSkillKind::ChiwenNextExtra && SkillShell.bFxActive
            && SkillShell.LastSeenHits > HitsBefore
            && Simulation.PendingExtraKickMul[0] <= 1.0 + 1.e-9)
        {
            SkillShell.NotifyExtraConsumed();
            UE_LOG(LogTemp, Display, TEXT("SKILL_FX_END chiwen_extra_consumed"));
        }''',
            1,
        )

cpp_path.write_text(cpp, encoding="utf-8")
print("PrototypeBattle skill wiring done")
