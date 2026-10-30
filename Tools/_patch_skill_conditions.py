# -*- coding: utf-8 -*-
"""Patch skill shell for quiet_spin / window_hit / hits; wall bump flag; HUD progress; tests."""
from pathlib import Path
root = Path(r"C:\BeybladeUE\Source\BeybladePrototype")

# --- BattleSimulation: wall bump flag (no Feel constant change) ---
bs = (root / "BattleSimulation.h").read_text(encoding="utf-8")
if "bWallBumpThisFrame" not in bs:
    bs = bs.replace(
        "\tdouble PendingExtraKickMul[2] = {1.0, 1.0};",
        "\tdouble PendingExtraKickMul[2] = {1.0, 1.0};\n\tbool bWallBumpThisFrame = false; // rim correction contact (skill shell)",
    )
    bs = bs.replace(
        "\t\tPendingExtraKickMul[0] = PendingExtraKickMul[1] = 1.0;\n\t\t// Keep Attack",
        "\t\tPendingExtraKickMul[0] = PendingExtraKickMul[1] = 1.0;\n\t\tbWallBumpThisFrame = false;\n\t\t// Keep Attack",
    )
    # In Tick start clear, on rim correction set true
    if "bWallBumpThisFrame = false;" not in bs.split("void Tick()")[1][:400]:
        bs = bs.replace(
            "\tvoid Tick()\n\t{\n\t\tif (!Running) return;\n\t\t++Frames;",
            "\tvoid Tick()\n\t{\n\t\tif (!Running) return;\n\t\tbWallBumpThisFrame = false;\n\t\t++Frames;",
        )
    bs = bs.replace(
        "\t\t\t\tif (Outward < 2.25)\n\t\t\t\t{\n\t\t\t\t\tVelocity[I] -= Radial * (Outward * 1.2 + 3.0 * Step);\n\t\t\t\t\tNext = P + Velocity[I] * Step;\n\t\t\t\t}",
        "\t\t\t\tif (Outward < 2.25)\n\t\t\t\t{\n\t\t\t\t\tVelocity[I] -= Radial * (Outward * 1.2 + 3.0 * Step);\n\t\t\t\t\tNext = P + Velocity[I] * Step;\n\t\t\t\t\tbWallBumpThisFrame = true;\n\t\t\t\t}",
    )
    (root / "BattleSimulation.h").write_text(bs, encoding="utf-8")
    print("wall bump flag ok")
else:
    print("wall bump already")

# --- SkillRuntime full rewrite ---
(root / "SkillRuntime.h").write_text(r'''#pragma once
#include "CoreMinimal.h"
#include "BattleSimulation.h"

/**
 * Active skill HUD shell — skills-grade1.csv (user patch 2026-10-27).
 * ATK/DEF: escalating hits 5/10/15/20
 * STA: quiet_spin seconds 5/10/15/20 (no bey/wall/obstacle contact)
 * BAL: window_hit — land bey-or-wall hit within N seconds 5/10/15/20
 * No time-gate CD 0-3s/8s. Feel / SPIN_KICK / RESTITUTION untouched.
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
	ChifengBurst = 1,     // ATK: Attack*1.20 + RingoutRateAdd
	ChiwenNextExtra = 2,  // ATK: next ExtraKickMul 1.35
	DefensiveBurst = 3,   // DEF: Defense mul stub
	StaminaQuiet = 4,     // STA: quiet spin
	BalanceWindow = 5     // BAL: window hit
};

enum class ESkillCondition : uint8
{
	HitsDealt = 0,
	HitsTaken = 1,
	QuietSpinSec = 2,
	WindowHitSec = 3
};

struct FActiveSkillShell
{
	static constexpr int32 SeqLen = 4;
	int32 NeedSeq[SeqLen] = {5, 10, 15, 20};
	int32 Tier = 0;
	int32 HitsDealt = 0;
	int32 HitsTaken = 0;
	double QuietSec = 0.0;
	double WindowSec = 0.0;
	bool bWindowGotHit = false;
	bool bFxActive = false;
	double FxRemainSec = 0.0;
	double AttackMulActive = 1.0;
	double RingoutRateAdd = 0.0;
	double ExtraKickMulPending = 1.0;
	double BaselineAttack = 1.0;
	bool bPendingRestore = false;
	int32 LastSeenHits = 0;
	EActiveSkillKind Kind = EActiveSkillKind::ChifengBurst;
	ESkillCondition Condition = ESkillCondition::HitsDealt;
	const TCHAR* DisplayName = TEXT("疾突");

	static constexpr double ChifengAttackMul = 1.20;
	static constexpr double ChifengRingoutAdd = 0.10;
	static constexpr double ChifengDurationSec = 3.0;
	static constexpr double ChiwenExtraMul = 1.35;

	void ConfigureForPoolSlot(int32 PoolSlot, EBeyType Type)
	{
		// Pool: 0 ChiFeng ATK, 1 BiLei DEF, 2 ChangXuan STA, 3 HengRen BAL, 4 ChiWen ATK
		switch (PoolSlot)
		{
		case 1:
			Kind = EActiveSkillKind::DefensiveBurst;
			Condition = ESkillCondition::HitsTaken;
			DisplayName = TEXT("铁壁");
			break;
		case 2:
			Kind = EActiveSkillKind::StaminaQuiet;
			Condition = ESkillCondition::QuietSpinSec;
			DisplayName = TEXT("长旋静转");
			break;
		case 3:
			Kind = EActiveSkillKind::BalanceWindow;
			Condition = ESkillCondition::WindowHitSec;
			DisplayName = TEXT("衡势");
			break;
		case 4:
			Kind = EActiveSkillKind::ChiwenNextExtra;
			Condition = ESkillCondition::HitsDealt;
			DisplayName = TEXT("炽焰斩");
			break;
		default:
			Kind = EActiveSkillKind::ChifengBurst;
			Condition = ESkillCondition::HitsDealt;
			DisplayName = TEXT("赤芒一闪");
			break;
		}
		(void)Type;
	}

	void ResetForBout()
	{
		HitsDealt = HitsTaken = 0;
		Tier = 0;
		QuietSec = WindowSec = 0.0;
		bWindowGotHit = false;
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

	double ProgressValue() const
	{
		switch (Condition)
		{
		case ESkillCondition::HitsTaken: return static_cast<double>(HitsTaken);
		case ESkillCondition::QuietSpinSec: return QuietSec;
		case ESkillCondition::WindowHitSec: return WindowSec;
		default: return static_cast<double>(HitsDealt);
		}
	}

	ESkillButtonState State() const
	{
		if (bFxActive) return ESkillButtonState::ActiveFx;
		switch (Condition)
		{
		case ESkillCondition::HitsTaken:
			if (HitsTaken >= Need()) return ESkillButtonState::Ready;
			break;
		case ESkillCondition::QuietSpinSec:
			if (QuietSec + 1.e-6 >= Need()) return ESkillButtonState::Ready;
			break;
		case ESkillCondition::WindowHitSec:
			if (bWindowGotHit && WindowSec <= Need() + 1.e-6) return ESkillButtonState::Ready;
			break;
		default:
			if (HitsDealt >= Need()) return ESkillButtonState::Ready;
			break;
		}
		return ESkillButtonState::Progress;
	}

	bool CanFire() const { return State() == ESkillButtonState::Ready; }

	/** Dt seconds; HitDelta new bey-bey contacts; bWall rim bump this frame. */
	void Observe(double Dt, int32 SimHits, bool bWall)
	{
		const int32 Delta = FMath::Max(0, SimHits - LastSeenHits);
		LastSeenHits = SimHits;
		const bool bContact = (Delta > 0) || bWall;

		if (bFxActive && Kind != EActiveSkillKind::ChiwenNextExtra)
		{
			// During timed FX, still track LastSeenHits only.
			return;
		}
		if (bFxActive && Kind == EActiveSkillKind::ChiwenNextExtra)
		{
			return; // consume handled by battle mode
		}

		switch (Condition)
		{
		case ESkillCondition::HitsDealt:
			HitsDealt += Delta;
			break;
		case ESkillCondition::HitsTaken:
			HitsTaken += Delta; // mutual collide counts as taken for shell
			break;
		case ESkillCondition::QuietSpinSec:
			if (bContact) QuietSec = 0.0;
			else QuietSec += Dt;
			break;
		case ESkillCondition::WindowHitSec:
			WindowSec += Dt;
			if (bContact) bWindowGotHit = true;
			if (!bWindowGotHit && WindowSec > Need())
			{
				// Missed window — restart
				WindowSec = 0.0;
				bWindowGotHit = false;
			}
			break;
		}
	}

	void TickFx(double Dt)
	{
		if (!bFxActive) return;
		if (Kind == EActiveSkillKind::ChiwenNextExtra) return;
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
		HitsDealt = HitsTaken = 0;
		QuietSec = WindowSec = 0.0;
		bWindowGotHit = false;
		Tier = FMath::Min(Tier + 1, SeqLen - 1);
		bFxActive = true;
		if (Kind == EActiveSkillKind::ChiwenNextExtra)
		{
			ExtraKickMulPending = ChiwenExtraMul;
			AttackMulActive = 1.0;
			RingoutRateAdd = 0.0;
			FxRemainSec = 0.0;
		}
		else if (Kind == EActiveSkillKind::ChifengBurst)
		{
			AttackMulActive = ChifengAttackMul;
			RingoutRateAdd = ChifengRingoutAdd;
			ExtraKickMulPending = 1.0;
			FxRemainSec = ChifengDurationSec;
		}
		else
		{
			// DEF/STA/BAL effect stubs — data layer placeholders; Feel untouched.
			AttackMulActive = 1.0;
			RingoutRateAdd = 0.0;
			ExtraKickMulPending = 1.0;
			FxRemainSec = 3.0;
		}
		return true;
	}

	FString ProgressLabel() const
	{
		const int32 N = Need();
		switch (Condition)
		{
		case ESkillCondition::QuietSpinSec:
			return FString::Printf(TEXT("%.0f/%ds"), FMath::Min(QuietSec, (double)N), N);
		case ESkillCondition::WindowHitSec:
			if (bWindowGotHit) return FString::Printf(TEXT("已撞 %.0f/%ds"), WindowSec, N);
			return FString::Printf(TEXT("需撞 %.0f/%ds"), WindowSec, N);
		case ESkillCondition::HitsTaken:
			return FString::Printf(TEXT("%d/%d"), HitsTaken, N);
		default:
			return FString::Printf(TEXT("%d/%d"), HitsDealt, N);
		}
	}

	const TCHAR* LabelZh() const { return DisplayName; }
};
''', encoding="utf-8")
print("SkillRuntime rewritten with STA/BAL conditions")

# --- PrototypeBattle Tick: use Observe(Dt, Hits, Wall) ---
cpp = (root / "PrototypeBattle.cpp").read_text(encoding="utf-8")
old = '''    if (MatchFlow.State == EMatchFlowState::Fighting && AutoMatches <= 0)
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
new = '''    if (MatchFlow.State == EMatchFlowState::Fighting && AutoMatches <= 0)
    {
        const int32 HitsBefore = SkillShell.LastSeenHits;
        SkillShell.Observe(DeltaSeconds, Simulation.Hits, Simulation.bWallBumpThisFrame);
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
if old in cpp:
    cpp = cpp.replace(old, new)
    print("Tick Observe wired")
elif "SkillShell.ObserveHits" in cpp:
    cpp = cpp.replace("SkillShell.ObserveHits(Simulation.Hits);",
                      "SkillShell.Observe(DeltaSeconds, Simulation.Hits, Simulation.bWallBumpThisFrame);")
    print("Tick ObserveHits replaced")
else:
    print("WARN tick observe not found")
(root / "PrototypeBattle.cpp").write_text(cpp, encoding="utf-8")

# --- ArtHUD: use ProgressLabel ---
hud = (root / "ArtHUD.cpp").read_text(encoding="utf-8")
hud2 = hud.replace(
    'Text(FString::Printf(TEXT("%d/%d"), Sk.HitsDealt, Sk.Need()), SP + FVector2D(60, 70), 22, Ready ? Gold : Cream, true);',
    'Text(Sk.ProgressLabel(), SP + FVector2D(60, 70), 20, Ready ? Gold : Cream, true);',
)
if hud2 == hud:
    # maybe already or different formatting
    import re
    hud2 = re.sub(
        r'Text\(FString::Printf\(TEXT\("%d/%d"\), Sk\.HitsDealt, Sk\.Need\(\)\), SP \+ FVector2D\(60, 70\), 22, Ready \? Gold : Cream, true\);',
        'Text(Sk.ProgressLabel(), SP + FVector2D(60, 70), 20, Ready ? Gold : Cream, true);',
        hud,
    )
(root / "ArtHUD.cpp").write_text(hud2, encoding="utf-8")
print("HUD ProgressLabel", "ProgressLabel" in (root/"ArtHUD.cpp").read_text(encoding="utf-8"))

# --- Update ActiveSkillShellTest ---
tpath = root / "BattleSimulationTest.cpp"
t = tpath.read_text(encoding="utf-8")
import re
m = re.search(r'IMPLEMENT_SIMPLE_AUTOMATION_TEST\(FActiveSkillShellTest[\s\S]*?^}\n', t, flags=re.M)
new_test = r'''IMPLEMENT_SIMPLE_AUTOMATION_TEST(FActiveSkillShellTest, "Beyblade.Match.ActiveSkillShell", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FActiveSkillShellTest::RunTest(const FString&)
{
	// ATK Chifeng: hits 5/10
	FActiveSkillShell Sk;
	Sk.ConfigureForPoolSlot(0, EBeyType::Attack);
	TestEqual(TEXT("chifeng hits cond"), (int32)Sk.Condition, (int32)ESkillCondition::HitsDealt);
	Sk.Observe(0.0, 5, false);
	TestEqual(TEXT("ready at 5 hits"), (int32)Sk.State(), (int32)ESkillButtonState::Ready);
	TestTrue(TEXT("fire chifeng"), Sk.TryFire());
	TestEqual(TEXT("next need 10"), Sk.Need(), 10);
	TestTrue(TEXT("atk mul"), FMath::IsNearlyEqual(Sk.AttackMulActive, 1.20));

	// Chiwen next Extra
	FActiveSkillShell Cw;
	Cw.ConfigureForPoolSlot(4, EBeyType::Attack);
	Cw.Observe(0.0, 5, false);
	TestTrue(TEXT("chiwen fire"), Cw.TryFire());
	TestTrue(TEXT("extra 1.35"), FMath::IsNearlyEqual(Cw.ExtraKickMulPending, 1.35));

	// STA quiet spin 5s without contact
	FActiveSkillShell Sta;
	Sta.ConfigureForPoolSlot(2, EBeyType::Stamina);
	TestEqual(TEXT("sta quiet cond"), (int32)Sta.Condition, (int32)ESkillCondition::QuietSpinSec);
	Sta.Observe(2.0, 0, false);
	TestEqual(TEXT("sta not ready 2s"), (int32)Sta.State(), (int32)ESkillButtonState::Progress);
	Sta.Observe(0.0, 1, false); // contact resets
	TestTrue(TEXT("quiet reset"), Sta.QuietSec < 0.01);
	Sta.Observe(5.0, 1, false); // same hit count, no new contact, +5s quiet
	TestEqual(TEXT("sta ready 5s"), (int32)Sta.State(), (int32)ESkillButtonState::Ready);
	TestTrue(TEXT("sta fire"), Sta.TryFire());
	TestEqual(TEXT("sta next need 10s"), Sta.Need(), 10);

	// BAL window hit within N seconds
	FActiveSkillShell Bal;
	Bal.ConfigureForPoolSlot(3, EBeyType::Balance);
	TestEqual(TEXT("bal window cond"), (int32)Bal.Condition, (int32)ESkillCondition::WindowHitSec);
	Bal.Observe(1.0, 0, false);
	TestFalse(TEXT("bal no hit yet"), Bal.CanFire());
	Bal.Observe(0.0, 1, true); // wall or bey hit inside window
	TestEqual(TEXT("bal ready after hit"), (int32)Bal.State(), (int32)ESkillButtonState::Ready);
	TestTrue(TEXT("bal fire"), Bal.TryFire());
	TestEqual(TEXT("bal next need 10s"), Bal.Need(), 10);

	// DEF hits taken
	FActiveSkillShell Def;
	Def.ConfigureForPoolSlot(1, EBeyType::Defense);
	Def.Observe(0.0, 5, false);
	TestEqual(TEXT("def ready"), (int32)Def.State(), (int32)ESkillButtonState::Ready);
	return true;
}
'''
if m:
    t = t[:m.start()] + new_test + t[m.end():]
    print("ActiveSkillShellTest replaced")
else:
    print("WARN test block not found")
tpath.write_text(t, encoding="utf-8")
print("done patches")
