#pragma once
#include "CoreMinimal.h"
#include "BattleSimulation.h"
#include "SkillBalance.h"

/**
 * Active skill runtime — skills-grade1.csv (user patch 2026-10-27).
 * ATK/DEF: escalating hits 5/10/15/20
 * STA: own wall hits within a rolling window, 5 in 5s / 10 in 10s / 15 in 15s / 20 in 20s.
 * BAL: window_hit_bey_and_wall — bey AND wall each >=1 within N seconds 5/10/15/20
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
	DefensiveBurst = 3,   // DEF: Defense multiplier
	StaminaQuiet = 4,     // STA: quiet spin
	BalanceWindow = 5     // BAL: window hit
};

enum class ESkillCondition : uint8
{
	HitsDealt = 0,
	HitsTaken = 1,
	QuietSpinSec = 2,
	WindowHitSec = 3,
    WallHitsWindow = 4
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
	bool bWindowGotBey = false;
	bool bWindowGotWall = false;
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
	FString DisplayName = TEXT("疾突");
    FString BeyId;
    SkillBalance::FRow ActiveData, PassiveData;
    double BaseDefense=1., BaseMass=1., BaseDecay=0., PassiveRemain=0.;
    double PassiveQuiet=0., PassiveNoBey=0., PassiveCooldown=0.;
    int32 PassiveStacks=0, PassiveCharges=0, SeenDealt=0, SeenTaken=0;
    bool bPassiveDefense=false;
    double EffectClock=0., LastBeyAt=-1.e9, LastWallAt=-1.e9;
    TArray<double> WallHitTimes;


	void ConfigureForPoolSlot(int32 PoolSlot, EBeyType Type)
	{
		// Pool: 0 ChiFeng ATK, 1 BiLei DEF, 2 ChangXuan STA, 3 HengRen BAL, 4 ChiWen ATK
        const TCHAR* Ids[] = {TEXT("chifeng"),TEXT("bilei"),TEXT("changxuan"),TEXT("hengblade"),TEXT("chiwen"),TEXT("huangkai"),TEXT("cuipan"),TEXT("shuanghuan")};
        ConfigureForId(Ids[FMath::Clamp(PoolSlot,0,UE_ARRAY_COUNT(Ids)-1)]);
        (void)Type;
    }

    void ConfigureForId(const FString& Id)
    {
        BeyId=Id; ActiveData=SkillBalance::Get(Id,TEXT("active")); PassiveData=SkillBalance::Get(Id,TEXT("passive"));
        DisplayName=ActiveData.Name;
        FString Prefix, Sequence;
        TArray<FString> Steps;
        ActiveData.Condition.Split(TEXT(":"),&Prefix,&Sequence);
        Sequence.ParseIntoArray(Steps,TEXT("/"));
        if(Steps.Num()!=SeqLen) ActiveData.Valid=false;
        else for(int32 I=0;I<SeqLen;++I)
        {
            const int32 N=FCString::Atoi(*Steps[I]);
            if(!Steps[I].IsNumeric() || N<1 || N>120 || (I>0 && N<NeedSeq[I-1])) ActiveData.Valid=false;
            NeedSeq[I]=FMath::Clamp(N,1,120);
        }
        if (ActiveData.Condition.StartsWith(TEXT("hits_taken"))) {Condition=ESkillCondition::HitsTaken; Kind=EActiveSkillKind::DefensiveBurst;}
        else if (ActiveData.Condition.StartsWith(TEXT("quiet_spin"))) {Condition=ESkillCondition::QuietSpinSec; Kind=EActiveSkillKind::StaminaQuiet;}
        else if (ActiveData.Condition.StartsWith(TEXT("wall_hits_window"))) {Condition=ESkillCondition::WallHitsWindow; Kind=EActiveSkillKind::StaminaQuiet;}
        else if (ActiveData.Condition.StartsWith(TEXT("window_hit"))) {Condition=ESkillCondition::WindowHitSec; Kind=EActiveSkillKind::BalanceWindow;}
        else {Condition=ESkillCondition::HitsDealt; Kind=Id==TEXT("chiwen")?EActiveSkillKind::ChiwenNextExtra:EActiveSkillKind::ChifengBurst;}
    }

	void ResetForBout()
	{
		HitsDealt = HitsTaken = 0;
		Tier = 0;
		QuietSec = WindowSec = 0.0;
		bWindowGotBey = bWindowGotWall = false;
		bFxActive = false;
		FxRemainSec = 0.0;
		AttackMulActive = 1.0;
		RingoutRateAdd = 0.0;
		ExtraKickMulPending = 1.0;
		BaselineAttack = 1.0;
		bPendingRestore = false;
		LastSeenHits = 0;
        PassiveQuiet=PassiveNoBey=PassiveCooldown=0.;
        PassiveStacks=PassiveCharges=SeenDealt=SeenTaken=0; bPassiveDefense=false;
        PassiveRemain=EffectClock=0.; LastBeyAt=LastWallAt=-1.e9;
        WallHitTimes.Reset();
	}

	int32 Need() const { return NeedSeq[FMath::Clamp(Tier, 0, SeqLen - 1)]; }

	double ProgressValue() const
	{
		switch (Condition)
		{
		case ESkillCondition::HitsTaken: return static_cast<double>(HitsTaken);
		case ESkillCondition::QuietSpinSec: return QuietSec;
        case ESkillCondition::WallHitsWindow: return WallHitTimes.Num();
		case ESkillCondition::WindowHitSec: return WindowSec;
		default: return static_cast<double>(HitsDealt);
		}
	}

	ESkillButtonState State() const
	{
		if (!ActiveData.Valid) return ESkillButtonState::Progress;
        if (bFxActive) return ESkillButtonState::ActiveFx;
		switch (Condition)
		{
		case ESkillCondition::HitsTaken:
			if (HitsTaken >= Need()) return ESkillButtonState::Ready;
			break;
		case ESkillCondition::QuietSpinSec:
			if (QuietSec + 1.e-6 >= Need()) return ESkillButtonState::Ready;
			break;
        case ESkillCondition::WallHitsWindow:
            if(WallHitTimes.Num()>=Need()) return ESkillButtonState::Ready;
            break;
		case ESkillCondition::WindowHitSec:
			if (bWindowGotBey && bWindowGotWall && WindowSec <= Need() + 1.e-6) return ESkillButtonState::Ready;
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
        case ESkillCondition::WallHitsWindow:
            EffectClock+=Dt;
            WallHitTimes.RemoveAll([&](double At){return EffectClock-At>Need()+1.e-6;});
            if(bWall) WallHitTimes.Add(EffectClock);
            break;
		case ESkillCondition::HitsTaken:
			HitsTaken += Delta; // mutual collide counts as taken for shell
			break;
		case ESkillCondition::QuietSpinSec:
			if (bContact) QuietSec = 0.0;
			else QuietSec += Dt;
			break;
		case ESkillCondition::WindowHitSec:
            EffectClock+=Dt;
            if (Delta>0) LastBeyAt=EffectClock;
            if (bWall) LastWallAt=EffectClock;
            bWindowGotBey=EffectClock-LastBeyAt<=Need();
            bWindowGotWall=EffectClock-LastWallAt<=Need();
            WindowSec=(bWindowGotBey && bWindowGotWall)?EffectClock-FMath::Min(LastBeyAt,LastWallAt):0.;
			break;
		}
	}

	void TickFx(double Dt)
	{
		if (!bFxActive) return;
		if (ActiveData.Duration == 0.) return;
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
		if (ActiveData.Duration != 0.) return;
		bFxActive = false;
		ExtraKickMulPending = 1.0;
		FxRemainSec = 0.0;
	}

	bool TryFire()
	{
		if (!CanFire()) return false;
		HitsDealt = HitsTaken = 0;
		QuietSec = WindowSec = 0.0;
		bWindowGotBey = bWindowGotWall = false;
        EffectClock=0.; LastBeyAt=LastWallAt=-1.e9;
        WallHitTimes.Reset();
		Tier = FMath::Min(Tier + 1, SeqLen - 1);
		bFxActive = true;
		if (Kind == EActiveSkillKind::ChiwenNextExtra)
		{
			ExtraKickMulPending = ActiveData.Value;
			AttackMulActive = 1.0;
			RingoutRateAdd = 0.0;
			FxRemainSec = 0.0;
		}
		else if (Kind == EActiveSkillKind::ChifengBurst)
		{
			AttackMulActive = ActiveData.Value;
			RingoutRateAdd = ActiveData.SecondaryValue;
			ExtraKickMulPending = 1.0;
			FxRemainSec = ActiveData.Duration;
		}
		else
		{
			// Timed effects are applied from the data row against the captured bout baseline.
			AttackMulActive = 1.0;
			RingoutRateAdd = 0.0;
			ExtraKickMulPending = 1.0;
			FxRemainSec = ActiveData.Duration;
		}
		return true;
	}

	FString ProgressLabel() const
	{
		const int32 N = Need();
		switch (Condition)
		{
        case ESkillCondition::WallHitsWindow:
            return FString::Printf(TEXT("%d秒内撞墙 %d/%d"),N,FMath::Min(WallHitTimes.Num(),N),N);
		case ESkillCondition::QuietSpinSec:
			return FString::Printf(TEXT("%.0f/%ds"), FMath::Min(QuietSec, (double)N), N);
		case ESkillCondition::WindowHitSec:
			return FString::Printf(TEXT("螺%d墙%d %.0f/%ds"), bWindowGotBey ? 1 : 0, bWindowGotWall ? 1 : 0, WindowSec, N);
		case ESkillCondition::HitsTaken:
			return FString::Printf(TEXT("受击 %d/%d"), FMath::Min(HitsTaken,N), N);
		default:
			return FString::Printf(TEXT("碰撞 %d/%d"), FMath::Min(HitsDealt,N), N);
		}
	}

	const TCHAR* LabelZh() const { return *DisplayName; }

    void BeginEffects(FBattleSimulation& S,int32 I)
    {
        BaselineAttack=S.Attack[I]; BaseDefense=S.Defense[I]; BaseMass=S.Mass[I]; BaseDecay=S.SpinDecay[I];
        ApplyEffects(S,I);
    }
    void ApplyEffects(FBattleSimulation& S,int32 I)
    {
        S.Attack[I]=BaselineAttack; S.Defense[I]=BaseDefense; S.Mass[I]=BaseMass; S.SpinDecay[I]=BaseDecay;
        S.SkillWearMul[I]=S.SkillIncomingMul[I]=S.SkillMassScale[I]=S.SkillOutgoingMul[I]=1.;
        S.SkillReflect[I]=0.; S.PassiveOutgoingMul[I]=S.PassiveWearMul[I]=1.;
        auto Apply=[&](const SkillBalance::FRow& Row) {
            if (!Row.Valid) return;
            if (Row.Effect.EndsWith(TEXT("AllStatMul"))) {S.Attack[I]*=Row.Value; S.Defense[I]*=Row.Value; S.Mass[I]*=Row.Value; S.SkillMassScale[I]*=Row.Value;}
            else if (Row.Effect.EndsWith(TEXT("AttackMul"))) S.Attack[I]*=Row.Value;
            else if (Row.Effect.EndsWith(TEXT("DefenseMul"))) S.Defense[I]*=Row.Value;
            else if (Row.Effect.EndsWith(TEXT("EnemyDecayMul"))) S.SkillEnemyDecayMul[I]*=Row.Value;
            else if (Row.Effect.EndsWith(TEXT("DecayMul"))) S.SpinDecay[I]*=Row.Value;
            else if (Row.Effect.EndsWith(TEXT("MassMul"))) {S.Mass[I]*=Row.Value; S.SkillMassScale[I]*=Row.Value;}
            else if (Row.Effect.EndsWith(TEXT("CollisionWearMul"))) S.PassiveWearMul[I]*=Row.Value;
            else if (Row.Effect.EndsWith(TEXT("IncomingOnlyMul"))) S.SkillIncomingMul[I]*=Row.Value;
            else if (Row.Effect.EndsWith(TEXT("WearMul"))) S.SkillWearMul[I]*=Row.Value;
            else if (Row.Effect.EndsWith(TEXT("IncomingKickMul"))) {S.SkillIncomingMul[I]*=Row.Value; S.SkillWearMul[I]*=Row.Value;}
            if (Row.Secondary==TEXT("decay_mul")) S.SpinDecay[I]*=Row.SecondaryValue;
            if (Row.Secondary==TEXT("defense_mul")) S.Defense[I]*=Row.SecondaryValue;
            if (Row.Secondary==TEXT("reflect")) S.SkillReflect[I]=Row.SecondaryValue;
            // shortcut: ringout_add biases outgoing kick, not calibrated win probability; replace when 3D flight is modeled.
            if (Row.Secondary==TEXT("ringout_add")) S.SkillOutgoingMul[I]*=1.+Row.SecondaryValue;
        };
        S.SkillEnemyDecayMul[I]=1.;
        Apply(PassiveData);
        if(PassiveData.Valid)
        {
            if(BeyId==TEXT("chifeng") && PassiveNoBey>=3.) S.PassiveOutgoingMul[I]=1.20;
            else if(BeyId==TEXT("chiwen")) S.Attack[I]*=1.+.04*PassiveStacks;
            else if(BeyId==TEXT("bilei") && PassiveCharges==3) S.PassiveOutgoingMul[I]=1.20;
            else if(BeyId==TEXT("huangkai"))
            {
                if(S.Position[I].Size()>S.TrapInnerR*S.ArenaScale) S.Defense[I]*=1.12;
                if(PassiveRemain>0.) S.SkillIncomingMul[I]*=.85;
            }
            else if(BeyId==TEXT("changxuan") && PassiveQuiet>=3.) S.SpinDecay[I]*=.88;
            else if(BeyId==TEXT("cuipan") && PassiveRemain>0.) S.SkillIncomingMul[I]*=.85;
            else if(BeyId==TEXT("hengblade") && PassiveRemain>0.)
            {
                if(bPassiveDefense) S.Defense[I]*=1.10; else S.Attack[I]*=1.10;
            }
            else if(BeyId==TEXT("shuanghuan") && PassiveRemain>0.) S.SkillEnemyDecayMul[I]=1.10;
        }
        if (bFxActive) Apply(ActiveData);
    }
    void AfterStep(FBattleSimulation& S,int32 I,double Dt)
    {
        const bool Hit=S.Hits>LastSeenHits;
        const bool Dealt=S.PassiveDealt[I]>SeenDealt, Taken=S.PassiveTaken[I]>SeenTaken;
        SeenDealt=S.PassiveDealt[I]; SeenTaken=S.PassiveTaken[I];
        PassiveRemain=FMath::Max(0.,PassiveRemain-Dt);
        PassiveCooldown=FMath::Max(0.,PassiveCooldown-Dt);
        PassiveQuiet=(Hit || S.bWallContact[I])?0.:PassiveQuiet+Dt;
        PassiveNoBey=Hit?0.:PassiveNoBey+Dt;
        if(PassiveRemain==0.) PassiveStacks=0;
        if(BeyId==TEXT("chiwen") && Dealt) {PassiveStacks=FMath::Min(3,PassiveStacks+1);PassiveRemain=2.5;}
        if(BeyId==TEXT("bilei"))
        {
            const bool Armed=PassiveCharges==3;
            if(Armed && Dealt) PassiveCharges=0;
            else if(!Armed && Taken) ++PassiveCharges;
        }
        if(BeyId==TEXT("huangkai") && Taken && PassiveCooldown==0. && S.Position[I].Size()>S.TrapInnerR*S.ArenaScale)
            {PassiveRemain=1.5;PassiveCooldown=6.;}
        if(BeyId==TEXT("cuipan") && Taken) PassiveRemain=2.;
        if(BeyId==TEXT("hengblade") && (Dealt || Taken)) {bPassiveDefense=Dealt;PassiveRemain=2.;}
        if(BeyId==TEXT("shuanghuan") && Dealt && PassiveCooldown==0.) {PassiveRemain=3.;PassiveCooldown=5.;}
        const bool Consumed=bFxActive && ActiveData.Duration==0. && Hit;
        TickFx(Dt);
        if (Consumed) NotifyExtraConsumed();
        Observe(Dt,S.Hits,S.bWallContact[I]);
        ApplyEffects(S,I);
        bPendingRestore=false;
    }
};
