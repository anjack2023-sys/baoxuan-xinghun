#pragma once
#include "BattleSimulation.h"

inline double VisualSpinRate(double Spin, EBeyType Type)
{
    // Approved previews: one turn in 0.18s or 0.27s at full spin.
    const double Period = Type == EBeyType::Attack || Type == EBeyType::Balance ? .18 : .27;
    return (360. / Period) * FMath::Clamp(Spin, 0., 1.);
}

inline double VisualTiltScale(double Spin)
{
    return FMath::Clamp((.8 - Spin) / .6, 0., 1.);
}
