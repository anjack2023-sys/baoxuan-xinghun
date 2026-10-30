#pragma once
#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "ChiwenEffectComponent.generated.h"
UCLASS()
class BEYBLADEPROTOTYPE_API UChiwenEffectComponent : public USceneComponent
{
    GENERATED_BODY()
public:
    UChiwenEffectComponent();
    bool InitializeVisuals();
    void SetArmed(bool Armed);
    void ConsumeHit(const FVector& Direction);
    void SetGroundNormal(const FVector& Normal);
    void ResetEffect();
    virtual void TickComponent(float Dt,ELevelTick Type,FActorComponentTickFunction* Function) override;
private:
    UPROPERTY() TObjectPtr<class UStaticMeshComponent> Flames;
    UPROPERTY() TObjectPtr<class UStaticMeshComponent> Core;
    UPROPERTY() TObjectPtr<class UStaticMeshComponent> Sparks;
    UPROPERTY() TObjectPtr<class UStaticMeshComponent> Wave;
    UPROPERTY() TObjectPtr<class UMaterialInstanceDynamic> FlameMaterial;
    UPROPERTY() TObjectPtr<class UMaterialInstanceDynamic> CoreMaterial;
    UPROPERTY() TObjectPtr<class UMaterialInstanceDynamic> HitMaterial;
    bool bArmed=false;
    double Age=0.,HitAge=-1.;
    FVector GroundNormal=FVector::UpVector;
};
