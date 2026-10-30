#include "BoutPresentation.h"
#include "LobbyClickUI.h"
#include "FeelLabTuning.h"
#include "Misc/AutomationTest.h"
#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBoutLaunchTest,"Beyblade.Battle.LaunchControls",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FBoutLaunchTest::RunTest(const FString&)
{
    FLaunchSetup Setup;Setup.Adjust(999,-999);TestEqual(TEXT("angle upper clamp"),Setup.Angle,45);TestEqual(TEXT("power lower clamp"),Setup.Power,70);
    Setup.Adjust(-999,999);TestEqual(TEXT("angle lower clamp"),Setup.Angle,-45);TestEqual(TEXT("power upper clamp"),Setup.Power,120);
    FBattleSimulation S;S.Reset();S.Velocity[0]=FVector2D(5,0);S.Velocity[1]=FVector2D(-4,1);const auto Foe=S.Velocity[1];
    Setup.Angle=30;Setup.Power=110;Setup.Apply(S);
    TestTrue(TEXT("launch power controls initial speed"),FMath::IsNearlyEqual(S.Velocity[0].Size(),5.5));
    TestTrue(TEXT("launch angle controls heading"),S.Velocity[0].Y>2.7);
    TestTrue(TEXT("player setup does not change opponent"),S.Velocity[1].Equals(Foe));
    TestEqual(TEXT("launch does not change spin lifetime"),S.Spin[0],1.);
    for(const FVector2D View:{FVector2D(1280,720),FVector2D(2400,1080)})
        for(int32 I=0;I<4;++I){const FVector2D P=FLaunchSetup::Button(I)+FVector2D(40,35);TestEqual(TEXT("phone button round trip"),FLaunchSetup::Hit(FLobbyClickUI::FromViewport(FLobbyClickUI::ToViewport(P,View),View)),I);}
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBoutTacticsTest,"Beyblade.Battle.TypeSteering",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FBoutTacticsTest::RunTest(const FString&)
{
    FVector2D Heading[4];
    for(int32 I=0;I<4;++I)
    {
        FBattleSimulation S;S.Reset();S.bTacticalSteering=true;S.Type[0]=static_cast<EBeyType>(I);S.Position[0]=FVector2D(.7,.5);S.Position[1]=FVector2D(-.7,.2);S.Velocity[0]=FVector2D(0,5);S.Frames=60;
        for(int32 N=0;N<90;++N)S.SteerType(0);
        TestTrue(TEXT("steering conserves speed"),FMath::IsNearlyEqual(S.Velocity[0].Size(),5.,1.e-6));Heading[I]=S.Velocity[0];
        S.LastContactFrame[0]=S.Frames;const auto V=S.Velocity[0];S.SteerType(0);TestTrue(TEXT("collision rebound remains free"),S.Velocity[0].Equals(V));
    }
    for(int32 I=1;I<4;++I)TestFalse(TEXT("types produce different headings"),Heading[0].Equals(Heading[I],.01));
    FBattleSimulation S;S.Reset();S.Velocity[0]=FVector2D(1,2);const auto V=S.Velocity[0];S.SteerType(0);TestTrue(TEXT("legacy simulation unchanged by default"),V.Equals(S.Velocity[0]));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBoutRecapTest,"Beyblade.Battle.FactualRecap",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FBoutRecapTest::RunTest(const FString&)
{
    FBattleSimulation S;S.Reset();S.Reason=TEXT("ringout");S.Winner=0;S.Frames=60;
    TestFalse(TEXT("no fabricated recent hit"),ExplainBout(S).Contains(TEXT("0.5")));
    S.LastBeyHitFrame=55;TestTrue(TEXT("recent hit reported from telemetry"),ExplainBout(S).Contains(TEXT("0.5")));
    S.Reason=TEXT("timeout");S.Winner=1;S.TimeoutMomentum[0]=1;S.TimeoutMomentum[1]=2;
    TestTrue(TEXT("timeout can have a winner"),ExplainBout(S).Contains(TEXT("较高者获胜")));
    S.Winner=-1;TestTrue(TEXT("timeout draw explained separately"),ExplainBout(S).Contains(TEXT("判平局")));
    S.Reason=TEXT("burst");S.Winner=1;TestTrue(TEXT("burst explanation refers to durability"),ExplainBout(S).Contains(TEXT("耐久")));
    S.Reset();TestEqual(TEXT("recap telemetry resets every bout"),S.LastBeyHitFrame,-10000);
    return true;
}
#endif
