#pragma once
#include "CoreMinimal.h"

namespace IronWallPresentation
{
constexpr double DeploySeconds = .18;
constexpr double FadeSeconds = .28;
constexpr double HitSeconds = .38;
inline double Opacity(double Age, double FadeAge)
{
    return FMath::Clamp(Age / DeploySeconds, 0., 1.)
        * (FadeAge < 0. ? 1. : FMath::Clamp(1. - FadeAge / FadeSeconds, 0., 1.));
}
inline double HitOpacity(double Age)
{
    return Age < 0. ? 0. : FMath::Clamp(1. - Age / HitSeconds, 0., 1.);
}
}
