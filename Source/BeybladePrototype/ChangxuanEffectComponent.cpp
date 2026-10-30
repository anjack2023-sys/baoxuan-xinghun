#include "ChangxuanEffectComponent.h"
#include "IronWallPresentation.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"

UChangxuanEffectComponent::UChangxuanEffectComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.bStartWithTickEnabled = false;
    PrimaryComponentTick.TickGroup = TG_PostPhysics;
    SetAbsolute(false, true, true);
}

bool UChangxuanEffectComponent::InitializeVisuals(bool StoneMode)
{
    bStoneMode=StoneMode;
    auto* RingMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Game/Beyblade/FX/Changxuan/SM_ChangxuanRing.SM_ChangxuanRing"));
    auto* MoteMesh = LoadObject<UStaticMesh>(nullptr, StoneMode ? TEXT("/Game/Beyblade/FX/Extra/SM_StoneFragments.SM_StoneFragments") : TEXT("/Game/Beyblade/FX/Changxuan/SM_ChangxuanMotes.SM_ChangxuanMotes"));
    auto* Base = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Beyblade/FX/IronWall/M_IronWallLines.M_IronWallLines"));
    if (!RingMesh || !MoteMesh || !Base) { UE_LOG(LogTemp, Error, TEXT("CHANGXUAN_MISSING_ASSET")); return false; }
    RingMaterial = UMaterialInstanceDynamic::Create(Base, this);
    MoteMaterial = UMaterialInstanceDynamic::Create(Base, this);
    RingMaterial->SetVectorParameterValue(TEXT("Tint"), FLinearColor(.005f, 1.f, .45f));
    RingMaterial->SetScalarParameterValue(TEXT("Strength"), 28.f);
    MoteMaterial->SetVectorParameterValue(TEXT("Tint"), FLinearColor(.08f, 1.f, .7f));
    MoteMaterial->SetScalarParameterValue(TEXT("Strength"), 40.f);
    if(StoneMode) {
        RingMaterial->SetVectorParameterValue(TEXT("Tint"),FLinearColor(.35f,.65f,.08f));
        RingMaterial->SetScalarParameterValue(TEXT("Strength"),18.f);
        MoteMaterial->SetVectorParameterValue(TEXT("Tint"),FLinearColor(.22f,.27f,.15f));
        MoteMaterial->SetScalarParameterValue(TEXT("Strength"),1.5f);
    }
    auto Part = [&](const FName Name, UStaticMesh* Mesh, UMaterialInstanceDynamic* Material)
    {
        auto* C = NewObject<UStaticMeshComponent>(GetOwner(), StoneMode ? FName(*(FString(TEXT("Stone_"))+Name.ToString())) : Name);
        C->SetupAttachment(this); C->SetStaticMesh(Mesh);
        for (int32 I = 0; I < C->GetNumMaterials(); ++I) C->SetMaterial(I, Material);
        C->SetCollisionEnabled(ECollisionEnabled::NoCollision); C->SetGenerateOverlapEvents(false);
        C->SetCanEverAffectNavigation(false); C->SetCastShadow(false); C->RegisterComponent();
        return C;
    };
    for (int32 I = 0; I < 3; ++I)
        Rings.Add(Part(FName(*FString::Printf(TEXT("ChangxuanRing%d"), I)), RingMesh, RingMaterial));
    Motes = Part(TEXT("ChangxuanMotes"), MoteMesh, MoteMaterial);
    ResetEffect(); return true;
}

void UChangxuanEffectComponent::SetEnabled(bool Enabled)
{
    if (!Motes || bActive == Enabled) return;
    bActive = Enabled;
    if (Enabled)
    {
        Age = 0.; FadeAge = -1.;
        SetVisibility(true, true); SetComponentTickEnabled(true);
        UE_LOG(LogTemp, Display, TEXT("CHANGXUAN_VFX_BEGIN"));
    }
    else { FadeAge = 0.; UE_LOG(LogTemp, Display, TEXT("CHANGXUAN_VFX_FADE")); }
}

void UChangxuanEffectComponent::SetGroundNormal(const FVector& Normal) { GroundNormal = Normal; }

void UChangxuanEffectComponent::TickComponent(float Dt, ELevelTick Type, FActorComponentTickFunction* Function)
{
    Super::TickComponent(Dt, Type, Function);
    if (bActive) Age += Dt; else FadeAge += Dt;
    const float Alpha = IronWallPresentation::Opacity(Age, FadeAge);
    RingMaterial->SetScalarParameterValue(TEXT("Opacity"), Alpha * (.65f + .13f * FMath::Sin(Age * 4.)));
    const FQuat Surface = FRotationMatrix::MakeFromZ(GroundNormal).ToQuat();
    for (int32 I = 0; I < Rings.Num(); ++I)
    {
        const float Pulse = FMath::Sin(Age * 3. + I * 2.);
        Rings[I]->SetRelativeScale3D(FVector((.24f + I * .045f + Pulse * .012f) * FMath::Lerp(.6f, 1.f, Alpha)));
        const FQuat Tilt = I == 1 ? FQuat(FVector::ForwardVector, .15f) : FQuat::Identity;
        Rings[I]->SetRelativeRotation(FQuat(GroundNormal, Age * (I % 2 ? -1.6 : 1.2) + I) * Surface * Tilt);
        Rings[I]->SetRelativeLocation(GroundNormal * (2.f + I * 6.f + Pulse * 1.2f));
    }
    const float Phase = FMath::Frac(float(Age * .7));
    Motes->SetRelativeRotation(FQuat(GroundNormal, Age * .9) * Surface);
    Motes->SetRelativeScale3D(FVector(.30f));
    Motes->SetRelativeLocation(GroundNormal * (3.f + Phase * 28.f));
    // Fade the shared mote cluster at its wrap so the upward loop never pops.
    MoteMaterial->SetScalarParameterValue(TEXT("Opacity"), Alpha * FMath::Sin(Phase * PI));
    if(bStoneMode) {
        for(int32 I=0;I<Rings.Num();++I) {
            Rings[I]->SetRelativeLocation(GroundNormal*(2.f+I));
            Rings[I]->SetRelativeRotation(FQuat(GroundNormal,Age*.25+I)*Surface);
        }
        Motes->SetRelativeLocation(GroundNormal*(4.f+FMath::Sin(Age*2.)*1.5f));
        Motes->SetRelativeRotation(FQuat(GroundNormal,Age*.15)*Surface);
        MoteMaterial->SetScalarParameterValue(TEXT("Opacity"),Alpha*.85f);
    }
    if (!bActive && Alpha <= 0.f) { ResetEffect(); UE_LOG(LogTemp, Display, TEXT("CHANGXUAN_VFX_HIDDEN")); }
}

void UChangxuanEffectComponent::ResetEffect()
{
    bActive = false; Age = 0.; FadeAge = -1.;
    SetVisibility(false, true); SetComponentTickEnabled(false);
    if (RingMaterial) RingMaterial->SetScalarParameterValue(TEXT("Opacity"), 0.f);
    if (MoteMaterial) MoteMaterial->SetScalarParameterValue(TEXT("Opacity"), 0.f);
}
