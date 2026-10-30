#include "BattleSimulation.h"
#include "FeelLabTuning.h"
#include "FeelLabTypePresets.h"
#include "Misc/AutomationTest.h"
#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FOpeningRingoutTest,"Beyblade.Battle.NoUnforcedOpeningRingout",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FOpeningRingoutTest::RunTest(const FString&)
{
    for (int32 Type=0;Type<4;++Type)
    for (int32 Move:{115,120,200})
    for (int32 Seed:{25383,27579,4242})
    {
        FBattleSimulation S;S.Random.Initialize(Seed);S.Launch();FeelLabTuning::Apply(S,Move);
        FeelLabTypes::Apply(S,0,Type);FeelLabTypes::Apply(S,1,1);
        S.bWeightCollision=true;S.bTacticalSteering=true;S.RingoutStrength=.6;
        for(int32 I=0;I<60 && S.Running;++I)
        {
            S.Tick();
            if(S.Hits==0) TestFalse(TEXT("no ringout before first bey collision"),S.Reason==TEXT("ringout"));
        }
    }
    auto WallStep=[](int32 LastImpact,double Strength) {
        FBattleSimulation S;S.Reset();S.Running=true;S.bLowWall=true;S.RingoutStrength=Strength;
        S.Frames=100;S.LastBeyHitFrame=LastImpact;S.Position[0]=FVector2D(1.925,0);S.Position[1]=FVector2D(-1,0);
        S.Velocity[0]=FVector2D(10,0);S.Tick();return S;
    };
    TestTrue(TEXT("high cruise reflects"),WallStep(-10000,1.).Velocity[0].X<0.);
    TestTrue(TEXT("old impact cannot authorize cruising out"),WallStep(0,1.).Velocity[0].X<0.);
    const auto Hit=WallStep(100,1.);
    TestTrue(TEXT("fresh strong impact still vaults"),Hit.Position[0].Size()>Hit.WallContactRadius);
    TestTrue(TEXT("ringout off still catches a fresh impact"),WallStep(100,0.).Velocity[0].X<0.);
    return true;
}
#endif

#include "BattleSimulation.h"
#include "Misc/AutomationTest.h"
#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStarCrownRimTest, "Beyblade.Arena.FourLowWalls", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FStarCrownRimTest::RunTest(const FString&)
{
    auto Shot=[](double Degrees, bool Fresh, bool Arena) {
        FBattleSimulation S; S.Reset(); S.Running=true; S.bLowWall=true; S.bStarCrownRim=Arena;
        S.ArenaScale=.8; S.RingoutStrength=1.; S.Frames=100; S.LastBeyHitFrame=Fresh?100:-10000;
        const FVector2D N(FMath::Cos(FMath::DegreesToRadians(Degrees)),FMath::Sin(FMath::DegreesToRadians(Degrees)));
        S.Position[0]=N*(S.WallContactRadius*.8-.004); S.Position[1]=-N*.5; S.Velocity[0]=N*10.;
        S.Tick(); return FVector2D::DotProduct(S.Velocity[0],N);
    };
    for(int32 I=0;I<4;++I)
    {
        const double Angle=45.+I*90.;
        TestTrue(TEXT("strong collision can clear each low wall"), Shot(Angle,true,true)>0.);
        TestTrue(TEXT("normal cruising is retained by low lip"), Shot(Angle,false,true)<0.);
        TestTrue(TEXT("high wall reflects even a strong impact"), Shot(I*90.,true,true)<0.);
        TestTrue(TEXT("old arena wall behavior unchanged"), Shot(I*90.,true,false)>0.);
    }
    TestTrue(TEXT("gap center"),StarCrownRim::IsLowSection(FVector2D(1,1)));
    TestFalse(TEXT("side launch position keeps high wall"),StarCrownRim::IsLowSection(FVector2D(1,0)));
    for(int32 I=0;I<6;++I)
    {
        const double Angle=PI/2.+I*PI/3.;
        const FVector2D N(FMath::Cos(Angle),FMath::Sin(Angle));
        TestTrue(TEXT("all six visible trap centers slow tops"),StarCrownRim::InSlowTrap(N*StarCrownRim::TrapRingRadius,0.));
        TestFalse(TEXT("spaces between traps remain open"),StarCrownRim::InSlowTrap(N.GetRotated(30.)*StarCrownRim::TrapRingRadius,0.));
    }
    TestFalse(TEXT("bowl center is not a trap"),StarCrownRim::InSlowTrap(FVector2D::ZeroVector,FBattleSimulation::Radius));
    FBattleSimulation Penetration;Penetration.Reset();Penetration.bLowWall=true;Penetration.bStarCrownRim=true;
    Penetration.Position[0]=FVector2D(1.55,0);Penetration.Velocity[0]=FVector2D(2,0);
    Penetration.ResolveRim(0,Penetration.Position[0]);
    TestTrue(TEXT("entire top clears physical wall, not just its center"),Penetration.Position[0].Size()+FBattleSimulation::Radius<StarCrownRim::InnerWallRadius);
    TestTrue(TEXT("penetrating top rebounds into bowl"),Penetration.Velocity[0].X<0.);
    Penetration.Position[0]=FVector2D(1.55,0);Penetration.Velocity[0]=FVector2D(-2,0);
    Penetration.ResolveRim(0,Penetration.Position[0]);
    TestTrue(TEXT("already inward motion stays inward during depenetration"),Penetration.Velocity[0].X<0.);
    FBattleSimulation Trapped,Free;
    Trapped.Reset();Trapped.Running=true;Trapped.bStarCrownRim=true;
    Trapped.Position[0]=FVector2D(0,StarCrownRim::TrapRingRadius);Trapped.Position[1]=FVector2D(-.5,0);
    Trapped.Velocity[0]=FVector2D(2,0);Free=Trapped;Free.bStarCrownRim=false;
    Trapped.Tick();Free.Tick();
    TestTrue(TEXT("trap removes movement speed"),Trapped.Velocity[0].Size()<Free.Velocity[0].Size());
    for (const bool Push : {false,true})
    {
        FBattleSimulation S; S.Reset(); S.Running=true; S.bLowWall=true; S.bStarCrownRim=true;
        S.bGyroPush=Push; S.ArenaScale=.8;
        S.Position[0]=FVector2D(S.WallContactRadius*.8-.0001,0); S.Position[1]=FVector2D(-.5,0);
        S.Velocity[0]=FVector2D(.05,3.); S.GyroTilt[0]=FVector2D(15,0);
        S.Tick();
        const FVector2D N=S.Position[0].GetSafeNormal();
        TestTrue(TEXT("grazing wall contact departs inward with or without gyro push"),
            -FVector2D::DotProduct(S.Velocity[0],N)>=S.Velocity[0].Size()*.249);
        TestTrue(TEXT("wall release adds no translational speed"),S.Velocity[0].Size()<3.001);
        double MinRadius=S.Position[0].Size();
        for(int32 Frame=0;Frame<60 && S.Running;++Frame)
        {
            S.Tick();MinRadius=FMath::Min(MinRadius,S.Position[0].Size());
        }
        TestTrue(TEXT("top actually leaves wall instead of staying clamped"),MinRadius<S.WallContactRadius*.8-.03);
    }
    return true;
}
#endif
