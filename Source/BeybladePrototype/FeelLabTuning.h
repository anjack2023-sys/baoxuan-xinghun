#pragma once
#include "BattleSimulation.h"

namespace FeelLabTuning
{
    constexpr double SpinSeconds = MobilityProfile::Duration;
    constexpr double MovePercent = MobilityProfile::InitialPercent;
    constexpr double FullMoveSpeed = 5.;
    inline double MassForLevel(int32 Level) { return FMath::Clamp(Level, 1, 100) / 50.; }
    constexpr int32 MinMoveLevel = 10, MaxMoveLevel = 200;
    inline int32 ClampMoveLevel(int32 Level) {return FMath::Clamp(Level,MinMoveLevel,MaxMoveLevel);}
    inline double SpeedForLevel(int32 Level) {return FullMoveSpeed*ClampMoveLevel(Level)/100.;}
    inline void SetMoveLevel(FBattleSimulation& S,int32 Level)
    {
        const double NewSpeed=SpeedForLevel(Level);
        const double Ratio=NewSpeed/FMath::Max(S.BaseMoveSpeed,1.e-9);
        for(int32 I=0;I<2;++I) S.Velocity[I]*=Ratio;
        S.BaseMoveSpeed=NewSpeed;
    }
    inline void Place(FBattleSimulation& S)
    {
        S.Position[0] = FVector2D(-1.2, -.55);
        S.Position[1] = FVector2D(.75, .95);
    }
    inline void Apply(FBattleSimulation& S,int32 MoveLevel=90)
    {
        Place(S);
        S.BaseMoveSpeed=SpeedForLevel(MoveLevel);
        S.bLowWall = true;
        S.bStagedMobility = true;
        S.FrameLimit = 120 * 60;
        S.bBalanceV1 = true;
        const FVector2D Targets[] = {FVector2D(.55, .2), FVector2D(-.35, .55)};
        for (int32 I = 0; I < 2; ++I)
        {
            S.TypeMoveScale[I]=1.;S.NaturalSpinSeconds[I]=SpinSeconds;
            S.SpinDecay[I] = FMath::Loge(S.SpinStart / S.SpinStopThreshold) / SpinSeconds;
            S.Velocity[I] = (Targets[I] - S.Position[I]).GetSafeNormal() * S.BaseMoveSpeed;
        }
    }
}
