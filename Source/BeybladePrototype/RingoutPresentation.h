#pragma once
#include "CoreMinimal.h"

// Centimetres, visual only: clear the bowl and fall to the actual floor.
// Does not touch BattleSimulation impulse constants.

inline double RingoutFallDuration(const FVector& Start, double FloorZ)
{
    constexpr double Gravity = 980.0;
    constexpr double LiftSpeed = 120.0;
    constexpr double Settle = 0.18;
    const double Drop = FMath::Max(0.0, Start.Z - FloorZ);
    if (Drop <= 0.0) return Settle;
    const double Flight = (LiftSpeed + FMath::Sqrt(LiftSpeed * LiftSpeed + 2.0 * Drop * Gravity)) / Gravity;
    return Flight + Settle;
}

inline FVector RingoutLocation(const FVector& Start, double FloorZ, double Elapsed)
{
    constexpr double Gravity = 980.0;
    constexpr double LiftSpeed = 120.0;
    constexpr double MinFinalRadial = 320.0; // clearly past OUT_RADIUS 228cm + one bey
    constexpr double MinTravel = 120.0;
    const double Drop = FMath::Max(0.0, Start.Z - FloorZ);
    if (Drop == 0.0) return FVector(Start.X, Start.Y, FloorZ);
    const double Flight = (LiftSpeed + FMath::Sqrt(LiftSpeed * LiftSpeed + 2.0 * Drop * Gravity)) / Gravity;
    const double T = FMath::Clamp(Elapsed, 0.0, Flight);
    const FVector Flat(Start.X, Start.Y, 0.0);
    const double StartRadial = Flat.Size();
    const FVector Outward = StartRadial > 1.e-3 ? Flat / StartRadial : FVector(1, 0, 0);
    const double TravelNeeded = FMath::Max(MinTravel, MinFinalRadial - StartRadial);
    const double Travel = TravelNeeded * FMath::Clamp(T / FMath::Min(0.28, Flight), 0.0, 1.0);
    const double Z = FMath::Max(FloorZ, Start.Z + LiftSpeed * T - 0.5 * Gravity * T * T);
    return FVector(Start.X, Start.Y, Z) + Outward * Travel;
}

// Presentation-only tumble; settles after landing. Labels stay attached to the actor.
inline FRotator RingoutRotation(double Elapsed, double Duration, int32 PlayerIndex)
{
    constexpr double Settle = 0.18;
    const double Flight = FMath::Max(1.e-3, Duration - Settle);
    const double T = FMath::Clamp(Elapsed, 0.0, Duration);
    const double U = FMath::Clamp(T / Flight, 0.0, 1.0);
    const double SpinRate = (PlayerIndex == 0) ? 640.0 : -700.0;
    double Yaw = SpinRate * U;
    double Pitch = 48.0 * FMath::Sin(PI * U);
    double Roll = 28.0 * FMath::Sin(1.6 * PI * U);
    if (T > Flight)
    {
        const double S = FMath::Clamp((T - Flight) / Settle, 0.0, 1.0);
        const double Ease = 1.0 - (1.0 - S) * (1.0 - S);
        Pitch = FMath::Lerp(0.0, 14.0, Ease);
        Roll = FMath::Lerp(0.0, (PlayerIndex == 0) ? -9.0 : 9.0, Ease);
        Yaw = SpinRate + ((PlayerIndex == 0) ? 25.0 : -25.0) * Ease;
    }
    return FRotator(Pitch, Yaw, Roll);
}