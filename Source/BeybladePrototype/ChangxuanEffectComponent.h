#pragma once
#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "ChangxuanEffectComponent.generated.h"

UCLASS()
class BEYBLADEPROTOTYPE_API UChangxuanEffectComponent : public USceneComponent
{
    GENERATED_BODY()
public:
    UChangxuanEffectComponent();
    bool InitializeVisuals(bool StoneMode = false);
    void SetEnabled(bool Enabled);
    void SetGroundNormal(const FVector& Normal);
    void ResetEffect();
    virtual void TickComponent(float DeltaTime, ELevelTick Type, FActorComponentTickFunction* Function) override;
private:
    UPROPERTY() TArray<TObjectPtr<class UStaticMeshComponent>> Rings;
    UPROPERTY() TObjectPtr<class UStaticMeshComponent> Motes;
    UPROPERTY() TObjectPtr<class UMaterialInstanceDynamic> RingMaterial;
    UPROPERTY() TObjectPtr<class UMaterialInstanceDynamic> MoteMaterial;
    bool bStoneMode = false;
    bool bActive = false;
    double Age = 0., FadeAge = -1.;
    FVector GroundNormal = FVector::UpVector;
};
