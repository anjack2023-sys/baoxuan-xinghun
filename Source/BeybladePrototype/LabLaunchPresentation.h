#pragma once
#include "CoreMinimal.h"

// Approved launch timeline (30 fps clip, 144 frames, frame 1 = t 0).
// Presentation only: does not touch SPIN_KICK / RESTITUTION / any battle rule.
namespace LabLaunch
{
constexpr double Release = 87. / 30.;          // 2.9 s, Blender frame 88
constexpr double Duration = 143. / 30.;        // 4.766667 s, clip end
constexpr double FlightDuration = .7;
inline double Smooth(double T) { T = FMath::Clamp(T, 0., 1.); return T * T * (3. - 2. * T); }
inline double Raise(double T) { return Smooth(T / .55) * (1. - Smooth((T - Release) / .45)); }
inline double Pull(double T) { return Smooth((T - .85) / (Release - .85)); }
inline double Flight(double T) { return Smooth((T - Release) / FlightDuration); }
}
