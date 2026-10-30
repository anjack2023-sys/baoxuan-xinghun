#pragma once
#include "MobilityProfile.h"
#include "CoreMinimal.h"
#include "StarCrownRim.h"

// Coordinates and velocities are metres; only the scene adapter converts to UE centimetres.
// Planar proxy collision (not a full gyroscope solver).
// End rules priority: ringout > burst > trap > spinout > timeout (momentum).
// M2 finish fields (U1–U6 locked) gated by bEnableBurstTrapXtr; Feel85 kick constants FROZEN.

enum class EBeyType : uint8
{
	Attack = 0,
	Defense = 1,
	Stamina = 2,
    Balance = 3
};

enum class EBeyGrade : uint8
{
	Grade1 = 1,
	Grade2 = 2,
	Grade3 = 3
};

// Minimal data table: Grade1 x Attack/Defense/Stamina. Grade2/3 are stubs (slower decay only).
struct FBeyLoadout
{
	EBeyType Type = EBeyType::Attack;
	EBeyGrade Grade = EBeyGrade::Grade1;
	double Attack = 1.0;
	double Defense = 1.0;
	double Mass = 1.0;
	// Exponential spin decay rate k (1/s): Spin *= Exp(-k * dt). Target SpinStop at ~t seconds.
	double SpinDecayPerSec = 0.0;

	const TCHAR* TypeLabel() const
	{
		switch (Type)
		{
		case EBeyType::Defense: return TEXT("DEFENSE");
		case EBeyType::Stamina: return TEXT("STAMINA");
        case EBeyType::Balance: return TEXT("BALANCE");
		default: return TEXT("ATTACK");
		}
	}
};

// Grade1 Attack/Defense/Mass/k: read from balance table (Grade1Balance); no magic numbers here.
#include "Grade1Balance.h"
inline FBeyLoadout MakeLoadout(EBeyType Type, EBeyGrade Grade = EBeyGrade::Grade1)
{
	return Grade1Balance::MakeLoadout(Type, Grade);
}

struct FDashHitEvent
{
	int32 Attacker = -1;
	int32 Victim = -1;
	double TimeSec = 0;
	bool bValid = false;
};

enum class ESimScoreTag : uint8
{
	None = 0,
	OVR = 1,
	XTR = 2
};

struct FBattleSimulation
{
	static constexpr double Step = 1.0 / 60.0;
	static constexpr int32 MaxFrames = 60 * 60; // FROZEN 60s hard wall
	static constexpr double TimeLimitSeconds = MaxFrames * Step;
	static constexpr double SPIN_KICK = 1.45;        // FeelRef60: provisional playtest values.
	static constexpr double RESTITUTION = 0.78;
	static constexpr int32 ContactFeelTrial = 86;
	static constexpr double TangentialKick = 0.65;
	static constexpr double ScrapeRetention = 0.90;
	static constexpr double KickReferenceSpeed = 4.550; // FROZEN
	// M2 finish fields retained while Feel86 is ported from the approved trial.
	static constexpr double DurabilityMax = 100.0;     // U1
	static constexpr double BalanceWearBase = 1.6;
	static constexpr double WearBase = 12.0;           // U2
	static constexpr double TrapInnerR = 1.70;         // U3
	static constexpr double TrapOuterR = 1.95;         // U3
	static constexpr double TrapDwellSeconds = 1.2;    // U4
	static constexpr double TrapSpinExtra = 0.08;      // U5 /s
	static constexpr double XtrWindowSeconds = 2.5;    // U6
	static constexpr double Radius = 0.22; // Match the approved 44 cm visible meshes.
	static constexpr double SpinStart = 1.0;
	static constexpr double SpinStopThreshold = 0.02;

	FVector2D Position[2], Velocity[2];
	FRandomStream Random;
	int32 Frames = 0, Hits = 0, FirstHitFrame = -1;
	int32 Winner = -1;
	bool Running = false;
	FString Reason;
	double LastClosing = 0, LastKickScale = 0, LastEnergyRatio = 0;
	double ScrapeSpeed = 0;
    double ArenaScale=1.;
    bool bLowWall = false;
    bool bStarCrownRim = false;
    bool bStagedMobility = false;
    bool bGyroTrial = false;
    bool bGyroPush = false;
    FVector2D GyroTilt[2] = {};
    int32 FrameLimit = MaxFrames;
    double MobilityFactor[2] = {1., 1.};
    int32 LastContactFrame[2] = {-10000, -10000};
    static constexpr double WallContactRadius = 1.93;
    TFunction<bool(const FVector2D&,const FVector2D&,FVector2D&,FVector2D&)> SweepObstacle;
    int32 WallHits = 0, WallHitPlayer = -1;
    int32 PlayerWallHits[2]={},LastBeyHitFrame=-10000;
    double PeakClosing=0.;
    bool bTacticalSteering=false;
    double WallClosing = 0;
	double LastSpeedBefore[2] = {}, LastSpeedAfter[2] = {};
    double ImpactAttackMultiplier[2] = {1., 1.};

	// Loadout attrs. Defaults 1/1/1 + SpinDecay=0 keep ContactWeight / timeout unit tests = Feel85 baseline.
	// PrototypeBattle applies Grade1 Attack vs Defense for the formal demo match.
	double Attack[2] = {1.0, 1.0};
	double Defense[2] = {1.0, 1.0};
	double Mass[2] = {1.0, 1.0};
    bool bWeightCollision = false;
    double RingoutStrength = 1.;
    double BaseMoveSpeed = 4.5;
    double TypeMoveScale[2]={1.,1.}, NaturalSpinSeconds[2]={120.,120.};
	double SpinDecay[2] = {0.0, 0.0};
	double Spin[2] = {SpinStart, SpinStart};
	double YawDeg[2] = {};
	EBeyType Type[2] = {EBeyType::Attack, EBeyType::Attack};
	EBeyGrade Grade[2] = {EBeyGrade::Grade1, EBeyGrade::Grade1};
	double TimeoutMomentum[2] = {};
	double TimeoutMomentumEpsilon = 1.e-3;

	// M2 finish fields — off by default so Feel85 / spinout goldens stay green.
	bool bEnableBurstTrapXtr = false;
    bool bBalanceV1 = false;
    double DamageReduction[2] = {};
    double MaxDurability[2] = {DurabilityMax, DurabilityMax};
	double Durability[2] = {DurabilityMax, DurabilityMax};
	double TrapDwell[2] = {};
	bool bTrapPenalizing[2] = {false, false};
	TArray<FDashHitEvent, TInlineAllocator<8>> DashHits;
	ESimScoreTag ScoreTag = ESimScoreTag::None;

	// Skill shell data-layer: next-hit Extra mul (Chiwen). Does not change SPIN_KICK constant.
	double PendingExtraKickMul[2] = {1.0, 1.0};
	bool bWallContact[2] = {false,false};
    double SkillWearMul[2]={1.,1.}, SkillIncomingMul[2]={1.,1.}, SkillReflect[2]={0.,0.};
    // Passive events count once per contact episode; active skill counters retain their existing rules.
    int32 PassiveDealt[2]={}, PassiveTaken[2]={};
    bool bPassiveContact=false;
    double PassiveOutgoingMul[2]={1.,1.}, PassiveWearMul[2]={1.,1.};
    double SkillMassScale[2]={1.,1.}, SkillOutgoingMul[2]={1.,1.}, SkillEnemyDecayMul[2]={1.,1.};
    bool bWallBumpThisFrame = false; // rim correction contact (skill shell)

	void ApplyLoadout(int32 Index, const FBeyLoadout& L)
	{
		check(Index == 0 || Index == 1);
		Type[Index] = L.Type;
		Grade[Index] = L.Grade;
		Attack[Index] = L.Attack;
		Defense[Index] = L.Defense;
		Mass[Index] = L.Mass;
		SpinDecay[Index] = L.SpinDecayPerSec;
	}

	const TCHAR* TypeLabel(int32 Index) const
	{
		switch (Type[Index])
		{
		case EBeyType::Defense: return TEXT("DEFENSE");
		case EBeyType::Stamina: return TEXT("STAMINA");
        case EBeyType::Balance: return TEXT("BALANCE");
		default: return TEXT("ATTACK");
		}
	}

	void Reset()
	{
		Position[0] = FVector2D(-0.85, 0.1);
		Position[1] = FVector2D(0.85, -0.1);
		Velocity[0] = Velocity[1] = FVector2D::ZeroVector;
		PassiveDealt[0]=PassiveDealt[1]=PassiveTaken[0]=PassiveTaken[1]=0;
        bPassiveContact=false;
        for(int32 I=0;I<2;++I) PassiveOutgoingMul[I]=PassiveWearMul[I]=1.;
        Frames = Hits = 0; FirstHitFrame = Winner = -1;
        WallHits = 0; WallHitPlayer = -1; WallClosing = 0;
        PlayerWallHits[0]=PlayerWallHits[1]=0;LastBeyHitFrame=-10000;PeakClosing=0.;
        MobilityFactor[0] = MobilityFactor[1] = 1.;
        LastContactFrame[0] = LastContactFrame[1] = -10000;
		Running = false; Reason.Empty();
		LastClosing = LastKickScale = LastEnergyRatio = 0;
		LastSpeedBefore[0] = LastSpeedBefore[1] = LastSpeedAfter[0] = LastSpeedAfter[1] = 0;
        ImpactAttackMultiplier[0] = ImpactAttackMultiplier[1] = 1.;
		TimeoutMomentum[0] = TimeoutMomentum[1] = 0;
		Spin[0] = Spin[1] = SpinStart;
		YawDeg[0] = YawDeg[1] = 0;
        GyroTilt[0] = GyroTilt[1] = FVector2D::ZeroVector;
		for (int32 I=0; I<2; ++I) Durability[I] = MaxDurability[I];
		TrapDwell[0] = TrapDwell[1] = 0;
		bTrapPenalizing[0] = bTrapPenalizing[1] = false;
		DashHits.Reset();
		ScoreTag = ESimScoreTag::None;
		PendingExtraKickMul[0] = PendingExtraKickMul[1] = 1.0;
        bWallContact[0]=bWallContact[1]=false;
        for (int32 I=0;I<2;++I) {SkillWearMul[I]=SkillIncomingMul[I]=SkillMassScale[I]=SkillOutgoingMul[I]=SkillEnemyDecayMul[I]=1.;SkillReflect[I]=0.;}
		bWallBumpThisFrame = false;
		// Keep Attack/Defense/Mass/SpinDecay/Type/Grade across Reset (loadouts persist between rematches).
	}

	void Launch()
	{
		Reset();
		const FVector2D Direction = (Position[1] - Position[0]).GetSafeNormal();
		const float AimA = Random.FRandRange(-8.f, 8.f);
		const float AimB = Random.FRandRange(-8.f, 8.f);
		const float PowerA = Random.FRandRange(1.55f, 1.95f);
		const float PowerB = Random.FRandRange(1.55f, 1.95f);
		Velocity[0] = Direction.GetRotated(AimA) * PowerA;
		Velocity[1] = (-Direction).GetRotated(AimB) * PowerB;
		Running = true;
	}

	static double BowlHeight(double R)
	{
		const double Radii[] = {1.1, 1.4, 1.6, 1.8, 1.9, 2.0};
		const double Heights[] = {0.42, 0.63, 0.86, 0.93, 1.055, 1.07};
		if (R <= Radii[0]) return Heights[0];
		for (int32 I = 1; I < 6; ++I)
			if (R <= Radii[I]) return FMath::Lerp(Heights[I-1], Heights[I],
				(R - Radii[I-1]) / (Radii[I] - Radii[I-1]));
		return 1.07;
	}


	static bool InTrapZone(const FVector2D& P)
	{
		const double R = P.Size();
		return R >= TrapInnerR && R <= TrapOuterR;
	}

	static double TypeMul(EBeyType AtkType, EBeyType DefType)
	{
		// No explicit type-advantage table this build → 1.00 (draft).
		(void)AtkType; (void)DefType;
		return 1.0;
	}

	void ApplyCollisionWear()
	{
		if (!bEnableBurstTrapXtr && !bBalanceV1) return;
		const double ClosingNorm = FMath::Clamp(LastClosing / KickReferenceSpeed, 0.0, 1.0);
		auto WearOnto = [&](int32 Attacker, int32 Victim)
		{
			const double DefMit = bBalanceV1 ? FMath::Clamp(DamageReduction[Victim], 0., .75) : FMath::Clamp(0.25 * (Defense[Victim] - 1.0), -0.15, 0.25);
			const double AtkMul = FMath::Clamp(Attack[Attacker], 0.8, 1.4);
			const double Wear = (bBalanceV1 ? BalanceWearBase : WearBase) * ClosingNorm * TypeMul(Type[Attacker], Type[Victim]) * (1.0 - DefMit) * AtkMul * SkillWearMul[Victim] * (bGyroTrial ? ImpactAttackMultiplier[Attacker] : 1.);
			Durability[Victim] = FMath::Max(0.0, Durability[Victim] - Wear);
		};
		WearOnto(0, 1);
		WearOnto(1, 0);
	}

	void RegisterDashHit(int32 Attacker, int32 Victim)
	{
		if (!bEnableBurstTrapXtr || Attacker < 0 || Victim < 0 || Attacker == Victim) return;
		FDashHitEvent E;
		E.Attacker = Attacker;
		E.Victim = Victim;
		E.TimeSec = Frames * Step;
		E.bValid = true;
		DashHits.Add(E);
	}

	ESimScoreTag ResolveScoreTag() const
	{
		if (Reason != TEXT("ringout") || Winner < 0) return ESimScoreTag::None;
		const int32 Loser = 1 - Winner;
		const double EndT = Frames * Step;
		for (const FDashHitEvent& E : DashHits)
		{
			if (!E.bValid) continue;
			if (E.Victim != Loser) continue;
			if ((EndT - E.TimeSec) <= XtrWindowSeconds + 1.e-9) return ESimScoreTag::XTR;
		}
		return ESimScoreTag::OVR;
	}

	void Collide()
	{
		FVector2D D = Position[1] - Position[0];
		const double Distance = D.Size();
		if (Distance >= Radius * 2) {bPassiveContact=false; return;}
		const FVector2D N = Distance > 1.e-8 ? D / Distance : FVector2D(1, 0);
		const double Inv0 = bWeightCollision ? 1. / FMath::Max(Mass[0], .01) : 1.;
        const double Inv1 = bWeightCollision ? 1. / FMath::Max(Mass[1], .01) : 1.;
        const double Share0 = Inv0 / (Inv0 + Inv1), Share1 = 1. - Share0;
        const double EnergyBefore = Velocity[0].SizeSquared() + Velocity[1].SizeSquared();
		for (int32 I = 0; I < 2; ++I)
        {
            LastSpeedBefore[I] = Velocity[I].Size();
            if (bGyroTrial)
            {
                const double RelativeSpeed = FMath::Clamp(LastSpeedBefore[I] / FMath::Max(BaseMoveSpeed * TypeMoveScale[I], .01), 0., 1.);
                const double SpinStrength = FMath::Sqrt(FMath::Clamp(Spin[I], 0., 1.));
                ImpactAttackMultiplier[I] = 1.15 * (.35 + .65 * RelativeSpeed) * (.4 + .6 * SpinStrength);
            }
        }
		const FVector2D Tangent(-N.Y, N.X);
		const double Slip = FVector2D::DotProduct(Velocity[0] - Velocity[1], Tangent);
		const FVector2D Scrape = Tangent * Slip * (1.0 - ScrapeRetention) * .5;
		Velocity[0] -= Scrape * (2. * Share0);
		Velocity[1] += Scrape * (2. * Share1);
		const double Overlap = Radius * 2 - Distance;
		Position[0] -= N * Overlap * Share0;
		Position[1] += N * Overlap * Share1;
		const double Closing = FVector2D::DotProduct(Velocity[0] - Velocity[1], N);
		ScrapeSpeed = Closing < 1.5 ? FMath::Abs(Slip) : 0.;
		if (Closing <= 0) return;
		const bool NewContact=!bPassiveContact;
        bPassiveContact=true;
        const bool Dealt0=NewContact && FVector2D::DotProduct(Velocity[0],N)>0.;
        const bool Dealt1=NewContact && FVector2D::DotProduct(Velocity[1],-N)>0.;
        if(Dealt0) {++PassiveDealt[0];++PassiveTaken[1];}
        if(Dealt1) {++PassiveDealt[1];++PassiveTaken[0];}
        const double J = (1 + RESTITUTION) * Closing * 0.5;
		LastClosing = Closing;
        if (bGyroTrial || bGyroPush)
        {
            const double Jolt = FMath::Clamp(Closing / KickReferenceSpeed, 0., 1.) * 9.;
            for (int32 I=0; I<2; ++I)
                GyroTilt[I] = (GyroTilt[I] + N * (I == 0 ? -Jolt : Jolt) / (0.4 + 0.6 * FMath::Clamp(Spin[I], 0., 1.))).GetClampedToMaxSize(22.);
        }
		LastKickScale = FMath::Clamp(Closing / KickReferenceSpeed, 0.0, 1.0);
		const double ExtraKickBase = FMath::Clamp(RingoutStrength, 0., 1.) * SPIN_KICK * LastKickScale * FMath::Sqrt(FMath::Clamp((Spin[0] + Spin[1]) * .5, 0., 1.));
		// Attack -> outgoing impulse bias; Defense -> impact resist.
		// DefScale(1)=1 so Feel85 defaults (Attack=Defense=1) match prior equal-and-opposite ExtraKick.
		const double DefScaleOn1 = 2.0 / (1.0 + Defense[1]);
		const double DefScaleOn0 = 2.0 / (1.0 + Defense[0]);
		const double ExtraOnto1 = ExtraKickBase * Attack[0] * DefScaleOn1 * PendingExtraKickMul[0] * SkillOutgoingMul[0] * (Dealt0 ? PassiveOutgoingMul[0] : 1.) * (bGyroTrial ? ImpactAttackMultiplier[0] : 1.);
		const double ExtraOnto0 = ExtraKickBase * Attack[1] * DefScaleOn0 * PendingExtraKickMul[1] * SkillOutgoingMul[1] * (Dealt1 ? PassiveOutgoingMul[1] : 1.) * (bGyroTrial ? ImpactAttackMultiplier[1] : 1.);
        PendingExtraKickMul[0] = PendingExtraKickMul[1] = 1.;
		const double Side = Slip < 0 ? -1. : 1.;
        const FVector2D Onto0=(N*(J+ExtraOnto0)+Tangent*ExtraOnto0*TangentialKick*Side)*(2.*Share0)/(bWeightCollision ? 1. : SkillMassScale[0]);
        const FVector2D Onto1=(N*(J+ExtraOnto1)+Tangent*ExtraOnto1*TangentialKick*Side)*(2.*Share1)/(bWeightCollision ? 1. : SkillMassScale[1]);
        Velocity[0]-=Onto0*SkillIncomingMul[0]+Onto1*SkillReflect[1];
        Velocity[1]+=Onto1*SkillIncomingMul[1]+Onto0*SkillReflect[0];
		if (LastKickScale > .5)
			for (int32 I = 0; I < 2; ++I) Spin[I] *= 1.0 - (.01 + .02 * LastKickScale) * PassiveWearMul[I];
		for (int32 I = 0; I < 2; ++I) LastSpeedAfter[I] = Velocity[I].Size();
		LastEnergyRatio = (Velocity[0].SizeSquared() + Velocity[1].SizeSquared()) / FMath::Max(EnergyBefore, 1.e-12);
		++Hits;LastBeyHitFrame=Frames;PeakClosing=FMath::Max(PeakClosing,Closing);
        LastContactFrame[0] = LastContactFrame[1] = Frames;
		if (FirstHitFrame < 0) FirstHitFrame = Frames;
		ApplyCollisionWear();
	}

    void ResolveObstacle(int32 I,const FVector2D& From,FVector2D& To)
    {
        FVector2D ContactPosition,ContactNormal;
        if (!SweepObstacle || !SweepObstacle(From,To,ContactPosition,ContactNormal)) return;
        To=ContactPosition;
        const double Closing=-FVector2D::DotProduct(Velocity[I],ContactNormal);
        if (Closing>0.)
        {
            if (bGyroTrial || bGyroPush) GyroTilt[I] = (GyroTilt[I] + ContactNormal * FMath::Clamp(Closing / KickReferenceSpeed, 0., 1.) * 4. / (0.4 + 0.6 * FMath::Clamp(Spin[I], 0., 1.))).GetClampedToMaxSize(22.);
            Velocity[I]+=ContactNormal*((1.+RESTITUTION)*Closing);
            Spin[I]*=1.-.005*FMath::Clamp(Closing/KickReferenceSpeed,0.,1.);
            WallClosing=Closing;WallHitPlayer=I;++WallHits;++PlayerWallHits[I];
            LastContactFrame[I]=Frames;
            bWallBumpThisFrame=true;bWallContact[I]=true;
        }
    }

    void SteerType(int32 I)
    {
        if(!bTacticalSteering || Frames-LastContactFrame[I]<=18 || MobilityFactor[I]<.25)return;
        const FVector2D P=Position[I],Radial=P.GetSafeNormal();
        const FVector2D Tangent(-Radial.Y,Radial.X);
        double Ring=.95,Turn=.45;
        FVector2D Desired;
        switch(Type[I])
        {
        case EBeyType::Attack:
            if((Position[1-I]-P).Size()<Radius*2.5)return;
            Desired=(Position[1-I]-P).GetSafeNormal();Turn=.85;break;
        case EBeyType::Defense:Ring=.45;Turn=.55;break;
        case EBeyType::Stamina:Ring=1.05;Turn=.4;break;
        case EBeyType::Balance:
            Ring=.75;Turn=.55;
            if((Frames/120)%2==0)Desired=(Position[1-I]-P).GetSafeNormal();break;
        }
        if(Desired.IsNearlyZero())Desired=(Tangent*(I==0?1.:-1.)+Radial*((Ring*ArenaScale-P.Size())*2.)).GetSafeNormal();
        const double Speed=Velocity[I].Size();
        const FVector2D Direction=(Velocity[I].GetSafeNormal()*(1.-Turn*Step)+Desired*(Turn*Step)).GetSafeNormal();
        if(!Direction.IsNearlyZero())Velocity[I]=Direction*Speed;
    }


    double ContactRadius() const { return bStarCrownRim ? StarCrownRim::InnerWallRadius-Radius : WallContactRadius*ArenaScale; }
    bool InSlowTrap(int32 I) const { return bStarCrownRim && StarCrownRim::InSlowTrap(Position[I],Radius); }
    void ResolveRim(int32 I,FVector2D& Next)
    {
            if (bLowWall && Next.Size() > ContactRadius())
            {
                const FVector2D N = Next.GetSafeNormal();
                const double Outward = FVector2D::DotProduct(Velocity[I], N);
                // shortcut: planar low wall; use 3D flight when accurate vaulting is needed.
                // Cruising speed alone cannot vault the wall; a recent bey impact must launch it.
                const bool RecentBeyImpact = Frames - LastBeyHitFrame <= 30;
                if ((bStarCrownRim && !StarCrownRim::IsLowSection(Next)) || !RecentBeyImpact || RingoutStrength <= 0. || Outward < 4.5 + (1. - FMath::Clamp(RingoutStrength, 0., 1.)) * 3.)
                {
                    Next = N * (ContactRadius() - (bStarCrownRim ? .002 : 0.));
                    if (Outward > 0.)
                    {
                        if (bGyroTrial || bGyroPush) GyroTilt[I] = (GyroTilt[I] - N * FMath::Clamp(Outward / KickReferenceSpeed, 0., 1.) * 4. / (0.4 + 0.6 * FMath::Clamp(Spin[I], 0., 1.))).GetClampedToMaxSize(22.);
                        Velocity[I] -= N * ((1. + RESTITUTION) * Outward);
                        if (bStarCrownRim)
                        {
                            // Grazing contacts need a departure angle, otherwise the circular clamp traps an orbit on the wall.
                            const double Speed = Velocity[I].Size();
                            const double Inward = -FVector2D::DotProduct(Velocity[I], N);
                            if (Inward < Speed * .25)
                            {
                                const FVector2D Tangent = (Velocity[I] + N * Inward).GetSafeNormal();
                                Velocity[I] = (Tangent * FMath::Sqrt(1. - .25 * .25) - N * .25) * Speed;
                            }
                        }
                        Spin[I] *= 1. - .005 * FMath::Clamp(Outward / KickReferenceSpeed, 0., 1.);
                        bWallBumpThisFrame=true; bWallContact[I]=true;
                        WallClosing = Outward; WallHitPlayer = I; ++WallHits;++PlayerWallHits[I];
                        LastContactFrame[I] = Frames;
                    }
                }
            }
    }

	void Tick()
	{
		if (!Running) return;
		bWallBumpThisFrame=false; bWallContact[0]=bWallContact[1]=false;
		++Frames;
		ScrapeSpeed = 0;
        WallHitPlayer = -1;
		for (int32 I = 0; I < 2; ++I)
		{
			const FVector2D P = Position[I];
			constexpr double DX = 0.06;
			const double GX = (BowlHeight((P + FVector2D(DX, 0)).Size()/ArenaScale) - BowlHeight((P - FVector2D(DX, 0)).Size()/ArenaScale)) / (2 * DX);
			const double GY = (BowlHeight((P + FVector2D(0, DX)).Size()/ArenaScale) - BowlHeight((P - FVector2D(0, DX)).Size()/ArenaScale)) / (2 * DX);
			Velocity[I] -= FVector2D(GX, GY) * (3.0 * Step);
            if (bGyroTrial || bGyroPush)
            {
                // shortcut: planar precession approximation; replace with 3D rigid-body dynamics if validated for competitive play.
                const double Stability = FMath::Clamp(Spin[I], 0., 1.);
                GyroTilt[I] = GyroTilt[I].GetRotated((I == 0 ? 1. : -1.) * (55. + 100. * Stability) * Step) * FMath::Exp(-(.35 + 1.8 * Stability) * Step);
                if (bGyroPush) Velocity[I] += GyroTilt[I] * (.015 * Step);
                else
                {
                    const FVector2D Direction = Velocity[I].GetSafeNormal();
                    const double Turn = FVector2D::CrossProduct(Direction, GyroTilt[I]) * .04 * Step;
                    Velocity[I] = Velocity[I].GetRotated(Turn);
                }
            }
			// Lower spin loses mobility; impulses remain free to produce a short burst.
            if (!bStagedMobility) Velocity[I] *= FMath::Exp(-.12 * Step);
            SteerType(I);
			FVector2D Next = P + Velocity[I] * Step;
            ResolveObstacle(I,P,Next);
            ResolveRim(I,Next);
			const double R = Next.Size();
			if (R > 2.0*ArenaScale && R <= 2.28*ArenaScale)
			{
				const FVector2D Radial = Next.GetSafeNormal();
				const double Outward = FVector2D::DotProduct(Velocity[I], Radial);
				if (Outward < 2.25)
				{
					Velocity[I] -= Radial * (Outward * 1.2 + 3.0 * Step);
					Next = P + Velocity[I] * Step;
                    bWallBumpThisFrame=true; bWallContact[I]=true;
				}
			}
			Position[I] = Next;
			// Trap dwell / penalize (M2); does not change rim/out radii.
			if (bEnableBurstTrapXtr && !bBalanceV1 && InTrapZone(Position[I]/ArenaScale))
			{
				TrapDwell[I] += Step;
				bTrapPenalizing[I] = TrapDwell[I] >= TrapDwellSeconds;
			}
			else
			{
				TrapDwell[I] = 0;
				bTrapPenalizing[I] = false;
			}
			// Grade1 spin decay (no-op when SpinDecay==0, i.e. unit-test Feel85 baseline).
			double Decay = SpinDecay[I] * SkillEnemyDecayMul[1-I];
			if (bEnableBurstTrapXtr && bTrapPenalizing[I]) Decay += TrapSpinExtra;
			if (Decay > 0.0)
			{
				const double RemainingFactor = FMath::Exp(-Decay * Step);
				Spin[I] *= RemainingFactor;
                if (bStagedMobility)
                {
                    const double NextFactor = bGyroTrial
                        ? MobilityProfile::GyroTrialFactor(MobilityProfile::RemainingSpinSeconds(Spin[I], SpinStopThreshold, Decay))
                        : MobilityProfile::SpeedPercent(Frames * Step * MobilityProfile::Duration / NaturalSpinSeconds[I]) / MobilityProfile::InitialPercent;
                    Velocity[I] *= MobilityFactor[I] > 1.e-9 ? NextFactor / MobilityFactor[I] : 0.;
                    MobilityFactor[I] = NextFactor;
                    // Restore drive after the impact has had time to separate the tops.
                    const double TargetSpeed = BaseMoveSpeed * TypeMoveScale[I] * NextFactor;
                    const double Speed = Velocity[I].Size();
                    if (Frames - LastContactFrame[I] > 18 && Speed < TargetSpeed && !InSlowTrap(I))
                    {
                        FVector2D Direction = Velocity[I].GetSafeNormal();
                        if (Direction.IsNearlyZero()) Direction = FVector2D(-P.Y, P.X).GetSafeNormal();
                        if (Direction.IsNearlyZero()) Direction = FVector2D(I == 0 ? 1. : -1., 0.);
                        Velocity[I] = Direction * FMath::Min(TargetSpeed, Speed + 3. * Step);
                    }
                }
                else Velocity[I] *= RemainingFactor;
			}
            if (InSlowTrap(I) && Frames-LastBeyHitFrame>30)
                Velocity[I]*=FMath::Exp(-2.5*Step);

			YawDeg[I] += 900.0 * Spin[I] * Step * (I == 0 ? 1.0 : -1.05);
		}
        const FVector2D BeforePair[2]={Position[0],Position[1]};
        Collide();
        // Pair separation can push a top sideways into a block after its movement sweep.
        for (int32 I=0;I<2;++I) {ResolveObstacle(I,BeforePair[I],Position[I]);ResolveRim(I,Position[I]);}
		const bool OutA = Position[0].Size() > 2.28*ArenaScale, OutB = Position[1].Size() > 2.28*ArenaScale;
		if (OutA || OutB)
		{
			// Priority 1: ringout (simultaneous → DRAW). Ignores concurrent burst.
			Reason = TEXT("ringout"); Winner = OutA == OutB ? -1 : (OutA ? 1 : 0);
			ScoreTag = ResolveScoreTag();
			Running = false;
			return;
		}
		if (bEnableBurstTrapXtr || bBalanceV1)
		{
			const bool BurstA = Durability[0] <= 0.0;
			const bool BurstB = Durability[1] <= 0.0;
			if (BurstA || BurstB)
			{
				// Priority 2: burst
				Reason = TEXT("burst");
				if (BurstA && BurstB) Winner = -1;
				else Winner = BurstA ? 1 : 0;
				ScoreTag = ESimScoreTag::None;
				Running = false;
				return;
			}
		}
		const bool StopA = Spin[0] <= SpinStopThreshold;
		const bool StopB = Spin[1] <= SpinStopThreshold;
		if (StopA || StopB)
		{
			// Priority 3 trap / 4 spinout: trap if loser was trap-penalizing this frame.
			int32 LocalWinner = -1;
			if (StopA && StopB)
			{
				const double Diff = Spin[0] - Spin[1];
				if (Diff > 1.e-6) LocalWinner = 0;
				else if (Diff < -1.e-6) LocalWinner = 1;
				else LocalWinner = -1;
			}
			else LocalWinner = StopA ? 1 : 0;

			bool bTrapEnd = false;
			if (bEnableBurstTrapXtr && LocalWinner >= 0)
			{
				const int32 Loser = 1 - LocalWinner;
				bTrapEnd = bTrapPenalizing[Loser];
			}
			else if (bEnableBurstTrapXtr && LocalWinner < 0)
			{
				bTrapEnd = bTrapPenalizing[0] || bTrapPenalizing[1];
			}
			Reason = (bTrapEnd ? TEXT("trap") : TEXT("spinout"));
			Winner = LocalWinner;
			ScoreTag = ESimScoreTag::None;
			Running = false;
			return;
		}
		if (Frames >= FrameLimit)
		{
			// Priority 5: residual planar momentum.
			Reason = TEXT("timeout");
			TimeoutMomentum[0] = Velocity[0].Size() * Mass[0];
			TimeoutMomentum[1] = Velocity[1].Size() * Mass[1];
			const double Diff = TimeoutMomentum[0] - TimeoutMomentum[1];
			if (Diff > TimeoutMomentumEpsilon) Winner = 0;
			else if (Diff < -TimeoutMomentumEpsilon) Winner = 1;
			else Winner = -1;
			ScoreTag = ESimScoreTag::None;
			Running = false;
		}
	}
};
