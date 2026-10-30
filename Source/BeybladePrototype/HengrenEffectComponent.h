#pragma once
#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "HengrenEffectComponent.generated.h"
UCLASS()
class BEYBLADEPROTOTYPE_API UHengrenEffectComponent : public USceneComponent
{
    GENERATED_BODY()
public:
    UHengrenEffectComponent();
    bool InitializeVisuals(bool FrostMode = false);
    void SetEnabled(bool Enabled);
    void NotifyHit(const FVector& Direction);
    void SetGroundNormal(const FVector& Normal);
    void ResetEffect();
    virtual void TickComponent(float Dt, ELevelTick Type, FActorComponentTickFunction* Function) override;
private:
    UPROPERTY() TObjectPtr<class UStaticMeshComponent> AttackRing;
    UPROPERTY() TObjectPtr<class UStaticMeshComponent> DefenseRing;
    UPROPERTY() TObjectPtr<class UStaticMeshComponent> Seal;
    UPROPERTY() TObjectPtr<class UStaticMeshComponent> Impact;
    UPROPERTY() TObjectPtr<class UMaterialInstanceDynamic> BlueMaterial;
    UPROPERTY() TObjectPtr<class UMaterialInstanceDynamic> GoldMaterial;
    UPROPERTY() TObjectPtr<class UMaterialInstanceDynamic> HitMaterial;
    bool bFrostMode = false;
    bool bActive = false;
    double Age = 0., FadeAge = -1., HitAge = 100.;
    FVector GroundNormal = FVector::UpVector;
};
