#pragma once
#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "IronWallEffectComponent.generated.h"

UCLASS()
class BEYBLADEPROTOTYPE_API UIronWallEffectComponent : public USceneComponent
{
    GENERATED_BODY()
public:
    UIronWallEffectComponent();
    bool InitializeVisuals(bool GoldMode = false);
    void SetShieldEnabled(bool Enabled, float SoundVolume = 1.f);
    void NotifyHit(const FVector& IncomingDirection);
    void SetGroundNormal(const FVector& Normal);
    void ResetShield();
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
private:
    UPROPERTY() TObjectPtr<class UStaticMeshComponent> Field;
    UPROPERTY() TObjectPtr<class UStaticMeshComponent> Lines;
    UPROPERTY() TObjectPtr<class UStaticMeshComponent> GroundRing;
    UPROPERTY() TObjectPtr<class UStaticMeshComponent> Ripple;
    UPROPERTY() TObjectPtr<class UStaticMeshComponent> SecondRipple;
    UPROPERTY() TObjectPtr<class UMaterialInstanceDynamic> FieldMaterial;
    UPROPERTY() TObjectPtr<class UMaterialInstanceDynamic> LineMaterial;
    UPROPERTY() TObjectPtr<class UMaterialInstanceDynamic> HitMaterial;
    UPROPERTY() TObjectPtr<class USoundBase> StartSound;
    bool bGoldMode = false;
    FVector ReturnContact, ReturnNormal;
    bool bShieldEnabled = false;
    double ActiveAge = 0., FadeAge = -1., HitAge = 100.;
};
