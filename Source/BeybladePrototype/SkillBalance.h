#pragma once
#include "CoreMinimal.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

namespace SkillBalance
{
struct FRow
{
    FString Id, Slot, Name, Condition, Effect, Secondary, Description;
    double Value = 1., Duration = 0., SecondaryValue = 1.;
    bool Valid = false;
};

inline bool Parse(const FString& Line, FRow& Row)
{
    TArray<FString> C;
    Line.ParseIntoArray(C, TEXT(","), false);
    if (C.Num() != 14 || C[0] == TEXT("bey_id") || (C[1] != TEXT("active") && C[1] != TEXT("passive"))) return false;
    if (!C[7].IsNumeric() || !C[11].IsNumeric() || !C[13].IsNumeric()) return false;
    Row.Id=C[0]; Row.Slot=C[1]; Row.Name=C[3]; Row.Condition=C[5]; Row.Effect=C[6];
    Row.Value=FCString::Atod(*C[7]); Row.Duration=FCString::Atod(*C[11]);
    Row.Description=C[10]; Row.Secondary=C[12]; Row.SecondaryValue=FCString::Atod(*C[13]);
    Row.Valid=FMath::IsFinite(Row.Value) && Row.Value>0. && Row.Value<=4. &&
        FMath::IsFinite(Row.Duration) && Row.Duration>=0. && Row.Duration<=60. &&
        FMath::IsFinite(Row.SecondaryValue) && Row.SecondaryValue>=0. && Row.SecondaryValue<=4.;
    return Row.Valid;
}

inline const TMap<FString,FRow>& Rows()
{
    static const TMap<FString,FRow> Data=[] {
        TMap<FString,FRow> Result;
        for (const FString& Path : {FPaths::ProjectContentDir()/TEXT("Beyblade/Data/skills-grade1.csv"),
             FPaths::ProjectDir()/TEXT("docs/balance/skills-grade1.csv")})
        {
            FString Text;
            if (!FFileHelper::LoadFileToString(Text,*Path)) continue;
            TMap<FString,FRow> Candidate;
            TArray<FString> Lines; Text.ParseIntoArrayLines(Lines);
            for (const FString& Line : Lines) { FRow Row; if (Parse(Line,Row)) Candidate.Add(Row.Id+TEXT("/")+Row.Slot,Row); }
            if (Candidate.Num()!=16) continue;
            UE_LOG(LogTemp,Display,TEXT("SKILL_DATA rows=16 source=%s"),*Path);
            return Candidate;
        }
        UE_LOG(LogTemp,Error,TEXT("SKILL_DATA invalid/missing table; skills disabled"));
        return Result;
    }();
    return Data;
}
inline FRow Get(const FString& Id,const TCHAR* Slot)
{
    if (const FRow* Row=Rows().Find(Id+TEXT("/")+Slot)) return *Row;
    return FRow();
}
struct FPassiveInfo {const TCHAR* Name; const TCHAR* Line1; const TCHAR* Line2;};
inline FPassiveInfo PassiveInfo(const FString& Id)
{
    if(Id==TEXT("chifeng")) return {TEXT("破阵"),TEXT("3秒未碰对手：下次主动撞击推力+20%"),TEXT("命中消耗；重新等待3秒")};
    if(Id==TEXT("chiwen")) return {TEXT("燎原"),TEXT("主动撞击：攻击+4% · 最多3层"),TEXT("持续2.5秒；命中刷新，超时清空")};
    if(Id==TEXT("bilei")) return {TEXT("蓄震"),TEXT("受击3次：下次主动撞击推力+20%"),TEXT("强化期间暂停蓄积；命中清空")};
    if(Id==TEXT("huangkai")) return {TEXT("守界"),TEXT("外圈防御+12%；外圈受击减击退15%"),TEXT("减击退持续1.5秒 · 冷却6秒")};
    if(Id==TEXT("changxuan")) return {TEXT("静息"),TEXT("连续3秒无碰撞：自然衰减再降12%"),TEXT("碰对手、墙或障碍立即中断")};
    if(Id==TEXT("cuipan")) return {TEXT("扎根"),TEXT("受到撞击：受到的击退降低15%"),TEXT("持续2秒；再次受击刷新")};
    if(Id==TEXT("hengblade")) return {TEXT("转势"),TEXT("主动撞击：防御+10%；受击：攻击+10%"),TEXT("持续2秒 · 互相替换；对撞优先防御")};
    if(Id==TEXT("shuanghuan")) return {TEXT("寒蚀"),TEXT("主动撞击：对手自然衰减提高10%"),TEXT("持续3秒 · 冷却5秒 · 不叠层")};
    return {TEXT("未知"),TEXT("数据未载入"),TEXT("")};
}
inline FString EffectLabel(const FRow& Row)
{
    if(!Row.Valid) return TEXT("数据未载入");
    if(Row.Slot==TEXT("passive")) return Row.Description;
    FString Stat=TEXT("效果");
    if(Row.Effect.EndsWith(TEXT("AllStatMul"))) Stat=TEXT("攻防质量");
    else if(Row.Effect.EndsWith(TEXT("EnemyDecayMul"))) Stat=TEXT("对手衰减");
    else if(Row.Effect.EndsWith(TEXT("AttackMul"))) Stat=TEXT("攻击");
    else if(Row.Effect.EndsWith(TEXT("DefenseMul"))) Stat=TEXT("防御");
    else if(Row.Effect.EndsWith(TEXT("DecayMul"))) Stat=TEXT("衰减");
    else if(Row.Effect.EndsWith(TEXT("MassMul"))) Stat=TEXT("质量");
    else if(Row.Effect.EndsWith(TEXT("WearMul"))) Stat=TEXT("磨损");
    else if(Row.Effect.EndsWith(TEXT("IncomingKickMul"))) Stat=TEXT("受击");
    else if(Row.Effect.EndsWith(TEXT("ExtraKickMul"))) Stat=TEXT("下一击追加冲量");
    FString Label=FString::Printf(TEXT("%s ×%.2f"),*Stat,Row.Value);
    if(Row.Secondary==TEXT("defense_mul")) Label+=FString::Printf(TEXT("  防御 ×%.2f"),Row.SecondaryValue);
    if(Row.Secondary==TEXT("reflect")) Label+=FString::Printf(TEXT("  回抛 %.0f%%"),100.*Row.SecondaryValue);
    if(Row.Secondary==TEXT("ringout_add")) Label+=FString::Printf(TEXT("  推力 +%.0f%%"),100.*Row.SecondaryValue);
    if(Row.Duration>0.) Label+=FString::Printf(TEXT(" · %.1fs"),Row.Duration);
    else if(Row.Slot==TEXT("active")) Label+=TEXT(" · 下一次碰撞");
    return Label;
}
}
