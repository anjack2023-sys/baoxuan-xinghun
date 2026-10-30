#include "HengrenEffectComponent.h"
#include "IronWallPresentation.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
UHengrenEffectComponent::UHengrenEffectComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.bStartWithTickEnabled = false;
    PrimaryComponentTick.TickGroup = TG_PostPhysics;
    SetAbsolute(false, true, true);
}

bool UHengrenEffectComponent::InitializeVisuals(bool FrostMode)
{
    bFrostMode=FrostMode;
    auto* Arc = LoadObject<UStaticMesh>(nullptr,TEXT("/Game/Beyblade/FX/Hengren/SM_HengrenArc.SM_HengrenArc"));
    auto* Glyph = LoadObject<UStaticMesh>(nullptr,FrostMode ? TEXT("/Game/Beyblade/FX/Extra/SM_FrostShards.SM_FrostShards") : TEXT("/Game/Beyblade/FX/Hengren/SM_HengrenSeal.SM_HengrenSeal"));
    auto* Ripple = LoadObject<UStaticMesh>(nullptr,TEXT("/Game/Beyblade/FX/IronWall/SM_IronWallRipple.SM_IronWallRipple"));
    auto* Base = LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Beyblade/FX/IronWall/M_IronWallLines.M_IronWallLines"));
    if(!Arc || !Glyph || !Ripple || !Base) { UE_LOG(LogTemp,Error,TEXT("HENGREN_MISSING_ASSET"));return false; }
    BlueMaterial=UMaterialInstanceDynamic::Create(Base,this);
    GoldMaterial=UMaterialInstanceDynamic::Create(Base,this);
    HitMaterial=UMaterialInstanceDynamic::Create(Base,this);
    BlueMaterial->SetVectorParameterValue(TEXT("Tint"),FLinearColor(.08f,.35f,1.f));
    GoldMaterial->SetVectorParameterValue(TEXT("Tint"),FLinearColor(1.f,.65f,.12f));
    HitMaterial->SetVectorParameterValue(TEXT("Tint"),FLinearColor(1.f,.85f,.45f));
    BlueMaterial->SetScalarParameterValue(TEXT("Strength"),32.f);
    GoldMaterial->SetScalarParameterValue(TEXT("Strength"),25.f);
    HitMaterial->SetScalarParameterValue(TEXT("Strength"),45.f);
    if(FrostMode) {
        BlueMaterial->SetVectorParameterValue(TEXT("Tint"),FLinearColor(.05f,.5f,1.f));
        GoldMaterial->SetVectorParameterValue(TEXT("Tint"),FLinearColor(.3f,.65f,1.f));
    }
    auto Part=[&](const FName Name,UStaticMesh* Mesh,UMaterialInstanceDynamic* Material) {
        auto* C=NewObject<UStaticMeshComponent>(GetOwner(),FrostMode ? FName(*(FString(TEXT("Frost_"))+Name.ToString())) : Name);
        C->SetupAttachment(this);C->SetStaticMesh(Mesh);
        for(int32 I=0;I<C->GetNumMaterials();++I)C->SetMaterial(I,Material);
        C->SetCollisionEnabled(ECollisionEnabled::NoCollision);C->SetGenerateOverlapEvents(false);
        C->SetCanEverAffectNavigation(false);C->SetCastShadow(false);C->RegisterComponent();return C;
    };
    AttackRing=Part(TEXT("HengrenAttackRing"),Arc,BlueMaterial);
    DefenseRing=Part(TEXT("HengrenDefenseRing"),Arc,GoldMaterial);
    Seal=Part(TEXT("HengrenSeal"),Glyph,BlueMaterial);
    Impact=Part(TEXT("HengrenImpact"),Ripple,HitMaterial);
    ResetEffect();return true;
}

void UHengrenEffectComponent::SetEnabled(bool Enabled)
{
    if(!Impact || bActive==Enabled)return;
    bActive=Enabled;
    if(Enabled) {
        Age=0.;FadeAge=-1.;HitAge=100.;SetVisibility(true,true);Impact->SetVisibility(false);SetComponentTickEnabled(true);
        UE_LOG(LogTemp,Display,TEXT("HENGREN_VFX_BEGIN"));
    } else { FadeAge=0.;UE_LOG(LogTemp,Display,TEXT("HENGREN_VFX_FADE")); }
}
void UHengrenEffectComponent::NotifyHit(const FVector& Direction)
{
    if(!bActive || HitAge<.08)return;
    // shortcut: latest contact replaces the prior flash; pool flashes if overlapping impacts need separate visuals.
    const FVector N=Direction.GetSafeNormal2D();
    Impact->SetRelativeLocation(N*22.+FVector(0,0,12));
    Impact->SetRelativeRotation(FRotationMatrix::MakeFromZ(N+FVector(0,0,.15)).Rotator());
    HitAge=0.;UE_LOG(LogTemp,Display,TEXT("HENGREN_VFX_HIT"));
}
void UHengrenEffectComponent::SetGroundNormal(const FVector& Normal) { GroundNormal=Normal; }
void UHengrenEffectComponent::TickComponent(float Dt,ELevelTick Type,FActorComponentTickFunction* Function)
{
    Super::TickComponent(Dt,Type,Function);
    if(bActive)Age+=Dt;else FadeAge+=Dt;
    HitAge+=Dt;
    const float Alpha=IronWallPresentation::Opacity(Age,FadeAge);
    const FQuat Surface=FRotationMatrix::MakeFromZ(GroundNormal).ToQuat();
    const float Pulse=FMath::Sin(Age*7.);
    AttackRing->SetRelativeScale3D(FVector((.28f+Pulse*.008f)*FMath::Lerp(.55f,1.f,Alpha)));
    DefenseRing->SetRelativeScale3D(FVector((.32f-Pulse*.008f)*FMath::Lerp(.55f,1.f,Alpha)));
    AttackRing->SetRelativeRotation(FQuat(GroundNormal,Age*3.2)*Surface*FQuat(FVector::ForwardVector,.12));
    DefenseRing->SetRelativeRotation(FQuat(GroundNormal,-Age*2.4+PI/2)*Surface*FQuat(FVector::ForwardVector,-.12));
    AttackRing->SetRelativeLocation(GroundNormal*13.);DefenseRing->SetRelativeLocation(GroundNormal*8.);
    Seal->SetRelativeScale3D(FVector(.34f*FMath::Lerp(.55f,1.f,Alpha)));
    Seal->SetRelativeRotation(Surface);Seal->SetRelativeLocation(GroundNormal*2.);
    BlueMaterial->SetScalarParameterValue(TEXT("Opacity"),Alpha*(.65f+.1f*Pulse));
    GoldMaterial->SetScalarParameterValue(TEXT("Opacity"),Alpha*(.65f-.1f*Pulse));
    if(bFrostMode) {
        AttackRing->SetRelativeRotation(FQuat(GroundNormal,Age*.8)*Surface*FQuat(FVector::ForwardVector,.55));
        DefenseRing->SetRelativeRotation(FQuat(GroundNormal,-Age*.6)*Surface*FQuat(FVector::ForwardVector,-.55));
        Seal->SetRelativeLocation(GroundNormal*(2.f+FMath::Sin(Age*5.)));
    }
    const float HitAlpha=IronWallPresentation::HitOpacity(HitAge)*Alpha;
    Impact->SetVisibility(HitAlpha>.001f);Impact->SetRelativeScale3D(FVector(.035f+FMath::Clamp(float(HitAge),0.f,.38f)*.5f));
    HitMaterial->SetScalarParameterValue(TEXT("Opacity"),HitAlpha);
    if(!bActive && Alpha<=0.f) { ResetEffect();UE_LOG(LogTemp,Display,TEXT("HENGREN_VFX_HIDDEN")); }
}
void UHengrenEffectComponent::ResetEffect()
{
    bActive=false;Age=0.;FadeAge=-1.;HitAge=100.;SetVisibility(false,true);SetComponentTickEnabled(false);
    for(auto* M:{BlueMaterial.Get(),GoldMaterial.Get(),HitMaterial.Get()})if(M)M->SetScalarParameterValue(TEXT("Opacity"),0.f);
}
