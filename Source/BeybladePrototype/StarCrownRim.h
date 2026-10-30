#pragma once
#include "CoreMinimal.h"
namespace StarCrownRim
{
    constexpr double HalfGapDegrees = 18.;
    constexpr double InnerWallRadius = 1.6;
    constexpr double TrapRingRadius = 1.23;
    constexpr double TrapHalfSegment = .13, TrapRadius = .09;
    inline bool InSlowTrap(const FVector2D& Position, double BeyRadius)
    {
        for(int32 I=0;I<6;++I)
        {
            const double Angle=PI/2.+I*PI/3.;
            const FVector2D N(FMath::Cos(Angle),FMath::Sin(Angle)),T(-N.Y,N.X);
            const FVector2D D=Position-N*TrapRingRadius;
            const FVector2D Closest=T*FMath::Clamp(FVector2D::DotProduct(D,T),-TrapHalfSegment,TrapHalfSegment);
            if((D-Closest).SizeSquared()<=FMath::Square(TrapRadius+BeyRadius))return true;
        }
        return false;
    }
    inline bool IsLowSection(const FVector2D& Position)
    {
        if (Position.IsNearlyZero()) return false;
        const double Angle = FMath::Atan2(FMath::Abs(Position.Y), FMath::Abs(Position.X));
        return FMath::Abs(Angle - PI / 4.) <= FMath::DegreesToRadians(HalfGapDegrees);
    }
}
