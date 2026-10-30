#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "ArenaWalker.generated.h"

UCLASS()
class BEYBLADEPROTOTYPE_API AArenaWalker : public ACharacter
{
    GENERATED_BODY()
public:
    AArenaWalker();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    void ToggleAvatar();
    void PreviewAvatar(class USkeletalMesh* Mesh, class UAnimSequence* Animation);
    void SetRunning(bool Running);
private:
    UPROPERTY() TObjectPtr<class USpringArmComponent> Arm;
    UPROPERTY() TObjectPtr<class UCameraComponent> View;
    UPROPERTY() TObjectPtr<class UAnimSequence> Idle;
    UPROPERTY() TObjectPtr<class UAnimSequence> Walk;
    UPROPERTY() TObjectPtr<class UAnimSequence> Run;
    UPROPERTY() TObjectPtr<class UAnimSequence> Current;
    bool bRunning = false, bAIAvatar = false, bGrok = false, bPreviewFrozen = false;
    void LoadAvatar();
};
