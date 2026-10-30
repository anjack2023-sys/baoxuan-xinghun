#include "ChiwenEffectComponent.h"
#include "IronWallPresentation.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
UChiwenEffectComponent::UChiwenEffectComponent()
{
    PrimaryComponentTick.bCanEverTick=true;PrimaryComponentTick.bStartWithTickEnabled=false;
    PrimaryComponentTick.TickGroup=TG_PostPhysics;SetAbsolute(false,true,true);
}
bool UChiwenEffectComponent::InitializeVisuals()
{
    auto* FlameMesh=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/Beyblade/FX/Chiwen/SM_ChiwenFlames.SM_ChiwenFlames"));
    auto* SparkMesh=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/Beyblade/FX/Chifeng/SM_ChifengSparks.SM_ChifengSparks"));
    auto* RingMesh=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/Beyblade/FX/IronWall/SM_IronWallRipple.SM_IronWallRipple"));
    auto* Base=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Beyblade/FX/IronWall/M_IronWallLines.M_IronWallLines"));
    if(!FlameMesh||!SparkMesh||!RingMesh||!Base){UE_LOG(LogTemp,Error,TEXT("CHIWEN_MISSING_ASSET"));return false;}
    FlameMaterial=UMaterialInstanceDynamic::Create(Base,this);CoreMaterial=UMaterialInstanceDynamic::Create(Base,this);HitMaterial=UMaterialInstanceDynamic::Create(Base,this);
    FlameMaterial->SetVectorParameterValue(TEXT("Tint"),FLinearColor(1.f,.045f,.002f));FlameMaterial->SetScalarParameterValue(TEXT("Strength"),26.f);
    CoreMaterial->SetVectorParameterValue(TEXT("Tint"),FLinearColor(1.f,.32f,.012f));CoreMaterial->SetScalarParameterValue(TEXT("Strength"),30.f);
    HitMaterial->SetVectorParameterValue(TEXT("Tint"),FLinearColor(1.f,.55f,.045f));HitMaterial->SetScalarParameterValue(TEXT("Strength"),50.f);
    auto Part=[&](const FName Name,UStaticMesh* Mesh,UMaterialInstanceDynamic* Material){
        auto* C=NewObject<UStaticMeshComponent>(GetOwner(),Name);C->SetupAttachment(this);C->SetStaticMesh(Mesh);
        for(int32 I=0;I<C->GetNumMaterials();++I)C->SetMaterial(I,Material);
        C->SetCollisionEnabled(ECollisionEnabled::NoCollision);C->SetGenerateOverlapEvents(false);C->SetCanEverAffectNavigation(false);C->SetCastShadow(false);C->RegisterComponent();return C;
    };
    Flames=Part(TEXT("ChiwenFlames"),FlameMesh,FlameMaterial);Core=Part(TEXT("ChiwenCore"),FlameMesh,CoreMaterial);
    Sparks=Part(TEXT("ChiwenSparks"),SparkMesh,HitMaterial);Wave=Part(TEXT("ChiwenWave"),RingMesh,HitMaterial);
    ResetEffect();return true;
}
void UChiwenEffectComponent::SetArmed(bool Armed)
{
    if(!Flames||bArmed==Armed)return;
    bArmed=Armed;
    if(Armed){Age=0.;HitAge=-1.;SetVisibility(true,true);Sparks->SetVisibility(false);Wave->SetVisibility(false);SetComponentTickEnabled(true);UE_LOG(LogTemp,Display,TEXT("CHIWEN_VFX_ARMED"));}
    else if(HitAge<0.)ResetEffect();
}
void UChiwenEffectComponent::ConsumeHit(const FVector& Direction)
{
    if(!bArmed)return;
    bArmed=false;HitAge=0.;const FVector N=Direction.GetSafeNormal2D();
    Sparks->SetRelativeLocation(N*21.+FVector(0,0,12));Sparks->SetRelativeRotation(FRotator(0,N.Rotation().Yaw,0));
    Wave->SetRelativeLocation(N*22.+FVector(0,0,12));Wave->SetRelativeRotation(FRotationMatrix::MakeFromZ(N+FVector(0,0,.15)).Rotator());
    Sparks->SetVisibility(true);Wave->SetVisibility(true);UE_LOG(LogTemp,Display,TEXT("CHIWEN_VFX_CONSUMED"));
}
void UChiwenEffectComponent::SetGroundNormal(const FVector& Normal){GroundNormal=Normal;}
void UChiwenEffectComponent::TickComponent(float Dt,ELevelTick Type,FActorComponentTickFunction* Function)
{
    Super::TickComponent(Dt,Type,Function);Age+=Dt;if(HitAge>=0.)HitAge+=Dt;
    const float Alpha=IronWallPresentation::Opacity(Age,HitAge<0.?-1.:HitAge);
    const FQuat Surface=FRotationMatrix::MakeFromZ(GroundNormal).ToQuat();const float Pulse=FMath::Sin(Age*17.);
    Flames->SetRelativeLocation(GroundNormal*4.);Flames->SetRelativeRotation(FQuat(GroundNormal,Age*4.)*Surface);Flames->SetRelativeScale3D(FVector(.27f,.27f,.20f+Pulse*.015f));
    Core->SetRelativeLocation(GroundNormal*7.);Core->SetRelativeRotation(FQuat(GroundNormal,-Age*3.+PI)*Surface);Core->SetRelativeScale3D(FVector(.23f,.23f,.14f-Pulse*.01f));
    FlameMaterial->SetScalarParameterValue(TEXT("Opacity"),Alpha*(.72f+Pulse*.12f));CoreMaterial->SetScalarParameterValue(TEXT("Opacity"),Alpha*.65f);
    const float HitAlpha=IronWallPresentation::HitOpacity(HitAge);HitMaterial->SetScalarParameterValue(TEXT("Opacity"),HitAlpha);
    Sparks->SetRelativeScale3D(FVector(.1f+FMath::Clamp(float(HitAge),0.f,.38f)*.85f));Wave->SetRelativeScale3D(FVector(.025f+FMath::Clamp(float(HitAge),0.f,.38f)*.8f));
    if(!bArmed && HitAge>=IronWallPresentation::HitSeconds){ResetEffect();UE_LOG(LogTemp,Display,TEXT("CHIWEN_VFX_HIDDEN"));}
}
void UChiwenEffectComponent::ResetEffect()
{
    bArmed=false;Age=0.;HitAge=-1.;SetVisibility(false,true);SetComponentTickEnabled(false);
    for(auto* M:{FlameMaterial.Get(),CoreMaterial.Get(),HitMaterial.Get()})if(M)M->SetScalarParameterValue(TEXT("Opacity"),0.f);
}
