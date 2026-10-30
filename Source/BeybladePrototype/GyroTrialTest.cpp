#include "BattleSimulation.h"
#include "Misc/AutomationTest.h"

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGyroTrialTest, "Beyblade.Battle.GyroTrial", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FGyroTrialTest::RunTest(const FString&)
{
    FBattleSimulation S;
    S.Reset(); S.bGyroTrial=true; S.Running=true;
    S.Position[0]=FVector2D(-.21,0); S.Position[1]=FVector2D(.21,0);
    S.Velocity[0]=FVector2D(2,0); S.Velocity[1]=FVector2D(-2,0);
    S.Spin[0]=1.; S.Spin[1]=.2;
    S.Collide();
    TestTrue(TEXT("impact tilts tops"), S.GyroTilt[0].Size()>0.);
    TestTrue(TEXT("low spin is less stable"), S.GyroTilt[1].Size()>S.GyroTilt[0].Size());
    S.Position[0]=FVector2D(-.6,0); S.Position[1]=FVector2D(.6,0);
    S.Velocity[0]=S.Velocity[1]=FVector2D::ZeroVector;
    S.GyroTilt[0]=S.GyroTilt[1]=FVector2D(10,0);
    for (int32 I=0; I<60; ++I) S.Tick();
    TestTrue(TEXT("high spin recovers faster"), S.GyroTilt[0].Size()<S.GyroTilt[1].Size());
    S.Reset();
    TestTrue(TEXT("reset clears tilt"), S.GyroTilt[0].IsNearlyZero() && S.GyroTilt[1].IsNearlyZero());
    FBattleSimulation Control; Control.Reset(); Control.Position[0]=FVector2D(-.21,0); Control.Position[1]=FVector2D(.21,0);
    Control.Velocity[0]=FVector2D(2,0); Control.Velocity[1]=FVector2D(-2,0); Control.Collide();
    TestTrue(TEXT("default mode has no gyro effect"), Control.GyroTilt[0].IsNearlyZero());
    for (const FVector2D Pair : {FVector2D(30.,1.), FVector2D(15.,.5), FVector2D(5.,.15), FVector2D(1.,.03), FVector2D(0.,0.)})
        TestTrue(TEXT("remaining-time speed matches target"), FMath::IsNearlyEqual(MobilityProfile::GyroTrialFactor(Pair.X),Pair.Y,1.e-6));
    const double Decay=FMath::Loge(1. / FBattleSimulation::SpinStopThreshold) / 210.;
    for (const double Remaining : {30.,15.,5.,1.,0.})
    {
        const double Spin=FBattleSimulation::SpinStopThreshold * FMath::Exp(Decay*Remaining);
        TestTrue(TEXT("remaining time follows actual spin including impacts"), FMath::IsNearlyEqual(MobilityProfile::RemainingSpinSeconds(Spin,FBattleSimulation::SpinStopThreshold,Decay),Remaining,1.e-6));
    }
    FBattleSimulation Late;
    Late.Reset(); Late.bGyroTrial=true; Late.bStagedMobility=true; Late.Running=true;
    Late.SpinDecay[0]=Late.SpinDecay[1]=Decay;
    Late.Spin[0]=FBattleSimulation::SpinStopThreshold * FMath::Exp(Decay*15.);
    Late.Spin[1]=1.; Late.Position[0]=FVector2D(-.6,0); Late.Position[1]=FVector2D(.6,0);
    Late.Velocity[0]=FVector2D(1,0); Late.Velocity[1]=FVector2D(-1,0);
    Late.Tick();
    TestTrue(TEXT("simulation uses actual remaining spin for mobility"), FMath::IsNearlyEqual(Late.MobilityFactor[0],.5,.002));
    TestTrue(TEXT("the other fresh top stays at full mobility"), FMath::IsNearlyEqual(Late.MobilityFactor[1],1.,.002));
    FBattleSimulation Impact;
    Impact.Reset(); Impact.bGyroTrial=true; Impact.bBalanceV1=true; Impact.BaseMoveSpeed=4.;
    Impact.Position[0]=FVector2D(-.21,0); Impact.Position[1]=FVector2D(.21,0);
    Impact.Velocity[0]=FVector2D(4,0); Impact.Velocity[1]=FVector2D(-4,0);
    Impact.Collide();
    const double FastAttack=Impact.ImpactAttackMultiplier[0], FastWear=100.-Impact.Durability[1];
    TestTrue(TEXT("full speed and spin increase opening attack moderately"), FMath::IsNearlyEqual(FastAttack,1.15,.001));
    Impact.Reset(); Impact.bGyroTrial=true; Impact.bBalanceV1=true; Impact.BaseMoveSpeed=4.;
    Impact.Position[0]=FVector2D(-.21,0); Impact.Position[1]=FVector2D(.21,0);
    Impact.Velocity[0]=FVector2D(1,0); Impact.Velocity[1]=FVector2D(-1,0);
    Impact.Spin[0]=Impact.Spin[1]=.25; Impact.Collide();
    TestTrue(TEXT("slower spin and movement reduce attack"), Impact.ImpactAttackMultiplier[0]<FastAttack);
    TestTrue(TEXT("slow impact causes less durability damage"), 100.-Impact.Durability[1]<FastWear);
    FBattleSimulation Push, NoPush;
    Push.Reset(); Push.bGyroPush=true; Push.Running=true;
    Push.Position[0]=FVector2D(-.6,0); Push.Position[1]=FVector2D(.6,0);
    Push.Velocity[0]=FVector2D(1,0); Push.GyroTilt[0]=FVector2D(10,0);
    NoPush=Push; NoPush.bGyroPush=false;
    Push.Tick(); NoPush.Tick();
    const FVector2D ExpectedDelta=Push.GyroTilt[0]*(.015*FBattleSimulation::Step)*FMath::Exp(-.12*FBattleSimulation::Step);
    TestTrue(TEXT("unified push restores original coefficient"), (Push.Velocity[0]-NoPush.Velocity[0]).Equals(ExpectedDelta,1.e-6));
    TestTrue(TEXT("push does not enable trial decay or attack scaling"), !Push.bGyroTrial && FMath::IsNearlyEqual(Push.ImpactAttackMultiplier[0],1.));
    Push.Reset(); Push.bGyroPush=true;
    Push.Position[0]=FVector2D(-.21,0); Push.Position[1]=FVector2D(.21,0);
    Push.Velocity[0]=FVector2D(2,0); Push.Velocity[1]=FVector2D(-2,0);
    Push.Collide();
    TestTrue(TEXT("unified collision supplies tilt for push"), !Push.GyroTilt[0].IsNearlyZero());
    Push.Reset();
    TestTrue(TEXT("new bout clears push tilt"), Push.GyroTilt[0].IsNearlyZero());
    return true;
}
#endif
