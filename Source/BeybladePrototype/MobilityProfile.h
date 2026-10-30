#pragma once
#include "CoreMinimal.h"

namespace MobilityProfile
{
    constexpr double Duration = 120.;
    constexpr double InitialPercent = 90.;
    inline double GyroTrialFactor(double Remaining)
    {
        if (Remaining >= 30.) return 1.;
        if (Remaining >= 15.) return FMath::Lerp(.5, 1., (Remaining - 15.) / 15.);
        if (Remaining >= 5.) return FMath::Lerp(.15, .5, (Remaining - 5.) / 10.);
        if (Remaining >= 1.) return FMath::Lerp(.03, .15, (Remaining - 1.) / 4.);
        return FMath::Clamp(Remaining, 0., 1.) * .03;
    }
    inline double RemainingSpinSeconds(double Spin, double StopThreshold, double Decay)
    {
        if (Decay <= 0.) return 1.e9;
        return FMath::Max(0., FMath::Loge(FMath::Max(Spin, StopThreshold) / StopThreshold) / Decay);
    }
    inline double SpeedPercent(double Age)
    {
        Age = FMath::Clamp(Age, 0., Duration);
        if (Age <= 90.) return InitialPercent;
        if (Age <= 115.) return FMath::Lerp(InitialPercent, 45., (Age - 90.) / 25.);
        return FMath::Lerp(45., 0., (Age - 115.) / 5.);
    }
}
