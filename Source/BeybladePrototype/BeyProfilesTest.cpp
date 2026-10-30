#include "FeelLabTypePresets.h"
#include "FeelLabTuning.h"
#include "Misc/AutomationTest.h"
#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBeyProfilesTest,"Beyblade.Battle.IndividualProfiles",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FBeyProfilesTest::RunTest(const FString&)
{
    const double MinS[]={170,210,220,190},MaxS[]={190,230,240,210};
    const int32 MinHp[]={100,130,120,110},MaxHp[]={120,150,140,130};
    const double MinA[]={1.25,.85,.90,1.05},MaxA[]={1.40,1.,1.05,1.20};
    const int32 MinD[]={8,26,14,18},MaxD[]={14,34,22,26};
    for(int32 Slot=0;Slot<8;++Slot)
    {
        const auto& R=FeelLabTypes::GetBey(Slot);const int32 T=FeelLabTypes::BeyType(Slot);
        TestTrue(TEXT("duration in type range"),R.NaturalSeconds>=MinS[T] && R.NaturalSeconds<=MaxS[T]);
        TestTrue(TEXT("hp in type range"),R.Life>=MinHp[T] && R.Life<=MaxHp[T]);
        TestTrue(TEXT("attack in type range"),R.AttackValue()>=MinA[T]-1.e-9 && R.AttackValue()<=MaxA[T]+1.e-9);
        TestTrue(TEXT("reduction in type range"),R.Defense>=MinD[T] && R.Defense<=MaxD[T]);
        FBattleSimulation S;S.Reset();FeelLabTuning::Apply(S,110);FeelLabTypes::ApplyBey(S,0,Slot);
        TestEqual(TEXT("selection reaches simulation"),S.NaturalSpinSeconds[0],R.NaturalSeconds);
        TestEqual(TEXT("selection hp reaches simulation"),S.MaxDurability[0],double(R.Life));
        S.Durability[0]=0;S.Reset();TestEqual(TEXT("rematch preserves unique max"),S.Durability[0],double(R.Life));
        const double Before=S.Durability[0];S.LastClosing=S.KickReferenceSpeed;S.Attack[1]=1.;S.ApplyCollisionWear();
        TestTrue(TEXT("direct mitigation applied to base damage"),FMath::IsNearlyEqual(S.Durability[0],Before-S.BalanceWearBase*(1-R.Defense/100.)));
        S.Position[0]=FVector2D(-.5,0);S.Position[1]=FVector2D(.5,0);S.Velocity[0]=S.Velocity[1]=FVector2D::ZeroVector;
        FeelLabTypes::ApplyBey(S,1,Slot);S.bStagedMobility=false;S.FrameLimit=360*60;S.Running=true;
        while(S.Running) S.Tick();
        TestTrue(TEXT("measured quiet duration matches profile"),FMath::Abs(S.Frames*S.Step-R.NaturalSeconds)<=S.Step+1.e-8);
        const auto& Other=FeelLabTypes::GetBey((Slot+4)%8);
        TestTrue(TEXT("same type offers actual tradeoffs"),R.Life!=Other.Life && R.NaturalSeconds!=Other.NaturalSeconds && R.Attack!=Other.Attack);
    }
    FBattleSimulation Trap;Trap.Reset();FeelLabTuning::Apply(Trap);Trap.bEnableBurstTrapXtr=true;Trap.bStagedMobility=false;Trap.Running=true;
    for(int32 I=0;I<120;++I)
    {
        Trap.Position[0]=FVector2D(1.8,0);Trap.Position[1]=FVector2D::ZeroVector;
        Trap.Velocity[0]=Trap.Velocity[1]=FVector2D::ZeroVector;Trap.Tick();
    }
    TestFalse(TEXT("new balance never enables legacy trap spin penalty"),Trap.bTrapPenalizing[0]);
    TestTrue(TEXT("rim dwell spends only natural spin"),FMath::IsNearlyEqual(Trap.Spin[0],FMath::Exp(-Trap.SpinDecay[0]*2.),1.e-6));
    return true;
}
#endif
