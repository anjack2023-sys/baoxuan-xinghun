#include "IronWallEffectComponent.h"
#include "IronWallPresentation.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"

UIronWallEffectComponent::UIronWallEffectComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.bStartWithTickEnabled = false;
    PrimaryComponentTick.TickGroup = TG_PostPhysics;
    SetAbsolute(false, true, true);
}

bool UIronWallEffectComponent::InitializeVisuals(bool GoldMode)
{
    bGoldMode = GoldMode;
    auto* FieldMesh = LoadObject<UStaticMesh>(nullptr, GoldMode ? TEXT("/Game/Beyblade/FX/Extra/SM_GoldPanels.SM_GoldPanels") : TEXT("/Game/Beyblade/FX/IronWall/SM_IronWallField.SM_IronWallField"));
    auto* LineMesh = LoadObject<UStaticMesh>(nullptr, GoldMode ? TEXT("/Game/Beyblade/FX/Extra/SM_GoldLines.SM_GoldLines") : TEXT("/Game/Beyblade/FX/IronWall/SM_IronWallLines.SM_IronWallLines"));
    auto* RippleMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Game/Beyblade/FX/IronWall/SM_IronWallRipple.SM_IronWallRipple"));
    auto* GroundMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Game/Beyblade/FX/IronWall/SM_IronWallGround.SM_IronWallGround"));
    auto* FieldBase = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Beyblade/FX/IronWall/M_IronWallField.M_IronWallField"));
    auto* LineBase = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Beyblade/FX/IronWall/M_IronWallLines.M_IronWallLines"));
    if (!FieldMesh || !LineMesh || !RippleMesh || !GroundMesh || !FieldBase || !LineBase)
    { UE_LOG(LogTemp, Error, TEXT("IRON_WALL_MISSING_ASSET")); return false; }
    FieldMaterial = UMaterialInstanceDynamic::Create(FieldBase, this);
    LineMaterial = UMaterialInstanceDynamic::Create(LineBase, this);
    HitMaterial = UMaterialInstanceDynamic::Create(LineBase, this);
    LineMaterial->SetScalarParameterValue(TEXT("Strength"), 40.f);
    HitMaterial->SetScalarParameterValue(TEXT("Strength"), 50.f);
    HitMaterial->SetVectorParameterValue(TEXT("Tint"), FLinearColor(.25f, .65f, 1.f));
    if (GoldMode)
    {
        FieldMaterial->SetVectorParameterValue(TEXT("Tint"),FLinearColor(1.f,.5f,.035f));
        LineMaterial->SetVectorParameterValue(TEXT("Tint"),FLinearColor(1.f,.65f,.12f));
        HitMaterial->SetVectorParameterValue(TEXT("Tint"),FLinearColor(1.f,.8f,.25f));
    }
    auto Part = [&](const TCHAR* Name, UStaticMesh* Mesh, UMaterialInstanceDynamic* Material)
    {
        auto* Component = NewObject<UStaticMeshComponent>(GetOwner(), GoldMode ? FName(*(FString(TEXT("Gold_"))+Name)) : FName(Name));
        Component->SetupAttachment(this);
        Component->SetStaticMesh(Mesh);
        for (int32 I = 0; I < Component->GetNumMaterials(); ++I) Component->SetMaterial(I, Material);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetGenerateOverlapEvents(false);
        Component->SetCanEverAffectNavigation(false);
        Component->SetCastShadow(false);
        Component->SetRelativeScale3D(FVector(.2));
        Component->RegisterComponent();
        return Component;
    };
    Field = Part(TEXT("IronWallField"), FieldMesh, FieldMaterial);
    Lines = Part(TEXT("IronWallLines"), LineMesh, LineMaterial);
    GroundRing = Part(TEXT("IronWallGround"), GroundMesh, LineMaterial);
    Ripple = Part(TEXT("IronWallRipple"), RippleMesh, HitMaterial);
    SecondRipple = Part(TEXT("IronWallSecondRipple"), RippleMesh, HitMaterial);
    StartSound = LoadObject<USoundBase>(nullptr, TEXT("/Game/Beyblade/FX/IronWall/S_IronWallStart.S_IronWallStart"));
    ResetShield();
    return true;
}

void UIronWallEffectComponent::SetShieldEnabled(bool Enabled, float SoundVolume)
{
    if (!Field || bShieldEnabled == Enabled) return;
    bShieldEnabled = Enabled;
    if (Enabled)
    {
        ActiveAge = 0.; FadeAge = -1.; HitAge = 100.;
        SetVisibility(true, true);
        Ripple->SetVisibility(false); SecondRipple->SetVisibility(false);
        SetComponentTickEnabled(true);
        if (StartSound) UGameplayStatics::PlaySound2D(this, StartSound, .3f * FMath::Clamp(SoundVolume, 0.f, 1.f));
        UE_LOG(LogTemp, Display, TEXT("IRON_WALL_VFX_BEGIN"));
    }
    else
    {
        FadeAge = 0.;
        UE_LOG(LogTemp, Display, TEXT("IRON_WALL_VFX_FADE"));
    }
}

void UIronWallEffectComponent::NotifyHit(const FVector& IncomingDirection)
{
    if (!bShieldEnabled || HitAge < .08) return;
    // shortcut: show the latest impact per shield; pool ripples if overlapping hits need separate traces.
    FVector Direction = IncomingDirection.GetSafeNormal2D();
    if (Direction.IsNearlyZero()) Direction = FVector::ForwardVector;
    const FVector Contact(Direction.X * 28., Direction.Y * 28., 14.);
    const FRotator Rotation = FRotationMatrix::MakeFromZ(Direction + FVector(0, 0, .15)).Rotator();
    Ripple->SetRelativeLocationAndRotation(Contact, Rotation);
    SecondRipple->SetRelativeLocationAndRotation(Contact + Direction * .3, Rotation);
    ReturnContact=Contact;ReturnNormal=Direction;
    HitAge = 0.;
    UE_LOG(LogTemp, Display, TEXT("IRON_WALL_VFX_HIT"));
}

void UIronWallEffectComponent::SetGroundNormal(const FVector& Normal)
{
    if (!GroundRing) return;
    GroundRing->SetRelativeRotation(FRotationMatrix::MakeFromZ(Normal).Rotator());
    GroundRing->SetRelativeLocation(Normal * 1.5);
}

void UIronWallEffectComponent::TickComponent(float Dt, ELevelTick TickType, FActorComponentTickFunction* Function)
{
    Super::TickComponent(Dt, TickType, Function);
    if (bShieldEnabled) ActiveAge += Dt;
    else FadeAge += Dt;
    HitAge += Dt;
    const float Alpha = IronWallPresentation::Opacity(ActiveAge, FadeAge);
    Field->SetRelativeScale3D(FVector(FMath::Lerp(.15f, .2f, Alpha)));
    Lines->SetRelativeScale3D(Field->GetRelativeScale3D());
    GroundRing->SetRelativeScale3D(Field->GetRelativeScale3D());
    FieldMaterial->SetScalarParameterValue(TEXT("Opacity"), Alpha * .45f);
    LineMaterial->SetScalarParameterValue(TEXT("Opacity"), Alpha * (.8f + .12f * FMath::Sin(ActiveAge * 5.)));
    const float HitAlpha = IronWallPresentation::HitOpacity(HitAge) * (bGoldMode ? 1.f : Alpha);
    HitMaterial->SetScalarParameterValue(TEXT("Opacity"), HitAlpha);
    FieldMaterial->SetScalarParameterValue(TEXT("Strength"), 30.f + HitAlpha * 10.f);
    Ripple->SetVisibility(HitAlpha > .001f);
    SecondRipple->SetVisibility(HitAlpha > .001f && HitAge > .045);
    const float T = FMath::Clamp(float(HitAge / IronWallPresentation::HitSeconds), 0.f, 1.f);
    Ripple->SetRelativeScale3D(FVector(FMath::Lerp(.018f, .24f, T)));
    SecondRipple->SetRelativeScale3D(FVector(FMath::Lerp(.012f, .19f, T)));
    if (bGoldMode && HitAge < IronWallPresentation::HitSeconds)
    {
        Ripple->SetRelativeLocation(ReturnContact+ReturnNormal*T*30.);
        SecondRipple->SetRelativeLocation(ReturnContact+ReturnNormal*T*24.);
    }
    if (!bShieldEnabled && Alpha <= 0.f && (!bGoldMode || HitAlpha <= 0.f))
    {
        ResetShield();
        UE_LOG(LogTemp, Display, TEXT("IRON_WALL_VFX_HIDDEN"));
    }
}

void UIronWallEffectComponent::ResetShield()
{
    bShieldEnabled = false; ActiveAge = 0.; FadeAge = -1.; HitAge = 100.;
    SetVisibility(false, true);
    SetComponentTickEnabled(false);
    for (auto* Material : {FieldMaterial.Get(), LineMaterial.Get(), HitMaterial.Get()})
        if (Material) Material->SetScalarParameterValue(TEXT("Opacity"), 0.f);
}
