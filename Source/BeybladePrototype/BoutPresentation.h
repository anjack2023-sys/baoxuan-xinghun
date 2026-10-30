#pragma once
#include "BattleSimulation.h"
#include "LabLaunchPresentation.h"
struct FLaunchSetup
{
    int32 Angle=0,Power=100;
    // Approved refined launch: release 2.9 s, clip end 4.7667 s (LabLaunch).
    static constexpr double ReleaseTime=LabLaunch::Release,Duration=LabLaunch::Duration;
    void Adjust(int32 A,int32 P) {Angle=FMath::Clamp(Angle+A,-45,45);Power=FMath::Clamp(Power+P,70,120);}
    void Apply(FBattleSimulation& S) const {S.Velocity[0]=S.Velocity[0].GetRotated(FMath::Clamp(Angle,-45,45))* (FMath::Clamp(Power,70,120)/100.);}
    static FVector2D Button(int32 I) {return FVector2D(95.f+(I%2)*340.f,805.f+(I/2)*95.f);}
    static int32 Hit(const FVector2D& P) {for(int32 I=0;I<4;++I){const FVector2D B=Button(I);if(P.X>=B.X && P.X<B.X+80 && P.Y>=B.Y && P.Y<B.Y+70)return I;}return -1;}
    static const TCHAR* Style(EBeyType T) {switch(T){case EBeyType::Defense:return TEXT("防御：小圈守中，稳住迎击");case EBeyType::Stamina:return TEXT("持久：中圈巡航，减少主动追撞");case EBeyType::Balance:return TEXT("均衡：巡航与接近交替");default:return TEXT("攻击：主动接近，争取连续碰撞");}}
};
inline FString ExplainBout(const FBattleSimulation& S)
{
    if(S.Reason==TEXT("timeout")) return FString::Printf(TEXT("超时按残余动量判定：P1 %.2f / P2 %.2f%s"),S.TimeoutMomentum[0],S.TimeoutMomentum[1],S.Winner<0?TEXT("，接近相同判平局"):TEXT("，较高者获胜"));
    if(S.Winner<0)return FString::Printf(TEXT("双方同时%s，按平局计分"),S.Reason==TEXT("ringout")?TEXT("出界"):S.Reason==TEXT("burst")?TEXT("耐久耗尽"):TEXT("停转"));
    const int32 Loser=2-S.Winner;
    if(S.Reason==TEXT("ringout"))return FString::Printf(TEXT("P%d 越过场地边界%s，出界判负"),Loser,S.Frames-S.LastBeyHitFrame<=30?TEXT("（最近0.5秒内发生过陀螺碰撞）"):TEXT(""));
    if(S.Reason==TEXT("burst"))return FString::Printf(TEXT("P%d 碰撞耐久降至零，爆裂判负"),Loser);
    if(S.Reason==TEXT("trap"))return FString::Printf(TEXT("P%d 在陷阱区域停转，期间承受额外转速消耗"),Loser);
    return FString::Printf(TEXT("P%d 转速降至停转阈值，停转判负"),Loser);
}
