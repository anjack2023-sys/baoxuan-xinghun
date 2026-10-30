#include "ArenaWalker.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Animation/AnimSequence.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

AArenaWalker::AArenaWalker()
{
    PrimaryActorTick.bCanEverTick = true;
    GetCapsuleComponent()->InitCapsuleSize(34, 96);
    GetCharacterMovement()->MaxWalkSpeed = 240;
    GetCharacterMovement()->bOrientRotationToMovement = true;
    GetCharacterMovement()->RotationRate = FRotator(0, 480, 0);
    bUseControllerRotationYaw = false;
    Arm = CreateDefaultSubobject<USpringArmComponent>(TEXT("ExploreArm"));
    Arm->SetupAttachment(GetRootComponent()); Arm->TargetArmLength = 270;
    Arm->TargetOffset = FVector(0, 0, 65); Arm->bUsePawnControlRotation = true;
    View = CreateDefaultSubobject<UCameraComponent>(TEXT("ExploreCamera"));
    View->SetupAttachment(Arm); View->FieldOfView = 75;
    auto* Fill = CreateDefaultSubobject<UPointLightComponent>(TEXT("HeroSoftFill"));
    Fill->SetupAttachment(View); Fill->SetRelativeLocation(FVector(80, 0, 80));
    Fill->SetIntensity(250); Fill->SetAttenuationRadius(650); Fill->SetCastShadows(false);
}
void AArenaWalker::BeginPlay()
{
    Super::BeginPlay();
    bAIAvatar=FParse::Param(FCommandLine::Get(),TEXT("AIAvatars")) || FParse::Param(FCommandLine::Get(),TEXT("AvatarSelection"));
    LoadAvatar();
}
void AArenaWalker::LoadAvatar()
{
    USkeletalMesh* HeroMesh=nullptr;
    if(bAIAvatar)
    {
        const FString Base=FString::Printf(TEXT("/Game/FeelLab/Characters/AIAvatars/%s/"),bGrok?TEXT("GROK"):TEXT("GPT"));
        HeroMesh=LoadObject<USkeletalMesh>(nullptr,*(Base+(bGrok?TEXT("SK_GROK"):TEXT("SK_GPT"))));
        Idle=LoadObject<UAnimSequence>(nullptr,*(Base+TEXT("A_Idle")));
        Walk=LoadObject<UAnimSequence>(nullptr,*(Base+TEXT("A_Walk")));
        Run=LoadObject<UAnimSequence>(nullptr,*(Base+TEXT("A_Run")));
    }
    else
    {
    HeroMesh = LoadObject<USkeletalMesh>(nullptr, TEXT("/Game/FeelLab/Characters/PortraitRefinedV3/Male/SK_MaleIdleLit.SK_MaleIdleLit"));
    Idle = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/FeelLab/Characters/MaleLauncher_v1/SK_MaleLauncher_Anim_standing_relax_001.SK_MaleLauncher_Anim_standing_relax_001"));
    Walk = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/FeelLab/Characters/MaleLauncher_v1/SK_MaleLauncher_Anim_walk_001.SK_MaleLauncher_Anim_walk_001"));
        Run=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/FeelLab/Characters/MaleLauncher_v1/SK_MaleLauncher_Anim_run_001"));
    }
    if (!ensure(HeroMesh && Idle && Walk)) return;
    const auto Bounds = HeroMesh->GetBounds();
    const double Scale = 180. / (2. * Bounds.BoxExtent.Z);
    GetMesh()->SetSkeletalMesh(HeroMesh); GetMesh()->SetRelativeScale3D(FVector(Scale));
    GetMesh()->SetRelativeLocation(FVector(0, 0, -96. - (Bounds.Origin.Z - Bounds.BoxExtent.Z) * Scale));
    GetMesh()->SetRelativeRotation(FRotator(0, -90, 0));
    GetMesh()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    GetMesh()->PlayAnimation(Idle, true);Current=Idle;
}
void AArenaWalker::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if(bPreviewFrozen) return;
    const double Speed=GetVelocity().Size2D();
    UAnimSequence* Desired=Speed>25 ? (bRunning && Run ? Run.Get() : Walk.Get()) : Idle.Get();
    if(Desired && Desired!=Current)
    {
        GetMesh()->PlayAnimation(Desired,true);Current=Desired;
    }
}
void AArenaWalker::SetRunning(bool Running)
{
    bRunning=Running;GetCharacterMovement()->MaxWalkSpeed=bAIAvatar?(Running?300:150):(Running?400:240);
}
void AArenaWalker::ToggleAvatar()
{
    if(!bAIAvatar)return;
    bGrok=!bGrok;LoadAvatar();
    UE_LOG(LogTemp,Display,TEXT("AI_AVATAR_WALKER character=%s"),bGrok?TEXT("GROK"):TEXT("GPT"));
}

void AArenaWalker::PreviewAvatar(USkeletalMesh* AvatarMesh,UAnimSequence* Animation)
{
    if(!AvatarMesh || !Animation || AvatarMesh->GetSkeleton()!=Animation->GetSkeleton()) return;
    const auto Bounds=AvatarMesh->GetBounds();
    if(Bounds.BoxExtent.Z<=0.) return;
    const double Scale=180./(2.*Bounds.BoxExtent.Z);
    GetMesh()->SetSkeletalMesh(AvatarMesh);GetMesh()->EmptyOverrideMaterials();GetMesh()->SetRelativeScale3D(FVector(Scale));
    GetMesh()->SetRelativeLocation(FVector(0,0,-96.-(Bounds.Origin.Z-Bounds.BoxExtent.Z)*Scale));
    const FString Name=AvatarMesh->GetName();
    const bool HasLocomotion=Name==TEXT("SK_GPT") || Name==TEXT("SK_GROK");
    if (HasLocomotion)
    {
        const FString Base=FString::Printf(TEXT("/Game/FeelLab/Characters/AIAvatars/%s/"),Name==TEXT("SK_GPT") ? TEXT("GPT") : TEXT("GROK"));
        UAnimSequence* NewIdle=LoadObject<UAnimSequence>(nullptr,*(Base+TEXT("A_Idle")));
        UAnimSequence* NewWalk=LoadObject<UAnimSequence>(nullptr,*(Base+TEXT("A_Walk")));
        UAnimSequence* NewRun=LoadObject<UAnimSequence>(nullptr,*(Base+TEXT("A_Run")));
        if (NewIdle && NewWalk && NewRun && NewIdle->GetSkeleton()==AvatarMesh->GetSkeleton() && NewWalk->GetSkeleton()==AvatarMesh->GetSkeleton() && NewRun->GetSkeleton()==AvatarMesh->GetSkeleton())
        {
            Idle=NewIdle; Walk=NewWalk; Run=NewRun; Current=Idle;
            GetMesh()->PlayAnimation(Idle,true);GetMesh()->SetPlayRate(1);
            bPreviewFrozen=false;
            return;
        }
    }
    // shortcut: these characters have no compatible locomotion clips; bind walk/run when supplied.
    GetMesh()->PlayAnimation(Animation,false);GetMesh()->SetPlayRate(0);GetMesh()->SetPosition(0,false);
    bPreviewFrozen=true;
}
