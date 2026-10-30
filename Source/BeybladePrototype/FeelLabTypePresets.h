#pragma once
#include "BattleSimulation.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

namespace FeelLabTypes
{
struct FRow
{
    int32 Attack=50,Defense=50,Life=50,Move=100;
    double NaturalSeconds=30.;
    bool Valid=false;
    double AttackValue() const {return 1.+(Attack-50)/100.;}
    double DefenseValue() const {return 1.+Defense/100.;}
    double SpinSeconds() const {return NaturalSeconds;}
};
inline const TArray<FRow>& Rows()
{
    static const TArray<FRow> Data=[] {
        TArray<FRow> Result;Result.SetNum(4);
        FString Text;
        const FString File=FPaths::ProjectContentDir()/TEXT("Beyblade/Data/feel-lab-types.csv");
        if(!FFileHelper::LoadFileToString(Text,*File)) {UE_LOG(LogTemp,Error,TEXT("FEEL_TYPES_MISSING %s"),*File);return Result;}
        TArray<FString> Lines;Text.ParseIntoArrayLines(Lines);
        const TCHAR* Ids[]={TEXT("ATTACK"),TEXT("DEFENSE"),TEXT("STAMINA"),TEXT("BALANCE")};
        for(const FString& Line:Lines)
        {
            TArray<FString> C;Line.ParseIntoArray(C,TEXT(","),false);
            if(C.Num()!=6)continue;
            for(int32 I=0;I<4;++I) if(C[0]==Ids[I])
            {
                bool Valid=true;int32 V[4];
                for(int32 J=0;J<4;++J) {V[J]=FCString::Atoi(*C[J+1]);Valid&=C[J+1].IsNumeric() && V[J]>=1 && V[J]<=(J==2 ? 200 : 100);}
                const double Seconds=FCString::Atod(*C[5]);
                Valid &= C[5].IsNumeric() && Seconds>0. && Seconds<=600.;
                if(Valid) {Result[I].NaturalSeconds=Seconds;Result[I].Attack=V[0];Result[I].Defense=V[1];Result[I].Life=V[2];Result[I].Move=V[3];Result[I].Valid=true;}
            }
        }
        return Result;
    }();return Data;
}
inline const FRow& Get(int32 I) {return Rows()[FMath::Clamp(I,0,3)];}
inline const TCHAR* Name(int32 I)
{
    const TCHAR* Names[]={TEXT("攻击型"),TEXT("防御型"),TEXT("持久型"),TEXT("均衡型")};
    return Names[FMath::Clamp(I,0,3)];
}
inline const FRow& GetBey(int32 Slot)
{
    // Stable pool order; fixed traits survive rematches and are never rolled per round.
    static const FRow Beys[] = {
        {90,8,100,100,170.,true}, {35,34,150,90,210.,true},
        {40,14,120,100,240.,true}, {70,18,110,95,190.,true},
        {75,14,120,100,190.,true}, {50,26,130,90,230.,true},
        {55,22,140,100,220.,true}, {55,26,130,95,210.,true}
    };
    return Beys[FMath::Clamp(Slot,0,7)];
}
inline int32 BeyType(int32 Slot) {return FMath::Clamp(Slot,0,7)%4;}
inline void ApplyRow(FBattleSimulation& S,int32 Player,int32 Index,const FRow& Row)
{
    check(Player==0 || Player==1);
    if(!Row.Valid)return;
    S.Type[Player]=static_cast<EBeyType>(FMath::Clamp(Index,0,3));
    S.Attack[Player]=Row.AttackValue();S.Defense[Player]=Row.DefenseValue();
    S.DamageReduction[Player]=Row.Defense/100.;
    S.MaxDurability[Player]=Row.Life;S.Durability[Player]=S.MaxDurability[Player];
    S.NaturalSpinSeconds[Player]=Row.SpinSeconds();
    S.SpinDecay[Player]=FMath::Loge(S.SpinStart/S.SpinStopThreshold)/Row.SpinSeconds();
    S.TypeMoveScale[Player]=Row.Move/100.;
    S.Velocity[Player]*=S.TypeMoveScale[Player];
}
inline void Apply(FBattleSimulation& S,int32 Player,int32 Index) {ApplyRow(S,Player,Index,Get(Index));}
inline void ApplyBey(FBattleSimulation& S,int32 Player,int32 Slot) {ApplyRow(S,Player,BeyType(Slot),GetBey(Slot));}
}
