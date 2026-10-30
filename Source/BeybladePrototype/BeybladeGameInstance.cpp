#include "BeybladeGameInstance.h"
#include "Engine/Texture2D.h"
#include "MoviePlayer.h"
#include "Styling/CoreStyle.h"
#include "UObject/UObjectGlobals.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SScaleBox.h"
#include "Widgets/SOverlay.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Images/SThrobber.h"
#include "Widgets/Text/STextBlock.h"
#include "Fonts/SlateFontInfo.h"
#include "Misc/Paths.h"

void UBeybladeGameInstance::Init()
{
    Super::Init();
    if (IsRunningCommandlet() || IsRunningDedicatedServer() || !IsMoviePlayerEnabled()) return;
    LoadingBackground = LoadObject<UTexture2D>(nullptr, TEXT("/Game/Beyblade/UI/P3/T_Lobby.T_Lobby"));
    if (!ensureMsgf(LoadingBackground, TEXT("Loading background is missing"))) return;
    BackgroundBrush.SetResourceObject(LoadingBackground);
    BackgroundBrush.ImageSize = FVector2D(LoadingBackground->GetSizeX(), LoadingBackground->GetSizeY());
    BackgroundBrush.DrawAs = ESlateBrushDrawType::Image;
    FCoreUObjectDelegates::PreLoadMap.AddUObject(this, &UBeybladeGameInstance::BeginLoadingScreen);
    FCoreUObjectDelegates::PostLoadMapWithWorld.AddUObject(this, &UBeybladeGameInstance::MapLoaded);
    GetMoviePlayer()->OnMoviePlaybackFinished().AddUObject(this, &UBeybladeGameInstance::LoadingFinished);
}

void UBeybladeGameInstance::BeginLoadingScreen(const FString& MapName)
{
    if (!LoadingBackground || (GetWorld() && GetWorld()->WorldType == EWorldType::PIE)) return;
    LoadingStarted = FPlatformTime::Seconds();
    const FSlateFontInfo Font(MakeShared<FCompositeFont>(FName(TEXT("Regular")),
        FPaths::EngineContentDir() / TEXT("Slate/Fonts/DroidSansFallback.ttf"),
        EFontHinting::Default, EFontLoadingPolicy::LazyLoad), 28);
    FLoadingScreenAttributes Screen;
    Screen.bAutoCompleteWhenLoadingCompletes = true;
    Screen.bMoviesAreSkippable = false;
    Screen.WidgetLoadingScreen = SNew(SOverlay)
        + SOverlay::Slot()
        [
            SNew(SScaleBox).Stretch(EStretch::ScaleToFill)
            [ SNew(SImage).Image(&BackgroundBrush) ]
        ]
        + SOverlay::Slot().HAlign(HAlign_Fill).VAlign(VAlign_Bottom)
        [
            SNew(SBorder).Padding(FMargin(48, 28))
            .BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
            .BorderBackgroundColor(FLinearColor(.015f, .03f, .06f, .9f))
            [
                SNew(SVerticalBox)
                + SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 14)
                [ SNew(STextBlock).Text(FText::FromString(TEXT("爆旋星魂 · 正在准备训练馆")))
                    .Font(Font).ColorAndOpacity(FLinearColor(.96f, .93f, .85f)) ]
                + SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 14)
                [ SNew(SThrobber).NumPieces(3) ]
                + SVerticalBox::Slot().AutoHeight()
                [ SNew(STextBlock).Text(FText::FromString(TEXT("小提示：调整发射角度，尝试不同的碰撞路线。")))
                    .Font(Font).ColorAndOpacity(FLinearColor(.85f, .71f, .42f)) ]
            ]
        ];
    GetMoviePlayer()->SetupLoadingScreen(Screen);
    UE_LOG(LogTemp, Display, TEXT("LOADING_SCREEN_BEGIN map=%s background=%s"), *MapName, *LoadingBackground->GetPathName());
}

void UBeybladeGameInstance::MapLoaded(UWorld* World)
{
    if (LoadingStarted > 0. && World)
        UE_LOG(LogTemp, Display, TEXT("LOADING_MAP_READY map=%s seconds=%.3f"), *World->GetName(), FPlatformTime::Seconds() - LoadingStarted);
}

void UBeybladeGameInstance::LoadingFinished()
{
    if (LoadingStarted > 0.)
    {
        UE_LOG(LogTemp, Display, TEXT("LOADING_SCREEN_FINISHED seconds=%.3f"), FPlatformTime::Seconds() - LoadingStarted);
        LoadingStarted = 0.;
    }
}

void UBeybladeGameInstance::Shutdown()
{
    FCoreUObjectDelegates::PreLoadMap.RemoveAll(this);
    FCoreUObjectDelegates::PostLoadMapWithWorld.RemoveAll(this);
    if (IsMoviePlayerEnabled()) GetMoviePlayer()->OnMoviePlaybackFinished().RemoveAll(this);
    Super::Shutdown();
}
