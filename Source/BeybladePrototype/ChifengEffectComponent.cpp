#include "ChifengEffectComponent.h"
#include "IronWallPresentation.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"

UChifengEffectComponent::UChifengEffectComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.bStartWithTickEnabled = false;
    PrimaryComponentTick.TickGroup = TG_PostPhysics;
    SetAbsolute(false, true, true);
}

bool UChifengEffectComponent::InitializeVisuals()
{
    auto* RingMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Game/Beyblade/FX/Chifeng/SM_ChifengRing.SM_ChifengRing"));
    auto* SparkMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Game/Beyblade/FX/Chifeng/SM_ChifengSparks.SM_ChifengSparks"));
    auto* Base = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Beyblade/FX/IronWall/M_IronWallLines.M_IronWallLines"));
    if (!RingMesh || !SparkMesh || !Base) { UE_LOG(LogTemp, Error, TEXT("CHIFENG_MISSING_ASSET")); return false; }
    RingMaterial = UMaterialInstanceDynamic::Create(Base, this);
    SparkMaterial = UMaterialInstanceDynamic::Create(Base, this);
    RingMaterial->SetVectorParameterValue(TEXT("Tint"), FLinearColor(1.f, .008f, .002f));
    RingMaterial->SetScalarParameterValue(TEXT("Strength"), 12.f);
    SparkMaterial->SetVectorParameterValue(TEXT("Tint"), FLinearColor(1.f, .2f, .012f));
    SparkMaterial->SetScalarParameterValue(TEXT("Strength"), 55.f);
    auto Part = [&](const FName Name, UStaticMesh* Mesh, UMaterialInstanceDynamic* Material)
    {
        auto* C = NewObject<UStaticMeshComponent>(GetOwner(), Name);
        C->SetupAttachment(this); C->SetStaticMesh(Mesh);
        for (int32 I = 0; I < C->GetNumMaterials(); ++I) C->SetMaterial(I, Material);
        C->SetCollisionEnabled(ECollisionEnabled::NoCollision); C->SetGenerateOverlapEvents(false);
        C->SetCanEverAffectNavigation(false); C->SetCastShadow(false); C->RegisterComponent();
        return C;
    };
    for (int32 I = 0; I < 3; ++I)
        Rings.Add(Part(FName(*FString::Printf(TEXT("ChifengRing%d"), I)), RingMesh, RingMaterial));
    Sparks = Part(TEXT("ChifengSparks"), SparkMesh, SparkMaterial);
    ResetEffect(); return true;
}

void UChifengEffectComponent::SetEnabled(bool Enabled)
{
    if (!Sparks || bActive == Enabled) return;
    bActive = Enabled;
    if (Enabled)
    {
        Age = 0.; FadeAge = -1.; HitAge = 100.;
        SetVisibility(true, true); Sparks->SetVisibility(false); SetComponentTickEnabled(true);
        UE_LOG(LogTemp, Display, TEXT("CHIFENG_VFX_BEGIN"));
    }
    else { FadeAge = 0.; UE_LOG(LogTemp, Display, TEXT("CHIFENG_VFX_FADE")); }
}

void UChifengEffectComponent::NotifyHit(const FVector& Direction)
{
    if (!bActive || HitAge < .08) return;
    // shortcut: latest impact replaces the previous burst; pool bursts if overlapping contacts need separate visuals.
    const FVector N = Direction.GetSafeNormal2D();
    Sparks->SetRelativeLocation(N * 21. + FVector(0, 0, 12));
    Sparks->SetRelativeRotation(FRotator(0, N.Rotation().Yaw, 0));
    HitAge = 0.; UE_LOG(LogTemp, Display, TEXT("CHIFENG_VFX_HIT"));
}

void UChifengEffectComponent::SetGroundNormal(const FVector& Normal) { GroundNormal = Normal; }

void UChifengEffectComponent::TickComponent(float Dt, ELevelTick Type, FActorComponentTickFunction* Function)
{
    Super::TickComponent(Dt, Type, Function);
    if (bActive) Age += Dt; else FadeAge += Dt;
    HitAge += Dt;
    const float Alpha = IronWallPresentation::Opacity(Age, FadeAge);
    RingMaterial->SetScalarParameterValue(TEXT("Opacity"), Alpha * (.8f + .15f * FMath::Sin(Age * 18.)));
    for (int32 I = 0; I < Rings.Num(); ++I)
    {
        const float Phase = FMath::Frac(float(Age * 1.25 + I / 3.));
        Rings[I]->SetRelativeScale3D(FVector((.22f + Phase * .14f) * FMath::Lerp(.65f, 1.f, Alpha)));
        const FQuat Tilt = I == 1 ? FQuat(FVector::ForwardVector, .32f) : FQuat::Identity;
        Rings[I]->SetRelativeRotation((FQuat(GroundNormal, Age * (I % 2 ? -4. : 4.) + I) * FRotationMatrix::MakeFromZ(GroundNormal).ToQuat() * Tilt));
        Rings[I]->SetRelativeLocation(GroundNormal * (I == 1 ? 13.f : 2.f + I));
    }
    const float HitAlpha = IronWallPresentation::HitOpacity(HitAge) * Alpha;
    Sparks->SetVisibility(HitAlpha > .001f);
    Sparks->SetRelativeScale3D(FVector(.10f + FMath::Clamp(float(HitAge), 0.f, .38f) * .7f));
    SparkMaterial->SetScalarParameterValue(TEXT("Opacity"), HitAlpha);
    if (!bActive && Alpha <= 0.f) { ResetEffect(); UE_LOG(LogTemp, Display, TEXT("CHIFENG_VFX_HIDDEN")); }
}

void UChifengEffectComponent::ResetEffect()
{
    bActive = false; Age = 0.; FadeAge = -1.; HitAge = 100.;
    SetVisibility(false, true); SetComponentTickEnabled(false);
    if (RingMaterial) RingMaterial->SetScalarParameterValue(TEXT("Opacity"), 0.f);
    if (SparkMaterial) SparkMaterial->SetScalarParameterValue(TEXT("Opacity"), 0.f);
}
