#include "SkillRuntime.h"
#include "Misc/AutomationTest.h"

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSkillEffectsTest,"Beyblade.Skills.EffectsAndExpiry",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSkillEffectsTest::RunTest(const FString&)
{
    for(const TCHAR* Id:{TEXT("chifeng"),TEXT("bilei"),TEXT("changxuan"),TEXT("hengblade"),TEXT("chiwen"),TEXT("huangkai"),TEXT("cuipan"),TEXT("shuanghuan")})
    {
        FBattleSimulation S; S.Reset(); S.Attack[0]=1.; S.Defense[0]=1.; S.Mass[0]=1.; S.SpinDecay[0]=.1;
        FActiveSkillShell K; K.ResetForBout(); K.ConfigureForId(Id); K.BeginEffects(S,0);
        TestTrue(TEXT("active data exists"),K.ActiveData.Valid); TestTrue(TEXT("passive data exists"),K.PassiveData.Valid);
        const double PassiveAttack=S.Attack[0],PassiveDefense=S.Defense[0],PassiveDecay=S.SpinDecay[0],PassiveMass=S.Mass[0];
        K.HitsDealt=K.HitsTaken=5; K.QuietSec=5; if(K.Condition==ESkillCondition::WallHitsWindow)for(int32 J=0;J<5;++J)K.Observe(.1,0,true); K.bWindowGotBey=K.bWindowGotWall=true;
        TestTrue(TEXT("qualified skill is ready and lights flame"),K.CanFire());
        TestTrue(TEXT("qualified skill fires"),K.TryFire());
        TestFalse(TEXT("fired skill extinguishes flame immediately"),K.CanFire());
        TestFalse(TEXT("holding or repeating key cannot fire active skill twice"),K.TryFire()); K.ApplyEffects(S,0);
        const FString Name(Id);
        if(Name==TEXT("bilei")) TestTrue(TEXT("iron wall actually raises defense"),FMath::IsNearlyEqual(S.Defense[0],1.10*1.25));
        if(Name==TEXT("changxuan")) TestTrue(TEXT("renewal reduces decay"),FMath::IsNearlyEqual(S.SpinDecay[0],.1*.92*.75));
        if(Name==TEXT("hengblade")) {TestTrue(TEXT("balance attack"),FMath::IsNearlyEqual(S.Attack[0],1.05*1.15));TestTrue(TEXT("balance defense"),FMath::IsNearlyEqual(S.Defense[0],1.05*1.10));}
        if(Name==TEXT("cuipan")) {TestTrue(TEXT("stone mass"),FMath::IsNearlyEqual(S.Mass[0],1.15));TestTrue(TEXT("stone wear"),FMath::IsNearlyEqual(S.PassiveWearMul[0],.88));}
        if(Name==TEXT("shuanghuan")) TestTrue(TEXT("frost enemy decay multiplier"),FMath::IsNearlyEqual(S.SkillEnemyDecayMul[0],1.12));
        if(Name==TEXT("huangkai")) {TestTrue(TEXT("shield absorbs"),FMath::IsNearlyEqual(S.SkillIncomingMul[0],.92*.75));TestTrue(TEXT("shield reflects"),FMath::IsNearlyEqual(S.SkillReflect[0],.25));}
        if(K.ActiveData.Duration>0.) {K.TickFx(K.ActiveData.Duration-.01);TestTrue(TEXT("active until duration"),K.bFxActive);K.TickFx(.02);}
        else K.NotifyExtraConsumed();
        K.ApplyEffects(S,0);
        TestFalse(TEXT("effect expires/consumes"),K.bFxActive);
        TestTrue(TEXT("attack restored without stacking"),FMath::IsNearlyEqual(S.Attack[0],PassiveAttack));
        TestTrue(TEXT("defense restored"),FMath::IsNearlyEqual(S.Defense[0],PassiveDefense));
        TestTrue(TEXT("decay restored"),FMath::IsNearlyEqual(S.SpinDecay[0],PassiveDecay));
        TestTrue(TEXT("mass restored"),FMath::IsNearlyEqual(S.Mass[0],PassiveMass));
        TestEqual(TEXT("next tier"),K.Need(),10);
        K.ApplyEffects(S,0);TestTrue(TEXT("repeat recompute does not stack"),FMath::IsNearlyEqual(S.Attack[0],PassiveAttack));
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSkillContactsTest,"Beyblade.Skills.ContactOwnershipAndWindows",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSkillContactsTest::RunTest(const FString&)
{
    FBattleSimulation S; S.Reset(); FActiveSkillShell K; K.ConfigureForId(TEXT("changxuan")); K.BeginEffects(S,0);
    S.bWallContact[1]=true;K.AfterStep(S,0,.1);
    TestEqual(TEXT("opponent wall does not charge my skill"),K.WallHitTimes.Num(),0);
    S.bWallContact[0]=true;K.AfterStep(S,0,.1);
    TestEqual(TEXT("own wall charges skill"),K.WallHitTimes.Num(),1);
    FActiveSkillShell B;B.ConfigureForId(TEXT("hengblade"));B.Observe(1.,1,false);B.Observe(6.,1,true);
    TestFalse(TEXT("old bey contact outside window cannot qualify"),B.CanFire());
    B.Observe(.1,2,false);TestTrue(TEXT("recent bey plus wall qualifies"),B.CanFire());
    B.Observe(6.,2,false);TestFalse(TEXT("unspent ready expires when both contacts age out"),B.CanFire());
    FActiveSkillShell C;C.ConfigureForId(TEXT("chiwen"));C.BeginEffects(S,0);S.Hits=1;S.PassiveDealt[0]=1;C.AfterStep(S,0,.01);
    TestTrue(TEXT("pursuit passive on hit"),FMath::IsNearlyEqual(S.Attack[0],C.BaselineAttack*1.06*1.04));
    C.AfterStep(S,0,2.51);TestTrue(TEXT("pursuit passive expires"),FMath::IsNearlyEqual(S.Attack[0],C.BaselineAttack*1.06));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStaminaWallWindowTest,"Beyblade.Skills.StaminaWallWindow",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FStaminaWallWindowTest::RunTest(const FString&)
{
    for(const TCHAR* Id:{TEXT("changxuan"),TEXT("cuipan")})
    {
        FActiveSkillShell K;K.ConfigureForId(Id);K.ResetForBout();
        K.Observe(1.,10,false);TestFalse(TEXT("bey hits do not charge stamina"),K.CanFire());
        for(int32 I=0;I<5;++I)K.Observe(1.,10,true);
        TestTrue(TEXT("five own walls qualify"),K.CanFire());
        K.Observe(5.01,10,false);TestFalse(TEXT("old contacts expire without firing"),K.CanFire());
        for(int32 I=0;I<5;++I)K.Observe(.1,10,true);
        TestTrue(TEXT("can build a fresh rolling window"),K.TryFire());
        TestEqual(TEXT("fire clears wall history"),K.WallHitTimes.Num(),0);
        TestEqual(TEXT("next tier is ten"),K.Need(),10);
        K.Observe(1.,10,true);TestEqual(TEXT("effect does not bank wall hits"),K.WallHitTimes.Num(),0);
        K.TickFx(K.ActiveData.Duration+.01);
        for(int32 I=0;I<9;++I)K.Observe(1.,10,true);
        TestFalse(TEXT("nine do not meet second tier"),K.CanFire());
        K.Observe(1.,10,true);TestTrue(TEXT("ten in ten seconds qualify"),K.CanFire());
        K.ResetForBout();TestEqual(TEXT("new bout returns to five"),K.Need(),5);
        TestEqual(TEXT("new bout clears wall window"),K.WallHitTimes.Num(),0);
        K.Observe(0.,0,true);K.Observe(5.,0,false);
        TestEqual(TEXT("exact five-second boundary included"),K.WallHitTimes.Num(),1);
        K.Observe(.001,0,false);TestEqual(TEXT("outside five-second boundary excluded"),K.WallHitTimes.Num(),0);
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSkillProgressDisplayTest,"Beyblade.Skills.ProgressDisplay",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSkillProgressDisplayTest::RunTest(const FString&)
{
    FActiveSkillShell Attack;Attack.ConfigureForId(TEXT("chifeng"));Attack.ResetForBout();
    Attack.Observe(0.,21,false);
    TestTrue(TEXT("overcharged skill remains ready"),Attack.CanFire());
    TestEqual(TEXT("display clamps to current threshold"),Attack.ProgressLabel(),FString(TEXT("碰撞 5/5")));
    TestEqual(TEXT("display does not change actual contacts"),Attack.HitsDealt,21);
    TestTrue(TEXT("ready skill fires"),Attack.TryFire());
    TestEqual(TEXT("next threshold advances and resets"),Attack.ProgressLabel(),FString(TEXT("碰撞 0/10")));
    FActiveSkillShell Defense;Defense.ConfigureForId(TEXT("bilei"));Defense.ResetForBout();Defense.Observe(0.,12,false);
    TestEqual(TEXT("defense progress is labeled and clamped"),Defense.ProgressLabel(),FString(TEXT("受击 5/5")));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSkillDataTest,"Beyblade.Skills.DataValidation",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSkillDataTest::RunTest(const FString&)
{
    TestEqual(TEXT("all sixteen rows loaded"),SkillBalance::Rows().Num(),16);
    SkillBalance::FRow Row;
    TestFalse(TEXT("missing fields rejected"),SkillBalance::Parse(TEXT("chifeng,active"),Row));
    TestFalse(TEXT("negative multiplier rejected"),SkillBalance::Parse(TEXT("x,active,x,x,x,x,x,-1,mul,x,x,3,,1"),Row));
    TestFalse(TEXT("nonnumeric rejected"),SkillBalance::Parse(TEXT("x,active,x,x,x,x,x,no,mul,x,x,3,,1"),Row));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FWeightedSkillMassTest,"Beyblade.Skills.WeightedMassNotDoubled",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FWeightedSkillMassTest::RunTest(const FString&)
{
    FBattleSimulation A,B;
    for (auto* S:{&A,&B})
    {
        S->Reset();S->bWeightCollision=true;S->Mass[0]=1.15;
        S->Position[0]=FVector2D(-.2,0);S->Position[1]=FVector2D(.2,0);
        S->Velocity[0]=FVector2D(2,0);S->Velocity[1]=FVector2D(-2,0);
    }
    B.SkillMassScale[0]=1.15;
    A.Collide();B.Collide();
    TestTrue(TEXT("skill mass already included in weighted impulse"),A.Velocity[0].Equals(B.Velocity[0],1.e-9) && A.Velocity[1].Equals(B.Velocity[1],1.e-9));
    return true;
}
#endif

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FChiwenNextHitLifetimeTest,"Beyblade.Skills.ChiwenNextHitLifetime",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FChiwenNextHitLifetimeTest::RunTest(const FString&)
{
    FBattleSimulation S;S.Reset();FActiveSkillShell K;K.ResetForBout();K.ConfigureForId(TEXT("chiwen"));K.BeginEffects(S,0);
    K.Observe(0.,4,false);TestFalse(TEXT("four hits do not qualify"),K.TryFire());
    K.Observe(0.,5,false);TestTrue(TEXT("fifth hit qualifies"),K.TryFire());
    TestTrue(TEXT("extra kick is 1.35"),FMath::IsNearlyEqual(K.ExtraKickMulPending,1.35));
    K.TickFx(20.);TestTrue(TEXT("armed charge has no video timeout"),K.bFxActive);
    S.Hits=5;S.bWallContact[0]=true;K.AfterStep(S,0,S.Step);
    TestTrue(TEXT("wall does not consume charged hit"),K.bFxActive);
    S.bWallContact[0]=false;S.Hits=6;K.AfterStep(S,0,S.Step);
    TestFalse(TEXT("next bey collision consumes charge"),K.bFxActive);
    TestTrue(TEXT("extra restored after consumption"),FMath::IsNearlyEqual(K.ExtraKickMulPending,1.));
    TestEqual(TEXT("next recharge tier"),K.Need(),10);return true;
}
#endif

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEightBeySkillsTest,"Beyblade.Skills.EightBeyMapping",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FEightBeySkillsTest::RunTest(const FString&)
{
    const TCHAR* Ids[]={TEXT("chifeng"),TEXT("bilei"),TEXT("changxuan"),TEXT("hengblade"),TEXT("chiwen"),TEXT("huangkai"),TEXT("cuipan"),TEXT("shuanghuan")};
    for(int32 I=0;I<8;++I){FActiveSkillShell K;K.ConfigureForPoolSlot(I,EBeyType::Attack);TestEqual(TEXT("slot maps its actual skill"),K.BeyId,FString(Ids[I]));TestTrue(TEXT("active row exists"),K.ActiveData.Valid);}
    FBattleSimulation S;S.Reset();FActiveSkillShell Gold;Gold.ResetForBout();Gold.ConfigureForId(TEXT("huangkai"));Gold.BeginEffects(S,0);
    Gold.Observe(0.,5,false);TestTrue(TEXT("gold charges from five contacts"),Gold.TryFire());Gold.ApplyEffects(S,0);
    TestTrue(TEXT("gold absorbs incoming kick"),FMath::IsNearlyEqual(S.SkillIncomingMul[0],.92*.75));TestTrue(TEXT("gold reflects quarter"),FMath::IsNearlyEqual(S.SkillReflect[0],.25));
    Gold.TickFx(20.);TestTrue(TEXT("gold waits for next collision"),Gold.bFxActive);S.Hits=6;Gold.AfterStep(S,0,S.Step);TestFalse(TEXT("gold consumed on hit"),Gold.bFxActive);
    TestEqual(TEXT("reflection clears after use"),S.SkillReflect[0],0.);return true;
}
#endif

#if WITH_DEV_AUTOMATION_TESTS
#include "IronWallEffectComponent.h"
#include "ChangxuanEffectComponent.h"
#include "HengrenEffectComponent.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Components/StaticMeshComponent.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMixedVariantComponentsTest,"Beyblade.Skills.MixedVariantComponents",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMixedVariantComponentsTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    AActor* Actor=World->SpawnActor<AActor>();
    auto* Root=NewObject<USceneComponent>(Actor);Actor->SetRootComponent(Root);Root->RegisterComponent();
    for(bool Variant:{false,true}) {
        auto* Gold=NewObject<UIronWallEffectComponent>(Actor);Gold->SetupAttachment(Root);Gold->RegisterComponent();TestTrue(TEXT("shield variant initializes together"),Gold->InitializeVisuals(Variant));
        auto* Stone=NewObject<UChangxuanEffectComponent>(Actor);Stone->SetupAttachment(Root);Stone->RegisterComponent();TestTrue(TEXT("stamina variant initializes together"),Stone->InitializeVisuals(Variant));
        auto* Frost=NewObject<UHengrenEffectComponent>(Actor);Frost->SetupAttachment(Root);Frost->RegisterComponent();TestTrue(TEXT("balance variant initializes together"),Frost->InitializeVisuals(Variant));
    }
    TArray<UStaticMeshComponent*> Parts;Actor->GetComponents(Parts);TestEqual(TEXT("all 26 visual parts coexist"),Parts.Num(),26);
    TSet<FName> Names;for(auto* Part:Parts){Names.Add(Part->GetFName());TestFalse(TEXT("no visual component collides"),Part->IsCollisionEnabled());}
    TestEqual(TEXT("all names unique on shared actor"),Names.Num(),26);
    World->DestroyActor(Actor);World->DestroyWorld(false);return true;
}
#endif

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTalentsPassivesTest,"Beyblade.Skills.TalentsAndPassives",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FTalentsPassivesTest::RunTest(const FString&)
{
    for(int32 I=0;I<2;++I)
    {
        auto Setup=[&](const TCHAR* Id,FBattleSimulation& S,FActiveSkillShell& K) {
            S.Reset();S.Attack[I]=S.Defense[I]=S.Mass[I]=1.;S.SpinDecay[I]=.1;
            K.ResetForBout();K.ConfigureForId(Id);K.BeginEffects(S,I);
        };
        auto Hit=[&](FBattleSimulation& S,FActiveSkillShell& K,bool Dealt,bool Taken) {
            ++S.Hits;if(Dealt)++S.PassiveDealt[I];if(Taken)++S.PassiveTaken[I];K.AfterStep(S,I,.01);
        };
        FBattleSimulation S;FActiveSkillShell K;
        Setup(TEXT("chifeng"),S,K);K.AfterStep(S,I,3.);
        TestEqual(TEXT("red arms after quiet gap"),S.PassiveOutgoingMul[I],1.2);
        Hit(S,K,true,false);TestEqual(TEXT("red consumes next contact"),S.PassiveOutgoingMul[I],1.);
        Setup(TEXT("chiwen"),S,K);
        for(int32 N=0;N<5;++N)Hit(S,K,true,false);
        TestEqual(TEXT("fire capped at three stacks"),K.PassiveStacks,3);
        TestTrue(TEXT("fire talent times three stacks"),FMath::IsNearlyEqual(S.Attack[I],1.06*1.12));
        K.AfterStep(S,I,2.51);TestEqual(TEXT("fire expires all stacks"),K.PassiveStacks,0);
        Hit(S,K,false,true);TestEqual(TEXT("being chased does not grant pursuit"),K.PassiveStacks,0);
        Setup(TEXT("bilei"),S,K);
        for(int32 N=0;N<3;++N)Hit(S,K,false,true);
        TestEqual(TEXT("wall ready after three taken"),S.PassiveOutgoingMul[I],1.2);
        Hit(S,K,false,true);TestEqual(TEXT("wall cannot bank more charges"),K.PassiveCharges,3);
        Hit(S,K,true,true);TestEqual(TEXT("wall consumes without recharging on same hit"),K.PassiveCharges,0);
        Setup(TEXT("huangkai"),S,K);S.Position[I]=FVector2D(S.TrapInnerR*S.ArenaScale+.1,0);K.ApplyEffects(S,I);
        TestTrue(TEXT("gold outer defense"),FMath::IsNearlyEqual(S.Defense[I],1.12));
        Hit(S,K,false,true);TestTrue(TEXT("gold multiplicative resistance"),FMath::IsNearlyEqual(S.SkillIncomingMul[I],.92*.85));
        K.AfterStep(S,I,1.51);Hit(S,K,false,true);TestEqual(TEXT("gold cooldown prevents refresh"),K.PassiveRemain,0.);
        K.AfterStep(S,I,4.5);Hit(S,K,false,true);TestEqual(TEXT("gold cooldown completes"),K.PassiveRemain,1.5);
        S.Position[I]=FVector2D::ZeroVector;K.ApplyEffects(S,I);TestEqual(TEXT("gold loses outer defense in center"),S.Defense[I],1.);
        Setup(TEXT("changxuan"),S,K);K.AfterStep(S,I,3.);
        TestTrue(TEXT("quiet stacks with talent"),FMath::IsNearlyEqual(S.SpinDecay[I],.1*.92*.88));
        S.bWallContact[1-I]=true;K.AfterStep(S,I,.1);TestTrue(TEXT("enemy wall preserves quiet"),K.PassiveQuiet>3.);
        S.bWallContact[I]=true;K.AfterStep(S,I,.01);TestEqual(TEXT("own wall breaks quiet"),K.PassiveQuiet,0.);
        Setup(TEXT("cuipan"),S,K);Hit(S,K,false,true);K.AfterStep(S,I,1.);Hit(S,K,false,true);
        TestEqual(TEXT("stone refreshes resistance"),K.PassiveRemain,2.);
        TestEqual(TEXT("stone resists knockback"),S.SkillIncomingMul[I],.85);
        K.AfterStep(S,I,2.01);TestEqual(TEXT("stone resistance expires"),S.SkillIncomingMul[I],1.);
        Setup(TEXT("hengblade"),S,K);Hit(S,K,true,true);
        TestTrue(TEXT("mutual hit chooses defensive stance"),FMath::IsNearlyEqual(S.Defense[I],1.05*1.10));
        Hit(S,K,false,true);TestTrue(TEXT("taken switches to attack"),FMath::IsNearlyEqual(S.Attack[I],1.05*1.10));
        TestTrue(TEXT("previous stance removed"),FMath::IsNearlyEqual(S.Defense[I],1.05));
        Setup(TEXT("shuanghuan"),S,K);Hit(S,K,true,false);
        TestEqual(TEXT("frost debuff applies"),S.SkillEnemyDecayMul[I],1.10);
        K.bFxActive=true;K.ApplyEffects(S,I);TestTrue(TEXT("frost active and passive compose"),FMath::IsNearlyEqual(S.SkillEnemyDecayMul[I],1.10*1.12));K.bFxActive=false;
        K.AfterStep(S,I,3.01);Hit(S,K,true,false);TestEqual(TEXT("frost cooldown blocks reapply"),S.SkillEnemyDecayMul[I],1.);
        K.AfterStep(S,I,2.);Hit(S,K,true,false);TestEqual(TEXT("frost reapply after cooldown"),S.SkillEnemyDecayMul[I],1.10);
        K.ResetForBout();K.ApplyEffects(S,I);TestEqual(TEXT("bout reset clears debuff"),S.SkillEnemyDecayMul[I],1.);
        TestEqual(TEXT("bout reset clears cooldown"),K.PassiveCooldown,0.);
    }
    FBattleSimulation S;S.Reset();S.Position[0]=FVector2D(-.2,0);S.Position[1]=FVector2D(.2,0);
    S.Velocity[0]=FVector2D(4,0);S.Velocity[1]=FVector2D::ZeroVector;S.Collide();
    TestEqual(TEXT("approaching player owns outgoing contact"),S.PassiveDealt[0],1);
    TestEqual(TEXT("stationary player owns incoming contact"),S.PassiveTaken[1],1);
    TestEqual(TEXT("stationary player not outgoing"),S.PassiveDealt[1],0);
    S.Position[0]=FVector2D(-.2,0);S.Position[1]=FVector2D(.2,0);S.Velocity[0]=FVector2D(4,0);S.Velocity[1]=FVector2D::ZeroVector;S.Collide();
    TestEqual(TEXT("same contact cannot farm charges"),S.PassiveDealt[0],1);
    S.Position[1]=FVector2D(10,0);S.Collide();S.Position[0]=FVector2D(-.2,0);S.Position[1]=FVector2D(.2,0);
    S.Velocity[0]=FVector2D(4,0);S.Velocity[1]=FVector2D(-4,0);S.Collide();
    TestEqual(TEXT("separation permits fresh contact"),S.PassiveDealt[0],2);
    TestEqual(TEXT("head on counts both attackers"),S.PassiveDealt[1],1);
    return true;
}
#endif

#if WITH_DEV_AUTOMATION_TESTS
#include "BeyTrailHistory.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBeyTrailHistoryTest,"Beyblade.Presentation.TrailHistory",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FBeyTrailHistoryTest::RunTest(const FString&)
{
    FBeyTrailHistory T;
    T.Record(1,FVector(1,0,0),FVector(0,1,0));
    TestEqual(TEXT("odd frames do not sample"),T.Points[0].Num(),0);
    for(int32 F=2;F<=80;F+=2) T.Record(F,FVector(F,0,0),FVector(0,F,0));
    TestEqual(TEXT("history remains bounded"),T.Points[0].Num(),30);
    TestEqual(TEXT("oldest sample is dropped"),T.Points[0][0].X,22.);
    TestEqual(TEXT("both players tracked independently"),T.Points[1].Last().Y,80.);
    T.Reset();TestEqual(TEXT("bout clears previous trail"),T.Points[0].Num()+T.Points[1].Num(),0);
    return true;
}
#endif
