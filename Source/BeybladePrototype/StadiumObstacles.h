#pragma once
#include "CoreMinimal.h"
namespace StadiumObstacles
{
inline const TArray<TArray<FVector2D>>& Polygons()
{
    // Measured orange-block footprints from industrial-bowl-original.glb, in unscaled world metres.
    // shortcut: convex footprints; regenerate these if the stadium mesh shape changes.
    static const TArray<TArray<FVector2D>> Data={
        {FVector2D(1.55337,0.31154), FVector2D(1.55408,-0.35721), FVector2D(1.55527,-0.36203), FVector2D(1.57088,-0.37580), FVector2D(1.66801,-0.41161), FVector2D(1.74141,-0.43693), FVector2D(1.85153,-0.47215), FVector2D(1.89264,-0.47709), FVector2D(1.96962,-0.48061), FVector2D(2.34295,-0.48061), FVector2D(2.34295,0.48034), FVector2D(1.96962,0.48034), FVector2D(1.89288,0.47662), FVector2D(1.85296,0.47125), FVector2D(1.84867,0.47045), FVector2D(1.62129,0.39207), FVector2D(1.57422,0.37508), FVector2D(1.55491,0.36260), FVector2D(1.55360,0.35807)},
        {FVector2D(-1.18325,-2.06265), FVector2D(-0.50971,-2.30780), FVector2D(-0.39400,-1.98988), FVector2D(-0.40205,-1.74296), FVector2D(-0.40532,-1.73128), FVector2D(-0.42403,-1.69923), FVector2D(-0.50355,-1.67099), FVector2D(-0.60836,-1.63833), FVector2D(-0.69702,-1.61128), FVector2D(-0.87607,-1.56183), FVector2D(-0.92177,-1.56481), FVector2D(-0.93279,-1.56850), FVector2D(-0.94024,-1.57505), FVector2D(-0.99113,-1.63619), FVector2D(-1.06156,-1.72831)},
        {FVector2D(-1.17804,2.06455), FVector2D(-1.05452,1.72521), FVector2D(-1.03617,1.69720), FVector2D(-0.96503,1.60342), FVector2D(-0.94203,1.57458), FVector2D(-0.93565,1.56826), FVector2D(-0.89347,1.55801), FVector2D(-0.87899,1.56075), FVector2D(-0.71680,1.60282), FVector2D(-0.62450,1.63178), FVector2D(-0.42448,1.69851), FVector2D(-0.40482,1.73712), FVector2D(-0.39668,1.89896), FVector2D(-0.39531,1.94281), FVector2D(-0.39424,1.98797), FVector2D(-0.51054,2.30750)}
    };return Data;
}
inline bool Sweep(const FVector2D& Start,const FVector2D& End,double ArenaScale,double Radius,FVector2D& Position,FVector2D& Normal)
{
    const FVector2D Delta=End-Start;
    double BestTime=2.;bool Hit=false;
    for (const auto& Polygon:Polygons())
    {
        double Enter=0.,Exit=1.,Depth=1.e30;
        FVector2D EnterNormal=FVector2D::ZeroVector,EscapeNormal=FVector2D::ZeroVector;
        bool Inside=true,Miss=false;
        for (int32 I=0;I<Polygon.Num();++I)
        {
            const FVector2D A=Polygon[I]*ArenaScale,B=Polygon[(I+1)%Polygon.Num()]*ArenaScale;
            const FVector2D Edge=B-A,N=FVector2D(Edge.Y,-Edge.X).GetSafeNormal();
            const double Distance=FVector2D::DotProduct(Start-A,N)-Radius;
            const double Rate=FVector2D::DotProduct(Delta,N);
            if (Distance>0.) Inside=false;
            if (-Distance<Depth) {Depth=-Distance;EscapeNormal=N;}
            if (FMath::Abs(Rate)<1.e-12) {if(Distance>0.) {Miss=true;break;}continue;}
            const double Time=-Distance/Rate;
            if (Rate<0.) {if(Time>=Enter) {Enter=Time;EnterNormal=N;}}
            else Exit=FMath::Min(Exit,Time);
            if(Enter>Exit) {Miss=true;break;}
        }
        if (Miss) continue;
        if (Inside)
        {
            Position=Start+EscapeNormal*(FMath::Max(Depth,0.)+.002);Normal=EscapeNormal;return true;
        }
        if (Enter>=0. && Enter<=1. && Enter<BestTime && !EnterNormal.IsNearlyZero())
        {
            BestTime=Enter;Normal=EnterNormal;Position=Start+Delta*Enter+Normal*.002;Hit=true;
        }
    }
    return Hit;
}
}
