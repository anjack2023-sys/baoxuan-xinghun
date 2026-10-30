#include "BattleSimulation.h"
#include "SpinPresentation.h"
#include "FeelLabTuning.h"
#include "IndustrialFeelSettings.h"
#include "StadiumObstacles.h"
#include "FeelLabTypePresets.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "Misc/AutomationTest.h"

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFeelRef60ContactTest, "Beyblade.Battle.FeelRef60Contact", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFeelRef60ContactTest::RunTest(const FString&)
{
    FBattleSimulation S;
    S.Reset();
    S.Position[0] = FVector2D(-.2, 0); S.Position[1] = FVector2D(.2, 0);
    S.Velocity[0] = FVector2D(0, 1); S.Velocity[1] = FVector2D(0, -1);
    S.Collide();
    TestTrue(TEXT("scrape removes ten percent relative tangent speed"), FMath::IsNearlyEqual(S.Velocity[0].Y - S.Velocity[1].Y, 1.8));
    TestTrue(TEXT("scrape conserves pair momentum"), (S.Velocity[0] + S.Velocity[1]).IsNearlyZero());
    TestEqual(TEXT("sliding is not another hard impact"), S.Hits, 0);
    S.Reset(); S.Position[0] = FVector2D(-.2, 0); S.Position[1] = FVector2D(.2, 0);
    S.Velocity[0] = FVector2D(2.5, 0); S.Velocity[1] = FVector2D(-2.5, 0);
    S.Collide();
    TestTrue(TEXT("hard impact spends three percent spin"), FMath::IsNearlyEqual(S.Spin[0], .97) && FMath::IsNearlyEqual(S.Spin[1], .97));
    TestTrue(TEXT("tangent candidate pinned"), FMath::IsNearlyEqual(FBattleSimulation::TangentialKick, .65));
    FBattleSimulation A;
    A.Random.Initialize(4242);
    A.ApplyLoadout(0, MakeLoadout(EBeyType::Attack)); A.ApplyLoadout(1, MakeLoadout(EBeyType::Defense));
    A.Launch();
    while (A.Running) A.Tick();
    TestTrue(TEXT("candidate ends inside the 60 second cap"), A.Frames <= FBattleSimulation::MaxFrames);
    TestTrue(TEXT("candidate has contacts"), A.Hits > 0);
    FBattleSimulation Fast, Slow;
    Fast.Reset(); Slow.Reset(); Fast.Running = Slow.Running = true;
    Fast.Velocity[0] = Slow.Velocity[0] = FVector2D(.5, 0);
    Fast.Position[1] = Slow.Position[1] = FVector2D(1, 0);
    Slow.Spin[0] = .1; Slow.SpinDecay[0] = .2;
    Fast.Tick(); Slow.Tick();
    TestTrue(TEXT("low spin loses mobility without a speed snap"), Slow.Velocity[0].Size() < Fast.Velocity[0].Size());
    for (const EBeyType Type : {EBeyType::Attack, EBeyType::Balance})
        TestTrue(TEXT("attack and balance full-spin period 0.18s"), FMath::IsNearlyEqual(VisualSpinRate(1., Type), 360. / .18));
    for (const EBeyType Type : {EBeyType::Defense, EBeyType::Stamina})
        TestTrue(TEXT("defense and stamina full-spin period 0.27s"), FMath::IsNearlyEqual(VisualSpinRate(1., Type), 360. / .27));
    TestTrue(TEXT("late slowdown preserved"), FMath::IsNearlyEqual(VisualSpinRate(.1, EBeyType::Attack), VisualSpinRate(1., EBeyType::Attack) * .1));
    TestEqual(TEXT("zero spin has zero visual rotation"), VisualSpinRate(0., EBeyType::Defense), 0.);
    TestEqual(TEXT("high spin stays level"), VisualTiltScale(.8), 0.);
    TestTrue(TEXT("low spin may wobble"), FMath::IsNearlyEqual(VisualTiltScale(.2), 1.));
    FBattleSimulation Tuned;
    Tuned.Random.Initialize(4242); Tuned.Launch();
    FeelLabTuning::Apply(Tuned);
    TestTrue(TEXT("launch points separated"), (Tuned.Position[0] - Tuned.Position[1]).Size() > 2.);
    TestTrue(TEXT("both launch points inside bowl"), Tuned.Position[0].Size() < 1.5 && Tuned.Position[1].Size() < 1.5);
    const FVector2D ToOpponent = (Tuned.Position[1] - Tuned.Position[0]).GetSafeNormal();
    TestTrue(TEXT("launch no longer aims straight at opponent"), FVector2D::DotProduct(Tuned.Velocity[0].GetSafeNormal(), ToOpponent) < .99);
    TestTrue(TEXT("90 percent maps to 4.5 metres per second"), FMath::IsNearlyEqual(Tuned.Velocity[0].Size(), FeelLabTuning::FullMoveSpeed * .90));
    TestTrue(TEXT("120 second natural spin calibration"), FMath::IsNearlyEqual(FMath::Exp(-Tuned.SpinDecay[0] * 120.), FBattleSimulation::SpinStopThreshold));
    for (const FVector2D Pair : {FVector2D(0,90), FVector2D(45,90), FVector2D(90,90), FVector2D(115,45), FVector2D(120,0)})
        TestTrue(TEXT("stage boundary continuous and calibrated"), FMath::IsNearlyEqual(MobilityProfile::SpeedPercent(Pair.X), Pair.Y));
    for (int32 Age = 1; Age <= 120; ++Age)
        TestTrue(TEXT("staged speed never rises with age"), MobilityProfile::SpeedPercent(Age) <= MobilityProfile::SpeedPercent(Age - 1));
    FBattleSimulation Coast;
    Coast.Reset(); FeelLabTuning::Apply(Coast); Coast.Running = true;
    Coast.Position[0] = FVector2D::ZeroVector; Coast.Position[1] = FVector2D(1,0);
    Coast.Velocity[0] = FVector2D(.1,0); Coast.Velocity[1] = FVector2D::ZeroVector;
    Coast.LastContactFrame[0] = 0;
    Coast.Tick();
    TestTrue(TEXT("impact grace preserves immediate slowdown"), FMath::IsNearlyEqual(Coast.Velocity[0].X, .1));
    Coast.Frames = 30; Coast.Tick();
    TestTrue(TEXT("drive recovers smoothly after impact grace"), FMath::IsNearlyEqual(Coast.Velocity[0].X, .15));
    Coast.Position[0] = FVector2D::ZeroVector; Coast.Velocity[0] = FVector2D(4.5,0);
    Coast.Spin[0] = .2; Coast.Frames = 90 * 60 - 1; Coast.Tick();
    TestTrue(TEXT("ninety seconds keeps full base despite spin wear"), FMath::IsNearlyEqual(Coast.MobilityFactor[0], 1.));
    TestTrue(TEXT("actual quiet movement stays at ninety"), FMath::IsNearlyEqual(Coast.Velocity[0].X, 4.5));
    Coast.Position[0] = FVector2D::ZeroVector; Coast.Frames = 115 * 60 - 1; Coast.Tick();
    TestTrue(TEXT("last five begins at half base speed"), FMath::IsNearlyEqual(Coast.Velocity[0].X, 2.25));
    Coast.Position[0] = FVector2D::ZeroVector; Coast.Frames = 120 * 60 - 1; Coast.Tick();
    TestTrue(TEXT("end of profile reaches zero movement"), Coast.Velocity[0].IsNearlyZero());
    TestEqual(TEXT("lab cap is two minutes"), Tuned.FrameLimit, 7200);
    FBattleSimulation Wall;
    Wall.Reset(); Wall.bLowWall = true; Wall.Running = true;
    Wall.Position[0] = FVector2D(1.925,0); Wall.Position[1] = FVector2D(-1,0); Wall.Velocity[0] = FVector2D(2,0);
    Wall.Tick();
    TestTrue(TEXT("ordinary wall hit reflects inward"), Wall.Velocity[0].X < 0);
    TestTrue(TEXT("wall keeps centre within visible inner face"), Wall.Position[0].Size() <= Wall.WallContactRadius + 1.e-6);
    TestEqual(TEXT("wall contact counted"), Wall.WallHits, 1);
    TestEqual(TEXT("wall hit is not a top-top hit"), Wall.Hits, 0);
    Wall.Reset(); Wall.Running = true; Wall.Position[0] = FVector2D(1.925,0); Wall.Position[1] = FVector2D(-1,0); Wall.Velocity[0] = FVector2D(6,0); Wall.LastBeyHitFrame=Wall.Frames;
    Wall.Tick();
    TestTrue(TEXT("strong hits can still clear low wall"), Wall.Position[0].Size() > Wall.WallContactRadius);
    while (Tuned.Running) Tuned.Tick();
    AddInfo(FString::Printf(TEXT("120s/hold90%% seed4242: %.3fs %d hits %s"), Tuned.Frames * Tuned.Step, Tuned.Hits, *Tuned.Reason));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFeelWeightTest, "Beyblade.Battle.FeelWeight", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFeelWeightTest::RunTest(const FString&)
{
    TestEqual(TEXT("lower clamp"), FeelLabTuning::MassForLevel(-1), .02);
    TestEqual(TEXT("neutral level"), FeelLabTuning::MassForLevel(50), 1.);
    TestEqual(TEXT("upper clamp"), FeelLabTuning::MassForLevel(101), 2.);
    auto Impact = [](double M0, double M1, bool Enabled)
    {
        FBattleSimulation S; S.Reset(); S.bWeightCollision = Enabled;
        S.Mass[0] = M0; S.Mass[1] = M1;
        S.Position[0] = FVector2D(-.2,0); S.Position[1] = FVector2D(.2,0);
        S.Velocity[0] = FVector2D(2,0); S.Velocity[1] = FVector2D(-2,0);
        S.Collide(); return S;
    };
    const auto Base = Impact(1,1,false), Equal = Impact(1,1,true);
    TestTrue(TEXT("equal weight preserves collision"), Base.Velocity[0].Equals(Equal.Velocity[0]));
    const auto Heavy = Impact(2,1,true), Swapped = Impact(1,2,true);
    TestTrue(TEXT("heavy top changes speed less"), (Heavy.Velocity[0] - FVector2D(2,0)).Size() < (Heavy.Velocity[1] - FVector2D(-2,0)).Size());
    TestTrue(TEXT("mass swap mirrors response"), Heavy.Velocity[0].Equals(-Swapped.Velocity[1]));
    TestTrue(TEXT("pair momentum conserved for symmetric attack"), (Heavy.Velocity[0]*2. + Heavy.Velocity[1]).Equals(FVector2D(2,0)));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFeelRingoutControlTest, "Beyblade.Battle.FeelRingoutControl", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFeelRingoutControlTest::RunTest(const FString&)
{
    auto WallStep = [](double Strength) {
        FBattleSimulation S; S.Reset(); S.bLowWall=true; S.Running=true; S.RingoutStrength=Strength;
        S.Position[0]=FVector2D(1.925,0); S.Position[1]=FVector2D(-1,0);
        S.Velocity[0]=FVector2D(5,0); S.LastBeyHitFrame=S.Frames; S.Tick(); return S;
    };
    const auto Old=WallStep(1.), Reduced=WallStep(.5), Off=WallStep(0.);
    TestTrue(TEXT("full strength keeps existing vault"), Old.Position[0].Size()>Old.WallContactRadius);
    TestTrue(TEXT("half strength catches moderate wall hit"), Reduced.Position[0].Size()<=Reduced.WallContactRadius+1.e-6);
    TestTrue(TEXT("zero strength catches wall hit"), Off.Velocity[0].X<0.);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFeelSpeedControlTest,"Beyblade.Battle.FeelSpeedControl",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FFeelSpeedControlTest::RunTest(const FString&)
{
    TestEqual(TEXT("minimum clamp"),FeelLabTuning::ClampMoveLevel(-10),10);
    TestEqual(TEXT("maximum clamp"),FeelLabTuning::ClampMoveLevel(999),200);
    TestTrue(TEXT("100 is five metres per second"),FMath::IsNearlyEqual(FeelLabTuning::SpeedForLevel(100),5.));
    TestTrue(TEXT("120 exceeds former percentage scale"),FMath::IsNearlyEqual(FeelLabTuning::SpeedForLevel(120),6.));
    for(int32 Level:{10,90,100,120,200})
    {
        FBattleSimulation S;S.Reset();FeelLabTuning::Apply(S,Level);
        TestTrue(TEXT("both launch speeds follow selection"),FMath::IsNearlyEqual(S.Velocity[0].Size(),FeelLabTuning::SpeedForLevel(Level)) && FMath::IsNearlyEqual(S.Velocity[1].Size(),S.Velocity[0].Size()));
    }
    FBattleSimulation S;S.Reset();FeelLabTuning::Apply(S);S.Frames=600;S.Spin[0]=.6;
    const FVector2D V=S.Velocity[0];FeelLabTuning::SetMoveLevel(S,120);
    TestTrue(TEXT("live speed scales proportionally"),S.Velocity[0].Equals(V*(120./90.)));
    TestEqual(TEXT("live setting does not reset match age"),S.Frames,600);
    TestEqual(TEXT("live setting preserves spin life"),S.Spin[0],.6);
    S.Position[0]=FVector2D::ZeroVector;S.Position[1]=FVector2D(1,0);
    S.Velocity[0]=FVector2D(6,0);S.Velocity[1]=FVector2D::ZeroVector;
    S.Frames=115*60-1;S.Running=true;S.Tick();
    TestTrue(TEXT("115 seconds remains half of selected speed"),FMath::IsNearlyEqual(S.Velocity[0].X,3.));
    S.Position[0]=FVector2D::ZeroVector;S.Position[1]=FVector2D(1,0);S.Frames=120*60-1;S.Tick();
    TestTrue(TEXT("120 seconds still reaches zero"),S.Velocity[0].IsNearlyZero());
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFeelTypePanelTest,"Beyblade.Battle.FeelTypePanel",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FFeelTypePanelTest::RunTest(const FString&)
{
    const int32 Points[4][4]={{82,11,110,100},{42,30,140,90},{47,18,130,100},{62,22,120,95}};
    for(int32 I=0;I<4;++I)
    {
        const auto& R=FeelLabTypes::Get(I);TestTrue(TEXT("preset CSV valid"),R.Valid);
        TestEqual(TEXT("attack panel matches user"),R.Attack,Points[I][0]);TestEqual(TEXT("defense panel matches user"),R.Defense,Points[I][1]);
        TestEqual(TEXT("life panel matches user"),R.Life,Points[I][2]);TestEqual(TEXT("move panel matches user"),R.Move,Points[I][3]);
        TestTrue(TEXT("attack inverse round trip"),FMath::RoundToInt(50.+(R.AttackValue()-1.)*100.)==R.Attack);
        const double ExpectedSeconds[]={180.,220.,230.,200.};
        TestEqual(TEXT("natural duration preset"),R.SpinSeconds(),ExpectedSeconds[I]);
        FBattleSimulation S;S.Reset();FeelLabTuning::Apply(S,100);S.Mass[0]=.7;S.FrameLimit=360*60;FeelLabTypes::Apply(S,0,I);
        TestTrue(TEXT("move is actual launch speed"),FMath::IsNearlyEqual(S.Velocity[0].Size(),5.*R.Move/100.));
        TestEqual(TEXT("type applies"),static_cast<int32>(S.Type[0]),I);
        TestEqual(TEXT("weight remains independent"),S.Mass[0],.7);
        TestTrue(TEXT("spin duration uses decay"),FMath::IsNearlyEqual(FMath::Exp(-S.SpinDecay[0]*R.SpinSeconds()),S.SpinStopThreshold));
        S.Frames=FMath::RoundToInt(R.SpinSeconds()*.75*60)-1;S.Running=true;S.Position[0]=FVector2D::ZeroVector;S.Position[1]=FVector2D(1.5,0);S.Velocity[0]=FVector2D(5.*R.Move/100.,0);S.Velocity[1]=FVector2D::ZeroVector;
        S.Tick();TestTrue(TEXT("75 percent lifetime still full speed"),FMath::IsNearlyEqual(S.MobilityFactor[0],1.));
        S.Frames=FMath::RoundToInt(R.SpinSeconds()*60)-1;S.Position[0]=FVector2D::ZeroVector;S.Position[1]=FVector2D(1.5,0);S.Tick();
        TestTrue(TEXT("movement reaches zero at type lifetime"),S.Velocity[0].IsNearlyZero());
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FObstacleSweepTest,"Beyblade.Battle.ObstacleSweep",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FObstacleSweepTest::RunTest(const FString&)
{
    FBattleSimulation S;S.Reset();S.Running=true;
    S.Position[0]=FVector2D(-.5,0);S.Position[1]=FVector2D(-1.5,0);S.Velocity[0]=FVector2D(60,0);
    S.SweepObstacle=[](const FVector2D& A,const FVector2D& B,FVector2D& P,FVector2D& N) {
        const double Face=-FBattleSimulation::Radius;
        if(A.X<Face && B.X>=Face) {P=FVector2D(Face-.01,A.Y);N=FVector2D(-1,0);return true;}
        return false;
    };
    S.Tick();
    TestTrue(TEXT("fast motion cannot cross thin obstacle"),S.Position[0].X<-.22);
    TestTrue(TEXT("impact reflects motion"),S.Velocity[0].X<0.);
    TestTrue(TEXT("obstacle counts as wall for quiet-spin skill"),S.bWallContact[0]);
    TestEqual(TEXT("one obstacle contact"),S.WallHits,1);
    S.SweepObstacle=nullptr;S.Position[0]=FVector2D(3.,0);S.Velocity[0]=FVector2D::ZeroVector;S.Tick();
    TestEqual(TEXT("obstacle fix retains ringout"),S.Reason,FString(TEXT("ringout")));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FIndustrialSettingsTest,"Beyblade.Battle.IndustrialSettings",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FIndustrialSettingsTest::RunTest(const FString&)
{
    FIndustrialFeelSettings A;
    TestEqual(TEXT("requested move default"),A.Move,120);TestEqual(TEXT("requested ringout default"),A.Ringout,60);
    const FString File=FPaths::ProjectSavedDir()/TEXT("Automation/IndustrialSettings-test.ini");
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(File),true);
    A.Move=145;A.Ringout=75;TestTrue(TEXT("saves settings"),A.Save(File));
    FIndustrialFeelSettings B;B.Load(File);TestEqual(TEXT("speed survives reload"),B.Move,145);TestEqual(TEXT("ringout survives reload"),B.Ringout,75);
    A.Move=999;A.Ringout=-10;A.Clamp();TestEqual(TEXT("speed bounded"),A.Move,200);TestEqual(TEXT("ringout bounded"),A.Ringout,0);
    IFileManager::Get().Delete(*File);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArenaScaleTest,"Beyblade.Battle.ArenaScale",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FArenaScaleTest::RunTest(const FString&)
{
    FBattleSimulation S;S.Reset();S.ArenaScale=.8;S.Running=true;
    S.Position[0]=FVector2D(1.9,0);S.Position[1]=FVector2D::ZeroVector;S.Tick();
    TestEqual(TEXT("smaller arena shrinks actual ringout boundary"),S.Reason,FString(TEXT("ringout")));
    S.Reset();S.bLowWall=true;S.RingoutStrength=0.;S.Running=true;
    S.Position[0]=FVector2D(1.6,0);S.Position[1]=FVector2D::ZeroVector;S.Velocity[0]=FVector2D(.3,0);S.Tick();
    TestTrue(TEXT("low wall scales with rendered arena"),FMath::IsNearlyEqual(S.Position[0].Size(),S.WallContactRadius*.8));
    TestEqual(TEXT("top radius stays original size"),S.Radius,.22);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStadiumFootprintTest,"Beyblade.Battle.StadiumObstacleFootprints",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FStadiumFootprintTest::RunTest(const FString&)
{
    TestEqual(TEXT("actual stadium has three block footprints"),StadiumObstacles::Polygons().Num(),3);
    for (double Scale:{1.,.8}) for (const auto& Polygon:StadiumObstacles::Polygons())
    {
        FVector2D Centre=FVector2D::ZeroVector;
        for(const auto& P:Polygon) Centre+=P;
        Centre*=Scale/Polygon.Num();
        const FVector2D Direction=Centre.GetSafeNormal();
        FVector2D Contact,Normal,Dummy,N;
        TestTrue(TEXT("all actual blocks stop a long fast sweep"),StadiumObstacles::Sweep(FVector2D::ZeroVector,Direction*10.,Scale,.22,Contact,Normal));
        TestTrue(TEXT("contact opposes incoming direction"),FVector2D::DotProduct(Direction,Normal)<0.);
        TestFalse(TEXT("resolved body is outside footprint"),StadiumObstacles::Sweep(Contact,Contact,Scale,.22,Dummy,N));
        TestFalse(TEXT("moving away is free"),StadiumObstacles::Sweep(Contact,Contact+Normal*.1,Scale,.22,Dummy,N));
        const FVector2D Penetrating=Contact-Normal*.04;
        TestTrue(TEXT("existing overlap is recovered"),StadiumObstacles::Sweep(Penetrating,Penetrating,Scale,.22,Dummy,N));
        FVector2D Check,CheckNormal;
        TestFalse(TEXT("recovery clears overlap"),StadiumObstacles::Sweep(Dummy,Dummy,Scale,.22,Check,CheckNormal));
        FBattleSimulation S;S.Reset();S.ArenaScale=Scale;S.Running=true;
        S.SweepObstacle=[Scale](const FVector2D& A,const FVector2D& B,FVector2D& P,FVector2D& N) {return StadiumObstacles::Sweep(A,B,Scale,.22,P,N);};
        S.Position[0]=Contact;S.Position[1]=Contact+Normal*.30;
        S.Tick();
        TestFalse(TEXT("pair separation cannot push a top into block"),StadiumObstacles::Sweep(S.Position[0],S.Position[0],Scale,.22,Check,CheckNormal));
    }
    FVector2D P,N;
    TestFalse(TEXT("centre bowl remains free"),StadiumObstacles::Sweep(FVector2D(-.3,0),FVector2D(.3,0),.8,.22,P,N));
    return true;
}
#endif
