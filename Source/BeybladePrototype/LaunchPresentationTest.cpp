#include "LabLaunchPresentation.h"
#include "BoutPresentation.h"
#include "Animation/AnimSequence.h"
#include "Engine/SkeletalMesh.h"
#include "Sound/SoundBase.h"
#include "Misc/AutomationTest.h"
#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FIndustrialLaunchTimingTest,"Beyblade.Launch.Timing",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FIndustrialLaunchTimingTest::RunTest(const FString&)
{
    TestEqual(TEXT("no flight before release"),LabLaunch::Flight(1.),0.);
    TestEqual(TEXT("flight starts at hand"),LabLaunch::Flight(LabLaunch::Release),0.);
    TestEqual(TEXT("flight lands without overshoot"),LabLaunch::Flight(20.),1.);
    TestEqual(TEXT("pull reaches full extension"),LabLaunch::Pull(LabLaunch::Release),1.);
    TestEqual(TEXT("arms recover after launch"),LabLaunch::Raise(LabLaunch::Duration),0.);
    TestTrue(TEXT("flight remains monotonic"),LabLaunch::Flight(3.4)>LabLaunch::Flight(3.2));
    // Industrial HUD / apply paths share these via FLaunchSetup.
    TestEqual(TEXT("setup release matches timeline"),FLaunchSetup::ReleaseTime,LabLaunch::Release);
    TestEqual(TEXT("setup duration matches timeline"),FLaunchSetup::Duration,LabLaunch::Duration);
    TestTrue(TEXT("release is 2.9s"),FMath::IsNearlyEqual(FLaunchSetup::ReleaseTime,2.9,1.e-9));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FIndustrialLaunchAssetsTest,"Beyblade.Launch.ImportedAssets",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FIndustrialLaunchAssetsTest::RunTest(const FString&)
{
    auto* Mesh=LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/FeelLab/Characters/PortraitRefinedV3/Male/SK_MaleIdleLit.SK_MaleIdleLit"));
    if(!TestNotNull(TEXT("new hero mesh"),Mesh))return false;
    for(const TCHAR* Bone:{TEXT("R_Hand"),TEXT("L_Hand"),TEXT("R_Upperarm"),TEXT("R_Forearm"),TEXT("L_Upperarm"),TEXT("L_Forearm")})TestTrue(TEXT("IK bone exists"),Mesh->GetRefSkeleton().FindBoneIndex(Bone)>=0);
    for(const TCHAR* Name:{TEXT("standing_relax"),TEXT("walk"),TEXT("run"),TEXT("jump"),TEXT("agree"),TEXT("defeat_02"),TEXT("fold_arms"),TEXT("turn")})
    {
        auto* Anim=LoadObject<UAnimSequence>(nullptr,*FString::Printf(TEXT("/Game/FeelLab/Characters/MaleLauncher_v1/SK_MaleLauncher_Anim_%s_001.SK_MaleLauncher_Anim_%s_001"),Name,Name));
        if(TestNotNull(TEXT("exported clip exists"),Anim)){TestTrue(TEXT("clip has duration"),Anim->GetPlayLength()>0.);TestTrue(TEXT("clip uses new skeleton"),Anim->GetSkeleton()==Mesh->GetSkeleton());}
    }
    auto* Launch=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/FeelLab/Characters/PortraitRefinedV3/Male/A_Launch.A_Launch"));
    auto* LaunchMesh=LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/FeelLab/Characters/PortraitRefinedV3/Male/SK_MaleLaunch.SK_MaleLaunch"));
    if(TestNotNull(TEXT("approved animation"),Launch))TestTrue(TEXT("approved clip duration matches timeline"),FMath::Abs(Launch->GetPlayLength()-LabLaunch::Duration)<.001);
    if(TestNotNull(TEXT("approved mesh"),LaunchMesh))
    {
        TestTrue(TEXT("release socket bone exists"),LaunchMesh->GetRefSkeleton().FindBoneIndex(TEXT("LaunchSocket"))>=0);
        if(Launch)TestTrue(TEXT("approved clip skeleton matches mesh"),Launch->GetSkeleton()==LaunchMesh->GetSkeleton());
    }
    auto* Female=LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/FeelLab/Characters/PortraitRefinedV3/Female/SK_FemaleLaunch.SK_FemaleLaunch"));
    auto* FemaleClip=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/FeelLab/Characters/PortraitRefinedV3/Female/A_Launch.A_Launch"));
    if(TestNotNull(TEXT("female rigged mesh"),Female))TestTrue(TEXT("female release socket"),Female->GetRefSkeleton().FindBoneIndex(TEXT("LaunchSocket"))>=0);
    if(TestNotNull(TEXT("female launch clip"),FemaleClip))
    {
        TestTrue(TEXT("female timing matches male"),FMath::Abs(FemaleClip->GetPlayLength()-LabLaunch::Duration)<.001);
        if(Female)TestTrue(TEXT("female skeleton matches clip"),Female->GetSkeleton()==FemaleClip->GetSkeleton());
    }
    for(const TCHAR* Name:{TEXT("S_LaunchCount"),TEXT("S_LaunchPull"),TEXT("S_LaunchRelease")})
        TestNotNull(TEXT("launch sound exists"),LoadObject<USoundBase>(nullptr,*FString::Printf(TEXT("/Game/Beyblade/Audio/%s.%s"),Name,Name)));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FNewAvatarLaunchAssetsTest,"Beyblade.Launch.NewAvatarAssets",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FNewAvatarLaunchAssetsTest::RunTest(const FString&)
{
    for(const TCHAR* Name : {TEXT("DeepSeek"), TEXT("Doubao")})
    {
        const FString Base=FString::Printf(TEXT("/Game/FeelLab/Characters/AIAvatars/%s/"),Name);
        auto* Mesh=LoadObject<USkeletalMesh>(nullptr,*(Base+TEXT("SK_")+Name));
        auto* Anim=LoadObject<UAnimSequence>(nullptr,*(Base+TEXT("A_LaunchScaled")));
        if(TestNotNull(TEXT("character mesh"),Mesh)) TestTrue(TEXT("release socket exists"),Mesh->GetRefSkeleton().FindBoneIndex(TEXT("LaunchSocket"))>=0);
        if(TestNotNull(TEXT("launch animation"),Anim) && Mesh) TestTrue(TEXT("animation matches character skeleton"),Anim->GetSkeleton()==Mesh->GetSkeleton());
    }
    return true;
}
#endif
