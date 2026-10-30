#pragma once
#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "ChifengEffectComponent.generated.h"

UCLASS()
class BEYBLADEPROTOTYPE_API UChifengEffectComponent : public USceneComponent
{
    GENERATED_BODY()
public:
    UChifengEffectComponent();
    bool InitializeVisuals();
    void SetEnabled(bool Enabled);
    void NotifyHit(const FVector& Direction);
    void SetGroundNormal(const FVector& Normal);
    void ResetEffect();
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* Function) override;
private:
    UPROPERTY() TArray<TObjectPtr<class UStaticMeshComponent>> Rings;
    UPROPERTY() TObjectPtr<class UStaticMeshComponent> Sparks;
    UPROPERTY() TObjectPtr<class UMaterialInstanceDynamic> RingMaterial;
    UPROPERTY() TObjectPtr<class UMaterialInstanceDynamic> SparkMaterial;
    bool bActive = false;
    double Age = 0., FadeAge = -1., HitAge = 100.;
    FVector GroundNormal = FVector::UpVector;
};
