#pragma once
#include "CoreMinimal.h"
#include "Engine/GameInstance.h"
#include "Styling/SlateBrush.h"
#include "BeybladeGameInstance.generated.h"

UCLASS()
class BEYBLADEPROTOTYPE_API UBeybladeGameInstance : public UGameInstance
{
    GENERATED_BODY()
public:
    virtual void Init() override;
    virtual void Shutdown() override;
private:
    void BeginLoadingScreen(const FString& MapName);
    void MapLoaded(UWorld* World);
    void LoadingFinished();
    UPROPERTY() TObjectPtr<class UTexture2D> LoadingBackground;
    FSlateBrush BackgroundBrush;
    double LoadingStarted = 0.;
};
