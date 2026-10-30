#pragma once
#include "CoreMinimal.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
namespace MobileUX
{
inline bool Enabled() { return PLATFORM_ANDROID || PLATFORM_IOS || FParse::Param(FCommandLine::Get(),TEXT("MobilePreview")); }
inline FVector2D StartButton() { return FVector2D(1120.f, 650.f); }
inline bool HitStart(const FVector2D& P) { const auto B=StartButton(); return P.X>=B.X && P.X<B.X+260 && P.Y>=B.Y && P.Y<B.Y+96; }
inline FVector2D Button(int32 Index) { return FVector2D(1420.f+Index*160.f,190.f); }
inline int32 Hit(const FVector2D& P) { for(int32 I=0;I<3;++I) {const auto B=Button(I);if(P.X>=B.X && P.X<=B.X+150 && P.Y>=B.Y && P.Y<=B.Y+72)return I;}return -1; }
}
