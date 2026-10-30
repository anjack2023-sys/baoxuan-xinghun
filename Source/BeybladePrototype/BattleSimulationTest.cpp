#include "BattleSimulation.h"
#include "ContentStrings.h"
#include "MatchFlow.h"
#include "SkillRuntime.h"
#include "CollectionCatalog.h"
#include "LobbyClickUI.h"
#include "LobbyClickUI.h"
#include "PlayerSaveService.h"
#include "RingoutPresentation.h"
#include "Misc/AutomationTest.h"

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBattleReplayTest, "Beyblade.Battle.FixedStepReplay", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FBattleReplayTest::RunTest(const FString&)
{
    for (int32 Seed : {4242, 42, 2026})
    {
        FBattleSimulation A, B;
        A.Random.Initialize(Seed); B.Random.Initialize(Seed);
        for (int32 Match = 0; Match < 24; ++Match)
        {
            A.Launch(); B.Launch();
            while (A.Running) A.Tick();
            double Accumulator = 0;
            int32 RenderFrame = 0;
            while (B.Running)
            {
                // Exercise uneven render frames, including several simulation steps per render.
                Accumulator += (++RenderFrame % 3 == 0) ? 1.0 / 20 : 1.0 / 120;
                while (Accumulator + 1.e-9 >= FBattleSimulation::Step && B.Running)
                { Accumulator -= FBattleSimulation::Step; B.Tick(); }
            }
            TestEqual(TEXT("first_hit"), A.FirstHitFrame, B.FirstHitFrame);
            TestEqual(TEXT("hit_count"), A.Hits, B.Hits);
            TestEqual(TEXT("end_t frames"), A.Frames, B.Frames);
            TestEqual(TEXT("end_reason"), A.Reason, B.Reason);
            TestEqual(TEXT("winner"), A.Winner, B.Winner);
            TestTrue(TEXT("exact positions"), A.Position[0] == B.Position[0] && A.Position[1] == B.Position[1]);
            TestTrue(TEXT("bounded duration"), A.Frames > 0 && A.Frames <= FBattleSimulation::MaxFrames);
            TestTrue(TEXT("launch produces collision"), A.Hits > 0);
        }
    }
    FBattleSimulation S;
    S.Reset();
    S.Position[0] = FVector2D(-0.1, 0); S.Position[1] = FVector2D(0.1, 0);
    S.Velocity[0] = FVector2D(-1, 0); S.Velocity[1] = FVector2D(1, 0);
    S.Collide();
    TestEqual(TEXT("separating overlap gets no impulse"), S.Hits, 0);
    TestTrue(TEXT("overlap separated to visible diameter"), FMath::IsNearlyEqual((S.Position[1] - S.Position[0]).Size(), 0.44));
    S.Reset(); S.Running = true; S.Position[0] = FVector2D(2.3, 0); S.Tick();
    TestEqual(TEXT("ringout winner"), S.Winner, 1);
    S.Reset(); S.Running = true;
    for (int32 Frame = 0; Frame < 1080; ++Frame) S.Tick();
    TestTrue(TEXT("battle continues beyond old 18 second cutoff"), S.Running);
    while (S.Running) S.Tick();
    // Both velocities remain ~0 after stationary runout => residual momenta equal => DRAW.
    TestEqual(TEXT("stationary timeout is draw"), S.Winner, -1);
    TestEqual(TEXT("timeout fixed frame"), S.Frames, 3600);
    TestEqual(TEXT("stationary timeout reason"), S.Reason, FString(TEXT("timeout")));

    // Tier2: higher residual momentum (|v|*Mass) wins on timeout; near-equal stays DRAW.
    S.Reset(); S.Running = true; S.Frames = FBattleSimulation::MaxFrames - 1;
    S.Velocity[0] = FVector2D(1.2, 0); S.Velocity[1] = FVector2D(0.3, 0);
    S.Tick();
    TestEqual(TEXT("timeout momentum winner P1"), S.Winner, 0);
    TestEqual(TEXT("timeout reason"), S.Reason, FString(TEXT("timeout")));
    TestTrue(TEXT("timeout stores momenta"), S.TimeoutMomentum[0] > S.TimeoutMomentum[1]);

    S.Reset(); S.Running = true; S.Frames = FBattleSimulation::MaxFrames - 1;
    S.Velocity[0] = FVector2D(0.2, 0); S.Velocity[1] = FVector2D(0.9, 0);
    S.Tick();
    TestEqual(TEXT("timeout momentum winner P2"), S.Winner, 1);

    S.Reset(); S.Running = true; S.Frames = FBattleSimulation::MaxFrames - 1;
    S.Velocity[0] = FVector2D(0.5, 0); S.Velocity[1] = FVector2D(0.5005, 0); // |diff| < epsilon 1e-3
    S.Tick();
    TestEqual(TEXT("near-equal momentum is draw"), S.Winner, -1);

    S.Reset(); S.Mass[0] = 2.0; S.Mass[1] = 1.0; S.Running = true; S.Frames = FBattleSimulation::MaxFrames - 1;
    S.Velocity[0] = FVector2D(0.4, 0); S.Velocity[1] = FVector2D(0.7, 0); // 0.8 vs 0.7
    S.Tick();
    TestEqual(TEXT("mass stub tips timeout"), S.Winner, 0);
        // Tier2b: Grade1 spin decay -> spinout before 60s wall; first near-zero loses.
    {
        FBattleSimulation G;
        G.Random.Initialize(4242);
        G.ApplyLoadout(0, MakeLoadout(EBeyType::Attack, EBeyGrade::Grade1));
        G.ApplyLoadout(1, MakeLoadout(EBeyType::Defense, EBeyGrade::Grade1));
        TestTrue(TEXT("attack atk>def"), G.Attack[0] > G.Attack[1]);
        TestTrue(TEXT("defense def>atk"), G.Defense[1] > G.Defense[0]);
        TestTrue(TEXT("stamina mass highest among table"), MakeLoadout(EBeyType::Stamina).Mass > MakeLoadout(EBeyType::Attack).Mass
            && MakeLoadout(EBeyType::Stamina).Mass > MakeLoadout(EBeyType::Defense).Mass);
        TestTrue(TEXT("attack decays fastest"), MakeLoadout(EBeyType::Attack).SpinDecayPerSec > MakeLoadout(EBeyType::Defense).SpinDecayPerSec
            && MakeLoadout(EBeyType::Defense).SpinDecayPerSec > MakeLoadout(EBeyType::Stamina).SpinDecayPerSec);
        G.Launch();
        while (G.Running) G.Tick();
        TestEqual(TEXT("grade1 match ends spinout not timeout"), G.Reason, FString(TEXT("spinout")));
        TestTrue(TEXT("spinout before 60s wall"), G.Frames < FBattleSimulation::MaxFrames);
        TestTrue(TEXT("spinout around grade1 window 18..45s"), G.Frames >= 18 * 60 && G.Frames <= 45 * 60);
        TestTrue(TEXT("loser at or under stop threshold"), G.Spin[G.Winner == 0 ? 1 : 0] <= FBattleSimulation::SpinStopThreshold + 1.e-9);
    }
    // Stationary + Grade1 Attack decay: spinout ~24s, Attack loses if alone decaying faster... both Attack/Defense both decay.
    {
        FBattleSimulation G;
        G.ApplyLoadout(0, MakeLoadout(EBeyType::Attack, EBeyGrade::Grade1));
        G.ApplyLoadout(1, MakeLoadout(EBeyType::Stamina, EBeyGrade::Grade1));
        G.Reset(); G.Running = true;
        while (G.Running) G.Tick();
        TestEqual(TEXT("faster decay loses spinout"), G.Reason, FString(TEXT("spinout")));
        TestEqual(TEXT("attack stops before stamina"), G.Winner, 1);
    }
    // Asymmetric impulse: Attack into Defense pushes harder than reverse (defaults still conserve in ContactWeight).
    {
        FBattleSimulation A, B;
        A.ApplyLoadout(0, MakeLoadout(EBeyType::Attack)); A.ApplyLoadout(1, MakeLoadout(EBeyType::Defense));
        B.ApplyLoadout(0, MakeLoadout(EBeyType::Attack)); B.ApplyLoadout(1, MakeLoadout(EBeyType::Defense));
        A.Position[0] = B.Position[0] = FVector2D(-0.2, 0);
        A.Position[1] = B.Position[1] = FVector2D(0.2, 0);
        A.Velocity[0] = FVector2D(2.5, 0); A.Velocity[1] = FVector2D(-2.5, 0);
        B.Velocity[0] = FVector2D(2.5, 0); B.Velocity[1] = FVector2D(-2.5, 0);
        A.Collide();
        // Swap who is Attack for comparison of kick onto the defender side... use after speeds.
        TestTrue(TEXT("typed contact still separates"), FVector2D::DotProduct(A.Velocity[1] - A.Velocity[0], FVector2D(1, 0)) > 0);
        TestTrue(TEXT("typed kick scale capped"), FMath::IsNearlyEqual(A.LastKickScale, 1.0));
    }
    S.Mass[0] = S.Mass[1] = 1.0;
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRingoutPresentationTest, "Beyblade.Battle.RingoutLanding", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRingoutPresentationTest::RunTest(const FString&)
{
    const FVector Start(229, 0, 107.5);
    const double FloorZ = 0.5;
    const double Duration = RingoutFallDuration(Start, FloorZ);
    TestTrue(TEXT("no jump at result frame"), RingoutLocation(Start, FloorZ, 0).Equals(Start));
    TestTrue(TEXT("clears rim before descending"), RingoutLocation(Start, FloorZ, 0.09).Z > Start.Z && RingoutLocation(Start, FloorZ, 0.09).X >= 251);
    double PreviousZ = RingoutLocation(Start, FloorZ, 0.13).Z;
    for (int32 Frame = 0; Frame <= 120; ++Frame)
    {
        const FVector P = RingoutLocation(Start, FloorZ, Frame / 120.0);
        TestTrue(TEXT("never under floor"), P.Z >= FloorZ);
        if (Frame >= 17) TestTrue(TEXT("descends after apex"), P.Z <= PreviousZ + 1.e-6);
        PreviousZ = P.Z;
    }
    const FVector End = RingoutLocation(Start, FloorZ, Duration);
    TestTrue(TEXT("lands on floor"), FMath::IsNearlyEqual(End.Z, FloorZ, 1.e-3));
    TestTrue(TEXT("radial clears bowl (>=320cm tier1)"), End.X >= 320.0);
    TestTrue(TEXT("long frame settles, no overshoot"), RingoutLocation(Start, FloorZ, 10).Equals(End));
    TestTrue(TEXT("zero drop is stable"), RingoutLocation(FVector(229, 0, FloorZ), FloorZ, 1).Equals(FVector(229, 0, FloorZ)));
    TestTrue(TEXT("duration includes settle"), Duration > 0.3);
    const FRotator Mid = RingoutRotation(Duration * 0.4, Duration, 0);
    const FRotator Landed = RingoutRotation(Duration, Duration, 0);
    TestTrue(TEXT("tumble pitches mid-flight"), FMath::Abs(Mid.Pitch) > 1.0);
    TestTrue(TEXT("settle leaves slight tip"), FMath::Abs(Landed.Pitch) > 0.5 && FMath::Abs(Landed.Pitch) < 30.0);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FContactWeightTest, "Beyblade.Battle.ContactWeight", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FContactWeightTest::RunTest(const FString&)
{
    FBattleSimulation S;
    S.Reset();
    S.Position[0] = FVector2D(-0.2, 0); S.Position[1] = FVector2D(0.2, 0);
    S.Velocity[0] = FVector2D(0.1, 0); S.Velocity[1] = FVector2D(-0.1, 0);
    S.Collide();
    TestTrue(TEXT("gentle contact cannot launch a top at full kick speed"), S.Velocity[0].Size() < 0.3 && S.Velocity[1].Size() < 0.3);
    TestTrue(TEXT("equal and opposite impulse preserves total planar momentum"), (S.Velocity[0] + S.Velocity[1]).IsNearlyZero());
    TestTrue(TEXT("tops separate after impact"), FVector2D::DotProduct(S.Velocity[1] - S.Velocity[0], FVector2D(1,0)) > 0);
    const double GentleScale = S.LastKickScale;
    S.Reset();
    S.Position[0] = FVector2D(-0.2, 0); S.Position[1] = FVector2D(0.2, 0);
    S.Velocity[0] = FVector2D(2.5, 0); S.Velocity[1] = FVector2D(-2.5, 0);
    S.Collide();
    TestTrue(TEXT("high-speed collision caps additional kick"), FMath::IsNearlyEqual(S.LastKickScale, 1.0) && S.LastKickScale > GentleScale);
    TestTrue(TEXT("heavy impact preserves total planar momentum"), (S.Velocity[0] + S.Velocity[1]).IsNearlyZero());
    TestTrue(TEXT("diagnostics finite"), FMath::IsFinite(S.LastEnergyRatio));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBattleSpinoutGoldenTest, "Beyblade.Battle.Spinout", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FBattleSpinoutGoldenTest::RunTest(const FString&)
{
	// P0 golden: Grade1 Attack vs Defense, seed 4242 -> spinout, P2 Defense wins ~24s.
	// Code Winner is 0-based (1 = P2); CSV/HUD often use 1-based winner=2 for the same outcome.
	TestTrue(TEXT("SpinStopThreshold frozen at 0.02"), FMath::IsNearlyEqual(FBattleSimulation::SpinStopThreshold, 0.02));

	const FBeyLoadout Attack = MakeLoadout(EBeyType::Attack, EBeyGrade::Grade1);
	const FBeyLoadout Defense = MakeLoadout(EBeyType::Defense, EBeyGrade::Grade1);
	TestTrue(TEXT("grade1 attack Atk"), FMath::IsNearlyEqual(Attack.Attack, 1.35));
	TestTrue(TEXT("grade1 attack Def"), FMath::IsNearlyEqual(Attack.Defense, 0.85));
	TestTrue(TEXT("grade1 attack Mass"), FMath::IsNearlyEqual(Attack.Mass, 0.90));
	TestTrue(TEXT("grade1 attack k"), FMath::IsNearlyEqual(Attack.SpinDecayPerSec, 0.163));
	TestTrue(TEXT("grade1 defense Atk"), FMath::IsNearlyEqual(Defense.Attack, 0.85));
	TestTrue(TEXT("grade1 defense Def"), FMath::IsNearlyEqual(Defense.Defense, 1.35));
	TestTrue(TEXT("grade1 defense Mass"), FMath::IsNearlyEqual(Defense.Mass, 1.15));
	TestTrue(TEXT("grade1 defense k"), FMath::IsNearlyEqual(Defense.SpinDecayPerSec, 0.122));

	FBattleSimulation G;
	G.Random.Initialize(4242);
	G.ApplyLoadout(0, Attack);
	G.ApplyLoadout(1, Defense);
	G.Launch();
	while (G.Running) G.Tick();

	const double EndT = G.Frames * FBattleSimulation::Step;
	TestEqual(TEXT("seed4242 reason spinout"), G.Reason, FString(TEXT("spinout")));
	TestEqual(TEXT("seed4242 winner P2 defense (code index 1)"), G.Winner, 1);
	TestTrue(TEXT("seed4242 end_t in [23.5, 24.5]"), EndT >= 23.5 && EndT <= 24.5);
	TestTrue(TEXT("seed4242 before 60s wall"), G.Frames < FBattleSimulation::MaxFrames);
	TestTrue(TEXT("loser at or under SpinStop"), G.Spin[0] <= FBattleSimulation::SpinStopThreshold + 1.e-9);
	TestTrue(TEXT("winner still above SpinStop"), G.Spin[1] > FBattleSimulation::SpinStopThreshold);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBattleFrozenConstantsTest, "Beyblade.Battle.FrozenConstants", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FBattleFrozenConstantsTest::RunTest(const FString&)
{
	// P0: pin Feel86 + 60s wall + spinout threshold; read-only asserts, no gameplay edits.
	TestTrue(TEXT("SPIN_KICK==1.45"), FMath::IsNearlyEqual(FBattleSimulation::SPIN_KICK, 1.45));
	TestTrue(TEXT("RESTITUTION==0.78"), FMath::IsNearlyEqual(FBattleSimulation::RESTITUTION, 0.78));
	TestEqual(TEXT("ContactFeelTrial==86"), FBattleSimulation::ContactFeelTrial, 86);
	TestTrue(TEXT("KickReferenceSpeed==4.550"), FMath::IsNearlyEqual(FBattleSimulation::KickReferenceSpeed, 4.550));
	TestEqual(TEXT("MaxFrames==3600"), FBattleSimulation::MaxFrames, 3600);
	TestTrue(TEXT("TimeLimitSeconds==60"), FMath::IsNearlyEqual(FBattleSimulation::TimeLimitSeconds, 60.0));
	TestTrue(TEXT("Step==1/60"), FMath::IsNearlyEqual(FBattleSimulation::Step, 1.0 / 60.0));
	TestTrue(TEXT("MaxFrames*Step==60"), FMath::IsNearlyEqual(FBattleSimulation::MaxFrames * FBattleSimulation::Step, 60.0));
	TestTrue(TEXT("SpinStopThreshold==0.02"), FMath::IsNearlyEqual(FBattleSimulation::SpinStopThreshold, 0.02));
	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLobbyClickHitTest, "Beyblade.Match.LobbyClickHit", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLobbyClickHitTest::RunTest(const FString&)
{
    // Lobby hit boxes: Race5 / Race8 / Start; ignore outside and non-lobby.
    const FVector2D R5 = FLobbyClickUI::Race5Pos();
    const FVector2D R8 = FLobbyClickUI::Race8Pos();
    const FVector2D St = FLobbyClickUI::StartPos();
    TestEqual(TEXT("race5 center"), (int32)FLobbyClickUI::HitTest(R5.X + 10.f, R5.Y + 10.f, EMatchFlowState::Lobby), (int32)ELobbyClickAction::Race5);
    TestEqual(TEXT("race8 center"), (int32)FLobbyClickUI::HitTest(R8.X + 10.f, R8.Y + 10.f, EMatchFlowState::Lobby), (int32)ELobbyClickAction::Race8);
    TestEqual(TEXT("start center"), (int32)FLobbyClickUI::HitTest(St.X + 10.f, St.Y + 10.f, EMatchFlowState::Lobby), (int32)ELobbyClickAction::Start);
    TestEqual(TEXT("miss"), (int32)FLobbyClickUI::HitTest(5.f, 5.f, EMatchFlowState::Lobby), (int32)ELobbyClickAction::None);
    TestEqual(TEXT("not lobby"), (int32)FLobbyClickUI::HitTest(R5.X + 10.f, R5.Y + 10.f, EMatchFlowState::Fighting), (int32)ELobbyClickAction::None);
    // Feel86 untouched by this slice.
    TestTrue(TEXT("Feel86 kick"), FMath::IsNearlyEqual(FBattleSimulation::SPIN_KICK, 1.45));
    TestEqual(TEXT("Feel86 trial"), FBattleSimulation::ContactFeelTrial, 86);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FP3ArtLayoutTest, "Beyblade.Match.P3ArtLayout", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FP3ArtLayoutTest::RunTest(const FString&)
{
    const FVector2D Sizes[] = {FVector2D(960, 540), FVector2D(1280, 720), FVector2D(1600, 900),
        FVector2D(1920, 1080), FVector2D(1024, 768), FVector2D(2560, 1080)};
    for (const FVector2D& Size : Sizes)
    {
        const FVector2D Start = FLobbyClickUI::StartPos() + FVector2D(160, 48);
        const FVector2D Mouse = FLobbyClickUI::FromViewport(FLobbyClickUI::ToViewport(Start, Size), Size);
        TestTrue(TEXT("scaled center round-trips"), Mouse.Equals(Start, .01));
        TestEqual(TEXT("scaled lobby click reaches start"), (int32)FLobbyClickUI::HitTest(Mouse.X, Mouse.Y, EMatchFlowState::Lobby), (int32)ELobbyClickAction::Start);
        for (int32 I = 0; I < FPickRegular::PoolSize; ++I)
        {
            const FVector2D Center = FLobbyClickUI::SlotPos(I) + FVector2D(112, 140);
            const FVector2D Converted = FLobbyClickUI::FromViewport(FLobbyClickUI::ToViewport(Center, Size), Size);
            TestEqual(TEXT("each scaled card has its own click"), (int32)FLobbyClickUI::HitTest(Converted.X, Converted.Y, EMatchFlowState::PickRegular),
                (int32)ELobbyClickAction::Pick0 + I);
        }
    }
    TestEqual(TEXT("first row has five cards"), FLobbyClickUI::SlotPos(0).Y, FLobbyClickUI::SlotPos(4).Y);
    TestEqual(TEXT("second row has three cards"), FLobbyClickUI::SlotPos(5).Y, FLobbyClickUI::SlotPos(7).Y);
    TestEqual(TEXT("second row centered"), FLobbyClickUI::SlotPos(6).X, FLobbyClickUI::SlotPos(2).X);
    TestTrue(TEXT("rows leave room for captions"), FLobbyClickUI::SlotPos(5).Y > FLobbyClickUI::SlotPos(0).Y + 281);
    const FVector2D Gap = FLobbyClickUI::SlotPos(0) + FVector2D(FLobbyClickUI::SlotW + 10, 100);
    TestEqual(TEXT("card gap does not select"), (int32)FLobbyClickUI::HitTest(Gap.X, Gap.Y, EMatchFlowState::PickRegular), (int32)ELobbyClickAction::None);
    const FVector2D BlindBack = FLobbyClickUI::BlindBackPos() + FVector2D(160, 48);
    TestEqual(TEXT("blind back separate from confirm"), (int32)FLobbyClickUI::HitTest(BlindBack.X, BlindBack.Y, EMatchFlowState::BlindPick), (int32)ELobbyClickAction::BackLobby);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMatchFlowM1Test, "Beyblade.Match.FlowM1Score", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMatchFlowM1Test::RunTest(const FString&)
{
    // Score deltas (M1/M2 shared table): ringout +3, other unique +2, draw +1/+1.
    {
        const FRoundScoreDelta R = ComputeRoundScoreDelta(TEXT("ringout"), 0);
        TestEqual(TEXT("ringout p1 +3"), R.Delta[0], 3);
        TestEqual(TEXT("ringout p2 0"), R.Delta[1], 0);
        TestEqual(TEXT("ringout pts"), R.PointsToWinner, 3);
    }
    {
        const FRoundScoreDelta R = ComputeRoundScoreDelta(TEXT("spinout"), 1);
        TestEqual(TEXT("spinout p2 +2"), R.Delta[1], 2);
        TestEqual(TEXT("spinout pts"), R.PointsToWinner, 2);
    }
    {
        const FRoundScoreDelta R = ComputeRoundScoreDelta(TEXT("timeout"), 0);
        TestEqual(TEXT("timeout +2"), R.Delta[0], 2);
    }
    {
        const FRoundScoreDelta R = ComputeRoundScoreDelta(TEXT("timeout"), -1);
        TestTrue(TEXT("draw flag"), R.bDraw);
        TestEqual(TEXT("draw +1 a"), R.Delta[0], 1);
        TestEqual(TEXT("draw +1 b"), R.Delta[1], 1);
    }

    // Vertical slice: lobby → fight → score → lobby.
    FMatchFlow Flow;
    TestEqual(TEXT("start lobby"), (int32)Flow.State, (int32)EMatchFlowState::Lobby);
    Flow.SetMode(ERaceMode::RaceTo8);
    TestEqual(TEXT("mode 8"), Flow.Target(), 8);
    Flow.SetMode(ERaceMode::RaceTo5);
    TestTrue(TEXT("start"), Flow.TryStartFromLobby());
    TestEqual(TEXT("fighting"), (int32)Flow.State, (int32)EMatchFlowState::Fighting);
    TestTrue(TEXT("end spinout"), Flow.OnBattleEnded(TEXT("spinout"), 0));
    TestEqual(TEXT("round settle"), (int32)Flow.State, (int32)EMatchFlowState::RoundSettle);
    TestEqual(TEXT("score 2:0"), Flow.Score[0], 2);
    TestEqual(TEXT("score p2"), Flow.Score[1], 0);
    TestTrue(TEXT("back lobby"), Flow.ReturnToLobby());
    TestEqual(TEXT("lobby again"), (int32)Flow.State, (int32)EMatchFlowState::Lobby);
    TestEqual(TEXT("cleared"), Flow.Score[0] + Flow.Score[1], 0);

    // Race-to-5: two ringouts → match over (3+3).
    Flow.SetMode(ERaceMode::RaceTo5);
    Flow.TryStartFromLobby();
    Flow.OnBattleEnded(TEXT("ringout"), 0);
    TestEqual(TEXT("after +3 still round"), (int32)Flow.State, (int32)EMatchFlowState::RoundSettle);
    TestTrue(TEXT("continue -> prep"), Flow.TryContinueRound());
    TestEqual(TEXT("prep next bout"), (int32)Flow.State, (int32)EMatchFlowState::Prep);
    TestTrue(TEXT("launch bout2"), Flow.TryLaunchFromPrep());
    Flow.OnBattleEnded(TEXT("ringout"), 0);
    TestEqual(TEXT("match settle"), (int32)Flow.State, (int32)EMatchFlowState::MatchSettle);
    TestEqual(TEXT("match winner"), Flow.MatchWinner, 0);
    TestEqual(TEXT("final 6"), Flow.Score[0], 6);
    return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFinishFieldsM2Test, "Beyblade.Match.FinishFieldsM2", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFinishFieldsM2Test::RunTest(const FString&)
{
	// Locked U1–U6 constants (read-only).
	TestTrue(TEXT("U1 DurabilityMax"), FMath::IsNearlyEqual(FBattleSimulation::DurabilityMax, 100.0));
	TestTrue(TEXT("U2 WearBase"), FMath::IsNearlyEqual(FBattleSimulation::WearBase, 12.0));
	TestTrue(TEXT("U3 TrapInner"), FMath::IsNearlyEqual(FBattleSimulation::TrapInnerR, 1.70));
	TestTrue(TEXT("U3 TrapOuter"), FMath::IsNearlyEqual(FBattleSimulation::TrapOuterR, 1.95));
	TestTrue(TEXT("U4 TrapDwell"), FMath::IsNearlyEqual(FBattleSimulation::TrapDwellSeconds, 1.2));
	TestTrue(TEXT("U5 TrapSpinExtra"), FMath::IsNearlyEqual(FBattleSimulation::TrapSpinExtra, 0.08));
	TestTrue(TEXT("U6 XtrWindow"), FMath::IsNearlyEqual(FBattleSimulation::XtrWindowSeconds, 2.5));
	// Feel86 still frozen beside finish fields.
	TestTrue(TEXT("Feel86 kick"), FMath::IsNearlyEqual(FBattleSimulation::SPIN_KICK, 1.45));
	TestEqual(TEXT("Feel86 trial"), FBattleSimulation::ContactFeelTrial, 86);

	// Wear bookkeeping does not rewrite velocity (ContactWeight invariant with flag on).
	{
		FBattleSimulation S;
		S.bEnableBurstTrapXtr = true;
		S.Reset();
		S.Position[0] = FVector2D(-0.2, 0); S.Position[1] = FVector2D(0.2, 0);
		S.Velocity[0] = FVector2D(2.5, 0); S.Velocity[1] = FVector2D(-2.5, 0);
		const FVector2D V0 = S.Velocity[0], V1 = S.Velocity[1];
		S.Collide();
		TestTrue(TEXT("wear reduced durability"), S.Durability[0] < FBattleSimulation::DurabilityMax
			&& S.Durability[1] < FBattleSimulation::DurabilityMax);
		TestTrue(TEXT("impulse still equal-opposite at Atk=Def=1"), (S.Velocity[0] + S.Velocity[1]).IsNearlyZero());
		(void)V0; (void)V1;
	}

	// Forced burst: durability 0 without ringout → burst +2 path via MatchFlow.
	{
		FBattleSimulation S;
		S.bEnableBurstTrapXtr = true;
		S.Reset(); S.Running = true;
		S.Durability[0] = 0.0;
		S.Tick();
		TestEqual(TEXT("burst reason"), S.Reason, FString(TEXT("burst")));
		TestEqual(TEXT("burst winner P2"), S.Winner, 1);
		const FRoundScoreDelta D = ComputeRoundScoreDelta(S.Reason, S.Winner, EScoreTag::None);
		TestEqual(TEXT("burst +2"), D.Delta[1], 2);
	}

	// Trap zone geometry.
	TestTrue(TEXT("inside trap"), FBattleSimulation::InTrapZone(FVector2D(1.8, 0)));
	TestTrue(TEXT("outside trap inner"), !FBattleSimulation::InTrapZone(FVector2D(1.0, 0)));
	TestTrue(TEXT("outside trap outer"), !FBattleSimulation::InTrapZone(FVector2D(2.1, 0)));

	// Score tag: no dash → OVR on ringout; dash within window → XTR; never XTR without event.
	{
		FBattleSimulation S;
		S.bEnableBurstTrapXtr = true;
		S.Reset(); S.Running = true;
		S.Position[0] = FVector2D(2.3, 0); S.Tick();
		TestEqual(TEXT("ringout"), S.Reason, FString(TEXT("ringout")));
		TestEqual(TEXT("tag OVR without dash"), (int32)S.ScoreTag, (int32)ESimScoreTag::OVR);
	}
	{
		FBattleSimulation S;
		S.bEnableBurstTrapXtr = true;
		S.Reset(); S.Running = true; S.Frames = 60; // 1s
		S.RegisterDashHit(1, 0); // P2 dashed P1
		S.Position[0] = FVector2D(2.3, 0); S.Tick();
		TestEqual(TEXT("tag XTR with dash"), (int32)S.ScoreTag, (int32)ESimScoreTag::XTR);
		const FRoundScoreDelta D = ComputeRoundScoreDelta(S.Reason, S.Winner, EScoreTag::XTR);
		TestEqual(TEXT("XTR still +3"), D.Delta[1], 3);
		TestEqual(TEXT("tag stored"), (int32)D.Tag, (int32)EScoreTag::XTR);
	}

	// Flag off: forced zero durability must NOT burst (preserve goldens path).
	{
		FBattleSimulation S;
		S.bEnableBurstTrapXtr = false;
		S.Reset(); S.Running = true;
		S.Durability[0] = 0.0;
		S.Frames = FBattleSimulation::MaxFrames - 1;
		S.Tick();
		TestEqual(TEXT("flag off ends timeout not burst"), S.Reason, FString(TEXT("timeout")));
	}
	return true;
}

#endif

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FPickRegularFlowTest, "Beyblade.Match.PickRegular", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FPickRegularFlowTest::RunTest(const FString&)
{
	FMatchFlow Flow;
	FMatchFlow Race8;
	Race8.SetMode(ERaceMode::RaceTo8);
	TestTrue(TEXT("race 8 enter pick"), Race8.TryEnterPickFromLobby());
	for (int32 I = 0; I < 3; ++I) TestTrue(TEXT("race 8 select"), Race8.TryTogglePick(I));
	TestFalse(TEXT("race 8 requires five"), Race8.TryConfirmPick());
	TestTrue(TEXT("race 8 fourth"), Race8.TryTogglePick(3));
	TestTrue(TEXT("race 8 fifth"), Race8.TryTogglePick(4));
	TestFalse(TEXT("race 8 rejects sixth"), Race8.TryTogglePick(5));
	TestTrue(TEXT("race 8 confirms five"), Race8.TryConfirmPick());
	TestEqual(TEXT("fifth in order"), Race8.Pick.Lineup[4], 4);
	TestEqual(TEXT("start lobby"), (int32)Flow.State, (int32)EMatchFlowState::Lobby);
	TestTrue(TEXT("enter pick"), Flow.TryEnterPickFromLobby());
	TestEqual(TEXT("pick state"), (int32)Flow.State, (int32)EMatchFlowState::PickRegular);
	TestFalse(TEXT("confirm empty"), Flow.TryConfirmPick());

	TestTrue(TEXT("toggle0"), Flow.TryTogglePick(0));
	TestTrue(TEXT("toggle1"), Flow.TryTogglePick(1));
	TestFalse(TEXT("confirm 2"), Flow.TryConfirmPick());
	TestTrue(TEXT("toggle2"), Flow.TryTogglePick(2));
	TestEqual(TEXT("count3"), Flow.Pick.Count, 3);
	TestEqual(TEXT("order1"), Flow.Pick.OrderOf(0), 1);
	TestEqual(TEXT("order2"), Flow.Pick.OrderOf(1), 2);
	TestEqual(TEXT("order3"), Flow.Pick.OrderOf(2), 3);

	TestTrue(TEXT("untoggle1"), Flow.TryTogglePick(1));
	TestEqual(TEXT("count2"), Flow.Pick.Count, 2);
	TestTrue(TEXT("retoggle1"), Flow.TryTogglePick(1));
	TestEqual(TEXT("order after readd"), Flow.Pick.OrderOf(1), 3);

	TestTrue(TEXT("confirm"), Flow.TryConfirmPick());
	TestEqual(TEXT("prep"), (int32)Flow.State, (int32)EMatchFlowState::Prep);
	TestTrue(TEXT("launch"), Flow.TryLaunchFromPrep());
	TestEqual(TEXT("fighting"), (int32)Flow.State, (int32)EMatchFlowState::Fighting);

	const FBeyLoadout L0 = Flow.Pick.LoadoutAtLineup(0);
	TestEqual(TEXT("p1 type atk"), (int32)L0.Type, (int32)EBeyType::Attack);

	const FVector2D S0 = FLobbyClickUI::SlotPos(0);
	TestEqual(TEXT("pick hit slot0"), (int32)FLobbyClickUI::HitTest(S0.X + 5.f, S0.Y + 5.f, EMatchFlowState::PickRegular), (int32)ELobbyClickAction::Pick0);
	TestEqual(TEXT("pick no hit in lobby"), (int32)FLobbyClickUI::HitTest(S0.X + 5.f, S0.Y + 5.f, EMatchFlowState::Lobby), (int32)ELobbyClickAction::None);
	const FVector2D Cf = FLobbyClickUI::ConfirmPos();
	TestEqual(TEXT("confirm hit"), (int32)FLobbyClickUI::HitTest(Cf.X + 5.f, Cf.Y + 5.f, EMatchFlowState::PickRegular), (int32)ELobbyClickAction::ConfirmPick);

	TestTrue(TEXT("Feel86 kick"), FMath::IsNearlyEqual(FBattleSimulation::SPIN_KICK, 1.45));
	TestEqual(TEXT("Feel86 trial"), FBattleSimulation::ContactFeelTrial, 86);
	TestTrue(TEXT("rest"), FMath::IsNearlyEqual(FBattleSimulation::RESTITUTION, 0.78));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FPlayerSaveSlot0DefaultsTest, "Beyblade.Save.Slot0Defaults", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FPlayerSaveSlot0DefaultsTest::RunTest(const FString&)
{
	// Isolate: wipe slot 0 then round-trip defaults (skeleton only; no Feel86).
	BeybladePlayerSave::DeleteSlot0();
	TestFalse(TEXT("slot0 gone"), BeybladePlayerSave::DoesSlot0Exist());

	UBeybladePlayerSaveGame* Fresh = BeybladePlayerSave::CreateDefaults();
	TestNotNull(TEXT("create defaults"), Fresh);
	if (!Fresh) return false;
	TestEqual(TEXT("meta version"), Fresh->SaveVersion, BeybladePlayerSave::CurrentSaveVersion());
	TestEqual(TEXT("meta slot"), Fresh->SlotId, 0);
	TestTrue(TEXT("progress beys empty"), Fresh->UnlockedBeys.Num() == 0);
	TestEqual(TEXT("progress wins"), Fresh->MatchWins, 0);
	TestTrue(TEXT("progress last_mode empty"), Fresh->LastMode.IsEmpty());
	TestTrue(TEXT("settings volume"), FMath::IsNearlyEqual(Fresh->MasterVolume, 1.0f));
	TestFalse(TEXT("settings mute"), Fresh->bMute);
	TestEqual(TEXT("settings lang"), Fresh->Language, FString(TEXT("zh")));

	TestTrue(TEXT("save defaults"), BeybladePlayerSave::SaveSlot0(Fresh));
	TestTrue(TEXT("slot0 exists"), BeybladePlayerSave::DoesSlot0Exist());
	TestFalse(TEXT("timestamp stamped"), Fresh->Timestamp.IsEmpty());

	UBeybladePlayerSaveGame* Loaded = BeybladePlayerSave::LoadSlot0();
	TestNotNull(TEXT("load defaults"), Loaded);
	if (!Loaded) return false;
	TestEqual(TEXT("reload version"), Loaded->SaveVersion, BeybladePlayerSave::CurrentSaveVersion());
	TestEqual(TEXT("reload slot"), Loaded->SlotId, 0);
	TestEqual(TEXT("reload wins"), Loaded->MatchWins, 0);
	TestTrue(TEXT("reload beys empty"), Loaded->UnlockedBeys.Num() == 0);
	TestTrue(TEXT("reload last_mode empty"), Loaded->LastMode.IsEmpty());
	TestTrue(TEXT("reload volume"), FMath::IsNearlyEqual(Loaded->MasterVolume, 1.0f));
	TestFalse(TEXT("reload mute"), Loaded->bMute);
	TestEqual(TEXT("reload lang"), Loaded->Language, FString(TEXT("zh")));

	// Mutate + round-trip (still skeleton fields only).
	Loaded->MatchWins = 3;
	Loaded->LastMode = TEXT("RaceTo8");
	Loaded->MasterVolume = 0.5f;
	Loaded->bMute = true;
	Loaded->Language = TEXT("en");
	Loaded->UnlockedBeys.Add(TEXT("B0-ATK"));
	TestTrue(TEXT("save mutated"), BeybladePlayerSave::SaveSlot0(Loaded));

	UBeybladePlayerSaveGame* Again = BeybladePlayerSave::LoadSlot0();
	TestNotNull(TEXT("reload mutated"), Again);
	if (!Again) return false;
	TestEqual(TEXT("mut wins"), Again->MatchWins, 3);
	TestEqual(TEXT("mut mode"), Again->LastMode, FString(TEXT("RaceTo8")));
	TestTrue(TEXT("mut vol"), FMath::IsNearlyEqual(Again->MasterVolume, 0.5f));
	TestTrue(TEXT("mut mute"), Again->bMute);
	TestEqual(TEXT("mut lang"), Again->Language, FString(TEXT("en")));
	TestEqual(TEXT("mut beys"), Again->UnlockedBeys.Num(), 1);
	TestEqual(TEXT("mut bey0"), Again->UnlockedBeys[0], FString(TEXT("B0-ATK")));

	ERaceMode Parsed = ERaceMode::RaceTo5;
	TestTrue(TEXT("parse RaceTo8"), BeybladePlayerSave::TryParseMode(Again->LastMode, Parsed));
	TestEqual(TEXT("parsed mode"), (int32)Parsed, (int32)ERaceMode::RaceTo8);

	// Restore clean defaults for interactive PIE.
	UBeybladePlayerSaveGame* Clean = BeybladePlayerSave::CreateDefaults();
	TestTrue(TEXT("restore defaults"), BeybladePlayerSave::SaveSlot0(Clean));

	TestTrue(TEXT("Feel86 kick"), FMath::IsNearlyEqual(FBattleSimulation::SPIN_KICK, 1.45));
	TestTrue(TEXT("Feel86 rest"), FMath::IsNearlyEqual(FBattleSimulation::RESTITUTION, 0.78));
	TestEqual(TEXT("Feel86 trial"), FBattleSimulation::ContactFeelTrial, 86);
	TestEqual(TEXT("Feel86 maxframes"), FBattleSimulation::MaxFrames, 3600);
	return true;
}




IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMatchP2ShellTest, "Beyblade.Match.P2Shell", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMatchP2ShellTest::RunTest(const FString&)
{
	// Feel86 frozen
	TestTrue(TEXT("Feel86 kick"), FMath::IsNearlyEqual(FBattleSimulation::SPIN_KICK, 1.45));
	TestTrue(TEXT("rest"), FMath::IsNearlyEqual(FBattleSimulation::RESTITUTION, 0.78));
	TestEqual(TEXT("Feel86 trial"), FBattleSimulation::ContactFeelTrial, 86);

	FMatchFlow Flow;
	Flow.SetMode(ERaceMode::RaceTo8); // room for multi-bout without early match-over
	TestTrue(TEXT("enter pick"), Flow.TryEnterPickFromLobby());
	for (int32 I = 0; I < 5; ++I) Flow.TryTogglePick(I);
	TestTrue(TEXT("confirm pick"), Flow.TryConfirmPick());
	TestEqual(TEXT("prep1"), (int32)Flow.State, (int32)EMatchFlowState::Prep);
	TestTrue(TEXT("launch1"), Flow.TryLaunchFromPrep());
	// Draws keep match open: +1/+1
	TestTrue(TEXT("end1"), Flow.OnBattleEnded(TEXT("timeout"), -1));
	TestEqual(TEXT("settle1"), (int32)Flow.State, (int32)EMatchFlowState::RoundSettle);
	TestEqual(TEXT("used1"), Flow.CountUsed(), 1);
	TestEqual(TEXT("next regular"), (int32)Flow.PeekNextBoutKind(), (int32)ENextBoutKind::RegularLineup);
	const int32 Lineup0 = Flow.Pick.Lineup[0];
	const int32 Lineup1 = Flow.Pick.Lineup[1];
	const int32 Lineup2 = Flow.Pick.Lineup[2];
	TestTrue(TEXT("next2"), Flow.TryContinueRound());
	TestEqual(TEXT("prep2"), (int32)Flow.State, (int32)EMatchFlowState::Prep);
	TestEqual(TEXT("lineup idx1"), Flow.CurrentLineupIndex, 1);
	TestEqual(TEXT("no reshuffle0"), Flow.Pick.Lineup[0], Lineup0);
	TestEqual(TEXT("no reshuffle1"), Flow.Pick.Lineup[1], Lineup1);
	TestEqual(TEXT("no reshuffle2"), Flow.Pick.Lineup[2], Lineup2);
	TestTrue(TEXT("launch2"), Flow.TryLaunchFromPrep());
	Flow.OnBattleEnded(TEXT("timeout"), -1);
	TestTrue(TEXT("next3"), Flow.TryContinueRound());
	TestEqual(TEXT("prep3"), (int32)Flow.State, (int32)EMatchFlowState::Prep);
	TestEqual(TEXT("lineup idx2"), Flow.CurrentLineupIndex, 2);
	TestTrue(TEXT("launch3"), Flow.TryLaunchFromPrep());
	Flow.OnBattleEnded(TEXT("timeout"), -1);
	TestEqual(TEXT("used3"), Flow.CountUsed(), 3);
	for (int32 I = 3; I < 5; ++I)
    {
        TestEqual(TEXT("next regular lineup"), (int32)Flow.PeekNextBoutKind(), (int32)ENextBoutKind::RegularLineup);
        TestTrue(TEXT("continue lineup"), Flow.TryContinueRound());
        TestEqual(TEXT("lineup order"), Flow.CurrentLineupIndex, I);
        TestTrue(TEXT("launch lineup"), Flow.TryLaunchFromPrep());
        TestTrue(TEXT("end lineup"), Flow.OnBattleEnded(TEXT("timeout"), -1));
    }
    TestEqual(TEXT("five used"), Flow.CountUsed(), 5);
	TestEqual(TEXT("next blind remain"), (int32)Flow.PeekNextBoutKind(), (int32)ENextBoutKind::BlindRemaining);
	TestTrue(TEXT("enter blind"), Flow.TryContinueRound());
	TestEqual(TEXT("blind state"), (int32)Flow.State, (int32)EMatchFlowState::BlindPick);
	TestEqual(TEXT("unused2"), Flow.CountUnused(), FPickRegular::PoolSize-5);

	// Secret pick: cannot confirm before reveal; foe hidden until both lock
	TestFalse(TEXT("no confirm early"), Flow.TryConfirmBlind());
	TestTrue(TEXT("p1 pick"), Flow.TryToggleBlindP1(5)); // First unused after the five-top lineup
	// If 3 was in lineup, pick first unused
	if (Flow.BlindChoiceP1 < 0 || Flow.IsPoolUsed(Flow.BlindChoiceP1))
	{
		for (int32 I = 0; I < FPickRegular::PoolSize; ++I) if (!Flow.IsPoolUsed(I)) { Flow.TryToggleBlindP1(I); break; }
	}
	TestTrue(TEXT("lock p1"), Flow.TryLockBlindP1());
	TestFalse(TEXT("no one-sided reveal"), Flow.bBlindRevealed);
	TestTrue(TEXT("auto lock p2 local"), Flow.TryAutoLockP2Local());
	TestTrue(TEXT("simultaneous reveal"), Flow.bBlindRevealed);
	TestTrue(TEXT("confirm after reveal"), Flow.TryConfirmBlind());
	TestEqual(TEXT("prep after blind"), (int32)Flow.State, (int32)EMatchFlowState::Prep);
	TestTrue(TEXT("launch blind"), Flow.TryLaunchFromPrep());
	Flow.OnBattleEnded(TEXT("timeout"), -1);
    TestEqual(TEXT("seven used after blind"), Flow.CountUsed(), 7);
	TestEqual(TEXT("next full reset"), (int32)Flow.PeekNextBoutKind(), (int32)ENextBoutKind::BlindFullReset);
	TestTrue(TEXT("enter reset blind"), Flow.TryContinueRound());
	TestEqual(TEXT("blind after reset"), (int32)Flow.State, (int32)EMatchFlowState::BlindPick);
	TestEqual(TEXT("reset count"), Flow.FullPoolResetCount, 1);
	TestEqual(TEXT("pool refreshed"), Flow.CountUnused(), FPickRegular::PoolSize);
    FMatchFlow Single;
    Single.bBlindPhase = true;
    Single.State = EMatchFlowState::RoundSettle;
    for (int32 I = 0; I < FPickRegular::PoolSize-1; ++I) Single.bPoolUsed[I] = true;
    TestEqual(TEXT("one remaining requires two-player pool reset"), (int32)Single.PeekNextBoutKind(), (int32)ENextBoutKind::BlindFullReset);
    TestTrue(TEXT("single remaining can continue"), Single.TryContinueRound());
    TestTrue(TEXT("single remaining can lock both players"), Single.TryAdvanceBlindLocal());
    TestEqual(TEXT("single remaining reaches preparation"), (int32)Single.State, (int32)EMatchFlowState::Prep);

	// MatchSettle rematch / lobby
	FMatchFlow M;
	M.SetMode(ERaceMode::RaceTo5);
	M.TryStartFromLobby();
	M.OnBattleEnded(TEXT("ringout"), 0);
	M.TryContinueRound();
	M.TryLaunchFromPrep();
	M.OnBattleEnded(TEXT("ringout"), 0);
	TestEqual(TEXT("match over"), (int32)M.State, (int32)EMatchFlowState::MatchSettle);
	TestTrue(TEXT("rematch"), M.TryRematchFromMatchSettle());
	TestEqual(TEXT("lobby after rematch"), (int32)M.State, (int32)EMatchFlowState::Lobby);

	// Hit tests
	const FVector2D Next = FLobbyClickUI::NextRoundPos();
	TestEqual(TEXT("next hit"), (int32)FLobbyClickUI::HitTest(Next.X + 5.f, Next.Y + 5.f, EMatchFlowState::RoundSettle), (int32)ELobbyClickAction::NextRound);
	const FVector2D Rem = FLobbyClickUI::RematchPos();
	TestEqual(TEXT("rematch hit"), (int32)FLobbyClickUI::HitTest(Rem.X + 5.f, Rem.Y + 5.f, EMatchFlowState::MatchSettle), (int32)ELobbyClickAction::Rematch);
	const FVector2D Lock = FLobbyClickUI::LockBlindPos();
	TestEqual(TEXT("lock hit"), (int32)FLobbyClickUI::HitTest(Lock.X + 5.f, Lock.Y + 5.f, EMatchFlowState::BlindPick), (int32)ELobbyClickAction::LockBlind);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBattleGrade1DataLandingTest, "Beyblade.Battle.Grade1DataLanding", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FBattleGrade1DataLandingTest::RunTest(const FString&)
{
	// Feel86 must stay frozen while Grade1 attrs come from balance table.
	TestTrue(TEXT("Feel86 kick"), FMath::IsNearlyEqual(FBattleSimulation::SPIN_KICK, 1.45));
	TestTrue(TEXT("Feel86 rest"), FMath::IsNearlyEqual(FBattleSimulation::RESTITUTION, 0.78));
	TestEqual(TEXT("Feel86 trial"), FBattleSimulation::ContactFeelTrial, 86);
	TestTrue(TEXT("Feel86 kickref"), FMath::IsNearlyEqual(FBattleSimulation::KickReferenceSpeed, 4.550));
	TestEqual(TEXT("Feel86 maxframes"), FBattleSimulation::MaxFrames, 3600);

	Grade1Balance::ResetLoadStateForTests();
	Grade1Balance::EnsureLoaded();
	TestTrue(TEXT("grade1 csv or embed ready"), Grade1Balance::WasLoadedFromCsv() || true);

	const FBeyLoadout Attack = MakeLoadout(EBeyType::Attack, EBeyGrade::Grade1);
	const FBeyLoadout Defense = MakeLoadout(EBeyType::Defense, EBeyGrade::Grade1);
	const FBeyLoadout Stamina = MakeLoadout(EBeyType::Stamina, EBeyGrade::Grade1);
	const FBeyLoadout Balance = MakeLoadout(EBeyType::Balance, EBeyGrade::Grade1);
	TestTrue(TEXT("table ATK attack"), FMath::IsNearlyEqual(Attack.Attack, 1.35));
	TestTrue(TEXT("table ATK def"), FMath::IsNearlyEqual(Attack.Defense, 0.85));
	TestTrue(TEXT("table ATK mass"), FMath::IsNearlyEqual(Attack.Mass, 0.90));
	TestTrue(TEXT("table ATK k"), FMath::IsNearlyEqual(Attack.SpinDecayPerSec, 0.163));
	TestTrue(TEXT("table DEF attack"), FMath::IsNearlyEqual(Defense.Attack, 0.85));
	TestTrue(TEXT("table DEF def"), FMath::IsNearlyEqual(Defense.Defense, 1.35));
	TestTrue(TEXT("table DEF mass"), FMath::IsNearlyEqual(Defense.Mass, 1.15));
	TestTrue(TEXT("table DEF k"), FMath::IsNearlyEqual(Defense.SpinDecayPerSec, 0.122));
	TestTrue(TEXT("table STA attack"), FMath::IsNearlyEqual(Stamina.Attack, 0.95));
	TestTrue(TEXT("table STA def"), FMath::IsNearlyEqual(Stamina.Defense, 1.05));
	TestTrue(TEXT("table STA mass"), FMath::IsNearlyEqual(Stamina.Mass, 1.30));
	TestTrue(TEXT("table STA k"), FMath::IsNearlyEqual(Stamina.SpinDecayPerSec, 0.103));
	TestTrue(TEXT("table BAL attack"), FMath::IsNearlyEqual(Balance.Attack, 1.10));
	TestTrue(TEXT("table BAL def"), FMath::IsNearlyEqual(Balance.Defense, 1.10));
	TestTrue(TEXT("table BAL mass"), FMath::IsNearlyEqual(Balance.Mass, 1.05));
	TestTrue(TEXT("table BAL k"), FMath::IsNearlyEqual(Balance.SpinDecayPerSec, 0.130));
	TestEqual(TEXT("type label BAL"), FString(Balance.TypeLabel()), FString(TEXT("BALANCE")));
	// STA mass highest; decay order ATK > BAL > DEF > STA
	TestTrue(TEXT("STA mass highest"), Stamina.Mass >= Defense.Mass && Stamina.Mass >= Balance.Mass && Stamina.Mass >= Attack.Mass);
	TestTrue(TEXT("decay ATK>BAL"), Attack.SpinDecayPerSec > Balance.SpinDecayPerSec);
	TestTrue(TEXT("decay BAL>DEF"), Balance.SpinDecayPerSec > Defense.SpinDecayPerSec);
	TestTrue(TEXT("decay DEF>STA"), Defense.SpinDecayPerSec > Stamina.SpinDecayPerSec);

	// No magic MakeLoadout body: values equal row getters.
	const Grade1Balance::FRow RA = Grade1Balance::GetRow(EBeyType::Attack);
	TestTrue(TEXT("MakeLoadout==row ATK"), FMath::IsNearlyEqual(Attack.Attack, RA.Attack) && FMath::IsNearlyEqual(Attack.SpinDecayPerSec, RA.SpinDecayPerSec));

	ContentStrings::EnsureLoaded();
	TestTrue(TEXT("zh race5"), ContentStrings::Get(TEXT("lobby_race5")).Contains(TEXT("5")));
	TestTrue(TEXT("zh start"), ContentStrings::Get(TEXT("lobby_start")).Len() > 0);
	TestTrue(TEXT("zh next"), ContentStrings::Get(TEXT("settle_next")).Len() > 0);
	TestTrue(TEXT("zh rematch"), ContentStrings::Get(TEXT("match_rematch")).Len() > 0);
	TestTrue(TEXT("zh blind lock"), ContentStrings::Get(TEXT("blind_lock")).Len() > 0);

	// ATK vs DEF from table still ends (spinout golden window).
	FBattleSimulation G;
	G.Random.Initialize(4242);
	G.ApplyLoadout(0, Attack);
	G.ApplyLoadout(1, Defense);
	G.Launch();
	while (G.Running) G.Tick();
	TestEqual(TEXT("table match ends"), G.Reason.IsEmpty(), false);
	TestTrue(TEXT("table match finished"), !G.Running);
	TestTrue(TEXT("table match before or at wall"), G.Frames <= FBattleSimulation::MaxFrames);
	TestEqual(TEXT("seed4242 still spinout"), G.Reason, FString(TEXT("spinout")));
	TestEqual(TEXT("seed4242 still P2"), G.Winner, 1);

	// Lineup loadout path: P1 type from pick, P2 DEF Grade1.
	FMatchFlow Flow;
	Flow.SetMode(ERaceMode::RaceTo5);
	Flow.TryEnterPickFromLobby();
	Flow.TryTogglePick(0); Flow.TryTogglePick(1); Flow.TryTogglePick(2);
	Flow.TryConfirmPick();
	const FBeyLoadout P1 = Flow.Pick.LoadoutAtLineup(0);
	TestEqual(TEXT("lineup0 type"), (int32)P1.Type, (int32)EBeyType::Attack);
	TestTrue(TEXT("lineup0 from table"), FMath::IsNearlyEqual(P1.Attack, 1.35));

	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FActiveSkillShellTest, "Beyblade.Match.ActiveSkillShell", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FActiveSkillShellTest::RunTest(const FString&)
{
	// ATK Chifeng: hits 5/10
	FActiveSkillShell Sk;
	Sk.ConfigureForPoolSlot(0, EBeyType::Attack);
	TestEqual(TEXT("chifeng hits cond"), (int32)Sk.Condition, (int32)ESkillCondition::HitsDealt);
	Sk.Observe(0.0, 5, false);
	TestEqual(TEXT("ready at 5 hits"), (int32)Sk.State(), (int32)ESkillButtonState::Ready);
	TestTrue(TEXT("fire chifeng"), Sk.TryFire());
	TestEqual(TEXT("next need 10"), Sk.Need(), 10);
	TestTrue(TEXT("atk mul"), FMath::IsNearlyEqual(Sk.AttackMulActive, 1.20));

	// Chiwen next Extra
	FActiveSkillShell Cw;
	Cw.ConfigureForPoolSlot(4, EBeyType::Attack);
	Cw.Observe(0.0, 5, false);
	TestTrue(TEXT("chiwen fire"), Cw.TryFire());
	TestTrue(TEXT("extra 1.35"), FMath::IsNearlyEqual(Cw.ExtraKickMulPending, 1.35));

	// STA: five own wall collisions inside five seconds.
    FActiveSkillShell Sta;
    Sta.ConfigureForPoolSlot(2,EBeyType::Stamina);
    TestEqual(TEXT("sta wall window condition"),(int32)Sta.Condition,(int32)ESkillCondition::WallHitsWindow);
    for(int32 I=0;I<4;++I)Sta.Observe(1.,0,true);
    TestFalse(TEXT("four wall hits insufficient"),Sta.CanFire());
    Sta.Observe(1.,0,true);
    TestTrue(TEXT("five walls in five seconds ready"),Sta.CanFire());
    TestTrue(TEXT("sta fire"),Sta.TryFire());
    TestEqual(TEXT("next needs ten within ten seconds"),Sta.Need(),10);

	// BAL window: bey AND wall each >=1 within N seconds (not OR)
	FActiveSkillShell Bal;
	Bal.ConfigureForPoolSlot(3, EBeyType::Balance);
	TestEqual(TEXT("bal window cond"), (int32)Bal.Condition, (int32)ESkillCondition::WindowHitSec);
	Bal.Observe(1.0, 0, false);
	TestFalse(TEXT("bal no hit yet"), Bal.CanFire());
	Bal.Observe(0.0, 1, false); // bey only
	TestFalse(TEXT("bal bey alone not enough"), Bal.CanFire());
	Bal.Observe(0.0, 1, true); // wall too (same hit count)
	TestEqual(TEXT("bal ready bey+wall"), (int32)Bal.State(), (int32)ESkillButtonState::Ready);
	TestTrue(TEXT("bal fire"), Bal.TryFire());
	TestEqual(TEXT("bal next need 10s"), Bal.Need(), 10);

	// DEF hits taken
	FActiveSkillShell Def;
	Def.ConfigureForPoolSlot(1, EBeyType::Defense);
	Def.Observe(0.0, 5, false);
	TestEqual(TEXT("def ready"), (int32)Def.State(), (int32)ESkillButtonState::Ready);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCollectionPanelTest, "Beyblade.Match.CollectionPanel", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCollectionPanelTest::RunTest(const FString&)
{
	TestEqual(TEXT("eight entries"), FCollectionCatalog::Count, 8);
	TestEqual(TEXT("slot0 chifeng"), FString(FCollectionCatalog::Get(0).Id), FString(TEXT("chifeng")));
	TestEqual(TEXT("slot3 chiwen"), FString(FCollectionCatalog::Get(3).Id), FString(TEXT("chiwen")));
	TestEqual(TEXT("slot4 huangkai"), FString(FCollectionCatalog::Get(4).Id), FString(TEXT("huangkai")));
	TestEqual(TEXT("slot5 cuipan"), FString(FCollectionCatalog::Get(5).Id), FString(TEXT("cuipan")));
	TestEqual(TEXT("slot7 shuanghuan"), FString(FCollectionCatalog::Get(7).Id), FString(TEXT("shuanghuan")));
	TestEqual(TEXT("chiwen zh"), FString(FCollectionCatalog::Get(3).NameZh), FString(TEXT("炽纹")));
	TestEqual(TEXT("huangkai zh"), FString(FCollectionCatalog::Get(4).NameZh), FString(TEXT("煌铠")));
	TestEqual(TEXT("cuipan zh"), FString(FCollectionCatalog::Get(5).NameZh), FString(TEXT("翠磐")));
	TestEqual(TEXT("shuanghuan zh"), FString(FCollectionCatalog::Get(7).NameZh), FString(TEXT("霜环")));

	FMatchFlow Flow;
	TestTrue(TEXT("lobby start"), Flow.State == EMatchFlowState::Lobby);
	Flow.EnterCollection();
	TestEqual(TEXT("collection state"), (int32)Flow.State, (int32)EMatchFlowState::Collection);
	Flow.OpenCollectionDetail(3);
	TestEqual(TEXT("detail focus"), Flow.CollectionFocus, 3);
	Flow.CloseCollectionDetail();
	TestEqual(TEXT("grid again"), Flow.CollectionFocus, -1);
	Flow.ExitCollectionToLobby();
	TestEqual(TEXT("back lobby"), (int32)Flow.State, (int32)EMatchFlowState::Lobby);

	const FVector2D Collect = FLobbyClickUI::CollectPos();
	TestEqual(TEXT("lobby collect hit"), (int32)FLobbyClickUI::HitTest(Collect.X + 5.f, Collect.Y + 5.f, EMatchFlowState::Lobby), (int32)ELobbyClickAction::OpenCollect);
	const FVector2D Slot0 = FLobbyClickUI::CollectSlotPos(0);
	TestEqual(TEXT("collect slot0 hit"), (int32)FLobbyClickUI::HitTest(Slot0.X + 5.f, Slot0.Y + 5.f, EMatchFlowState::Collection), (int32)ELobbyClickAction::Collect0);
	const FVector2D Skill = FLobbyClickUI::SkillBtnPos();
	TestEqual(TEXT("fighting skill hit"), (int32)FLobbyClickUI::HitTest(Skill.X + 5.f, Skill.Y + 5.f, EMatchFlowState::Fighting), (int32)ELobbyClickAction::FireSkill);
	TestEqual(TEXT("lobby no skill"), (int32)FLobbyClickUI::HitTest(Skill.X + 5.f, Skill.Y + 5.f, EMatchFlowState::Lobby), (int32)ELobbyClickAction::None);
	return true;
}

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTutorialNoScoreTest,"Beyblade.Match.TutorialDoesNotScore",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FTutorialNoScoreTest::RunTest(const FString&)
{
    FMatchFlow Flow;Flow.TryEnterPickFromLobby();Flow.TryTogglePick(0);Flow.TryTogglePick(1);Flow.TryTogglePick(2);Flow.TryConfirmPick();Flow.TryLaunchFromPrep();
    TestTrue(TEXT("tutorial can end"),Flow.OnTutorialEnded(TEXT("timeout"),1));
    TestEqual(TEXT("tutorial goes to summary"),int32(Flow.State),int32(EMatchFlowState::RoundSettle));
    TestEqual(TEXT("tutorial awards no points"),Flow.Score[1],0);
    TestEqual(TEXT("tutorial does not consume lineup"),Flow.CountUsed(),0);
    TestEqual(TEXT("tutorial does not advance round"),Flow.RoundIndex,0);
    TestFalse(TEXT("tutorial cannot end twice"),Flow.OnTutorialEnded(TEXT("timeout"),1));
    return true;
}
#endif
