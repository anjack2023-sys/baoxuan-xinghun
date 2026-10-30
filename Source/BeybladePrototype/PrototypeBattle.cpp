#include "PrototypeBattle.h"
#include "ArenaWalker.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "IronWallEffectComponent.h"
#include "ChifengEffectComponent.h"
#include "ChangxuanEffectComponent.h"
#include "HengrenEffectComponent.h"
#include "ChiwenEffectComponent.h"
#include "MobileUX.h"
#include "PlayerSaveService.h"
#include "LobbyClickUI.h"
#include "ContentStrings.h"
#include "Grade1Balance.h"
#include "RingoutPresentation.h"
#include "SpinPresentation.h"
#include "FeelLabTuning.h"
#include "FeelLabTypePresets.h"
#include "DrawDebugHelpers.h"
#include "StadiumObstacles.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Animation/AnimSequence.h"
#include "Animation/SkeletalMeshActor.h"
#include "Components/PoseableMeshComponent.h"
#include "Components/AudioComponent.h"
#include "Sound/SoundBase.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputCoreTypes.h"
#include "EngineUtils.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/Parse.h"
#include "Misc/ConfigCacheIni.h"
#include "Engine/StaticMesh.h"
#include "HAL/FileManager.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"

void APrototypeBattleController::SetupInputComponent()
{
    Super::SetupInputComponent();
    UEnhancedInputComponent* Enhanced = Cast<UEnhancedInputComponent>(InputComponent);
    UEnhancedInputLocalPlayerSubsystem* Subsystem = GetLocalPlayer() ?
        GetLocalPlayer()->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>() : nullptr;
    if (!ensure(Enhanced && Subsystem)) return;
    LaunchAction = NewObject<UInputAction>(this);
    ResetAction = NewObject<UInputAction>(this);
    ArenaAction = NewObject<UInputAction>(this);
    ArenaAction->ValueType = EInputActionValueType::Boolean;
    SkillAction = NewObject<UInputAction>(this);
    SkillAction->ValueType = EInputActionValueType::Boolean;
    ModeRace5Action = NewObject<UInputAction>(this);
    ModeRace8Action = NewObject<UInputAction>(this);
    ToggleModeAction = NewObject<UInputAction>(this);
    LaunchAction->ValueType = ResetAction->ValueType = ModeRace5Action->ValueType =
        ModeRace8Action->ValueType = ToggleModeAction->ValueType = EInputActionValueType::Boolean;
    Mapping = NewObject<UInputMappingContext>(this);
    Mapping->MapKey(LaunchAction, EKeys::SpaceBar);
    Mapping->MapKey(ResetAction, EKeys::R);
    Mapping->MapKey(ArenaAction, EKeys::E);
    Enhanced->BindAction(ArenaAction, ETriggerEvent::Started, this, &APrototypeBattleController::EnterArena);
    Mapping->MapKey(SkillAction, EKeys::Q);
    Enhanced->BindAction(SkillAction, ETriggerEvent::Started, this, &APrototypeBattleController::FireSkill);
    Mapping->MapKey(ModeRace5Action, EKeys::One);
    Mapping->MapKey(ModeRace8Action, EKeys::Two);
    Mapping->MapKey(ToggleModeAction, EKeys::Tab);
    Pick3Action = NewObject<UInputAction>(this);
    Pick4Action = NewObject<UInputAction>(this);
    Pick5Action = NewObject<UInputAction>(this);
    Pick3Action->ValueType = Pick4Action->ValueType = Pick5Action->ValueType = EInputActionValueType::Boolean;
    Mapping->MapKey(Pick3Action, EKeys::Three);
    Mapping->MapKey(Pick4Action, EKeys::Four);
    Mapping->MapKey(Pick5Action, EKeys::Five);
    const FKey ExtraKeys[] = {EKeys::Six,EKeys::Seven,EKeys::Eight};
    void (APrototypeBattleController::*const ExtraHandlers[])() = {&APrototypeBattleController::PickSlot5,&APrototypeBattleController::PickSlot6,&APrototypeBattleController::PickSlot7};
    for(int32 I=0;I<3;++I)
    {
        auto* Action=NewObject<UInputAction>(this);Action->ValueType=EInputActionValueType::Boolean;ExtraPickActions.Add(Action);
        Mapping->MapKey(Action,ExtraKeys[I]);Enhanced->BindAction(Action,ETriggerEvent::Started,this,ExtraHandlers[I]);
    }
    Subsystem->AddMappingContext(Mapping, 0);
    Enhanced->BindAction(LaunchAction, ETriggerEvent::Started, this, &APrototypeBattleController::Launch);
    Enhanced->BindAction(ResetAction, ETriggerEvent::Started, this, &APrototypeBattleController::ResetMatch);
    Enhanced->BindAction(ModeRace5Action, ETriggerEvent::Started, this, &APrototypeBattleController::SelectRace5);
    Enhanced->BindAction(ModeRace8Action, ETriggerEvent::Started, this, &APrototypeBattleController::SelectRace8);
    Enhanced->BindAction(ToggleModeAction, ETriggerEvent::Started, this, &APrototypeBattleController::ToggleMode);
    Enhanced->BindAction(Pick3Action, ETriggerEvent::Started, this, &APrototypeBattleController::PickSlot2);
    Enhanced->BindAction(Pick4Action, ETriggerEvent::Started, this, &APrototypeBattleController::PickSlot3);
    Enhanced->BindAction(Pick5Action, ETriggerEvent::Started, this, &APrototypeBattleController::PickSlot4);
    ClickAction = NewObject<UInputAction>(this);
    ClickAction->ValueType = EInputActionValueType::Boolean;
    Mapping->MapKey(ClickAction, EKeys::LeftMouseButton);
    Enhanced->BindAction(ClickAction, ETriggerEvent::Started, this, &APrototypeBattleController::OnLobbyClick);
    FInputModeGameAndUI Mode;
    Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
    Mode.SetHideCursorDuringCapture(false);
    SetInputMode(Mode);
    bShowMouseCursor = !MobileUX::Enabled();
    bEnableTouchEvents = true;
    InputComponent->BindTouch(IE_Pressed,this,&APrototypeBattleController::OnTouchPressed);
    if (UGameViewportClient* Viewport = GetWorld()->GetGameViewport())
    {
        Viewport->SetMouseCaptureMode(EMouseCaptureMode::CaptureDuringMouseDown);
        Viewport->SetMouseLockMode(EMouseLockMode::DoNotLock);
        Viewport->SetHideCursorDuringCapture(false);
        UE_LOG(LogTemp, Display, TEXT("BATTLE_INPUT mouse_visible=%d capture=%d lock=%d"),
            bShowMouseCursor ? 1 : 0, static_cast<int32>(Viewport->GetMouseCaptureMode()), static_cast<int32>(Viewport->GetMouseLockMode()));
    }
}
void APrototypeBattleController::EndPlay(const EEndPlayReason::Type Reason)
{
    if (GetLocalPlayer())
        if (auto* Subsystem = GetLocalPlayer()->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())
            if (Mapping) Subsystem->RemoveMappingContext(Mapping);
    Super::EndPlay(Reason);
}
void APrototypeBattleController::PlayerTick(float DeltaTime)
{
    Super::PlayerTick(DeltaTime);
    auto* Mode = GetWorld()->GetAuthGameMode<APrototypeBattleMode>();
    if (!Mode || Mode->IsAutomationBypass()) return;
    if (Mode->GetMatchFlow().State==EMatchFlowState::Prep && !Mode->IsLaunching())
    {
        if(WasInputKeyJustPressed(EKeys::A))Mode->AdjustLaunch(-5,0);
        if(WasInputKeyJustPressed(EKeys::D))Mode->AdjustLaunch(5,0);
        if(WasInputKeyJustPressed(EKeys::W))Mode->AdjustLaunch(0,5);
        if(WasInputKeyJustPressed(EKeys::S))Mode->AdjustLaunch(0,-5);
    }
    if (Mode->IsArenaExploring())
    {
        const FRotator Yaw(0, GetControlRotation().Yaw, 0);
        if (auto WalkerPawn = GetPawn())
        {
            if(auto* Walker=Cast<AArenaWalker>(WalkerPawn))
            {
                Walker->SetRunning(IsInputKeyDown(EKeys::LeftShift)||IsInputKeyDown(EKeys::RightShift));
                if(!Mode->HasAvatarSelection() && WasInputKeyJustPressed(EKeys::C))Walker->ToggleAvatar();
            }
            WalkerPawn->AddMovementInput(Yaw.Vector(), (IsInputKeyDown(EKeys::W) ? 1.f : 0.f) - (IsInputKeyDown(EKeys::S) ? 1.f : 0.f));
            WalkerPawn->AddMovementInput(FRotationMatrix(Yaw).GetUnitAxis(EAxis::Y), (IsInputKeyDown(EKeys::D) ? 1.f : 0.f) - (IsInputKeyDown(EKeys::A) ? 1.f : 0.f));
        }
        if (IsInputKeyDown(EKeys::RightMouseButton))
        {
            float X, Y; GetInputMouseDelta(X, Y); AddYawInput(X * .7f); AddPitchInput(-Y * .7f);
        }
        return;
    }
    if (WasInputKeyJustPressed(EKeys::F11)) Mode->ToggleTuning();
    if (WasInputKeyJustPressed(EKeys::V)) Mode->ToggleFaceView();
    if (WasInputKeyJustPressed(EKeys::F10)) Mode->LockFaceView();
    const float Pitch = (IsInputKeyDown(EKeys::Up) ? 1.f : 0.f) - (IsInputKeyDown(EKeys::Down) ? 1.f : 0.f);
    const float Height = (IsInputKeyDown(EKeys::PageUp) ? 1.f : 0.f) - (IsInputKeyDown(EKeys::PageDown) ? 1.f : 0.f);
    Mode->AdjustFaceView(Pitch * DeltaTime * 30.f, Height * DeltaTime * 45.f);
}

void APrototypeBattleMode::AdjustTuning(int32 MoveDelta,int32 RingoutDelta)
{
    if (AutoMatches>0) return;
    FeelSettings.Move+=MoveDelta;FeelSettings.Ringout+=RingoutDelta;FeelSettings.Clamp();
    if (Simulation.bStagedMobility) FeelLabTuning::SetMoveLevel(Simulation,FeelSettings.Move);
    Simulation.RingoutStrength=FeelSettings.Ringout/100.;
    const bool Saved=FeelSettings.Save(FPaths::ProjectSavedDir()/TEXT("IndustrialFeel.ini"));
    UE_LOG(LogTemp,Display,TEXT("INDUSTRIAL_FEEL_SETTINGS move=%d ringout=%d saved=%d"),FeelSettings.Move,FeelSettings.Ringout,Saved);
    if (!Saved) Error=TEXT("调试设置保存失败");
}
bool APrototypeBattleMode::HandleTuningClick(const FVector2D& Mouse)
{
    auto In=[&](double X,double Y,double W,double H) {return Mouse.X>=X && Mouse.X<=X+W && Mouse.Y>=Y && Mouse.Y<=Y+H;};
    if (In(30,190,230,52)) {ToggleTuning();return true;}
    if (!bTuningOpen || !In(30,250,470,235)) return false;
    if (In(310,300,65,50)) AdjustTuning(-5,0);
    else if (In(405,300,65,50)) AdjustTuning(5,0);
    else if (In(310,365,65,50)) AdjustTuning(0,-5);
    else if (In(405,365,65,50)) AdjustTuning(0,5);
    return true;
}
void APrototypeBattleMode::ToggleFaceView()
{
    if (!FaceCharacter) return;
    bFaceView = !bFaceView;
    FaceCharacter->SetActorHiddenInGame(bFaceView);
    if (FaceBackdrop) FaceBackdrop->SetActorHiddenInGame(!bFaceView);
    UE_LOG(LogTemp, Display, TEXT("FACE_VIEW enabled=%d pitch=%.1f height=%.1f"), bFaceView, FacePitch, FaceHeight);
}
void APrototypeBattleMode::AdjustFaceView(float PitchDelta, float HeightDelta)
{
    if (!bFaceView || bFaceLocked) return;
    FacePitch = FMath::Clamp(FacePitch + PitchDelta, -80.f, 20.f);
    FaceHeight = FMath::Clamp(FaceHeight + HeightDelta, -100.f, 350.f);
}
void APrototypeBattleMode::LockFaceView()
{
    if (!bFaceView) return;
    bFaceLocked = !bFaceLocked;
    const FString File = FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir() / TEXT("FaceCamera.ini"));
    GConfig->SetFloat(TEXT("FaceCamera"), TEXT("Pitch"), FacePitch, File);
    GConfig->SetFloat(TEXT("FaceCamera"), TEXT("Height"), FaceHeight, File);
    GConfig->SetBool(TEXT("FaceCamera"), TEXT("Locked"), bFaceLocked, File);
    GConfig->Flush(false, File);
    UE_LOG(LogTemp, Display, TEXT("FACE_VIEW locked=%d saved=%s"), bFaceLocked, *File);
}
void APrototypeBattleController::Launch()
{
    if (auto* Mode = GetWorld()->GetAuthGameMode<APrototypeBattleMode>()) Mode->Launch();
}
void APrototypeBattleController::EnterArena()
{
    if (auto* Mode = GetWorld()->GetAuthGameMode<APrototypeBattleMode>()) Mode->EnterArena();
}
void APrototypeBattleController::FireSkill()
{
    if (auto* Mode = GetWorld()->GetAuthGameMode<APrototypeBattleMode>()) Mode->FireActiveSkill();
}
void APrototypeBattleController::ResetMatch()
{
    if (auto* Mode = GetWorld()->GetAuthGameMode<APrototypeBattleMode>()) Mode->ResetMatch();
}
void APrototypeBattleController::SelectRace5()
{
    if (auto* Mode = GetWorld()->GetAuthGameMode<APrototypeBattleMode>())
    {
        const EMatchFlowState St = Mode->GetMatchFlow().State;
        if (St == EMatchFlowState::PickRegular || St == EMatchFlowState::BlindPick) Mode->TogglePickSlot(0);
        else Mode->SelectRaceMode(ERaceMode::RaceTo5);
    }
}
void APrototypeBattleController::SelectRace8()
{
    if (auto* Mode = GetWorld()->GetAuthGameMode<APrototypeBattleMode>())
    {
        const EMatchFlowState St = Mode->GetMatchFlow().State;
        if (St == EMatchFlowState::PickRegular || St == EMatchFlowState::BlindPick) Mode->TogglePickSlot(1);
        else Mode->SelectRaceMode(ERaceMode::RaceTo8);
    }
}
void APrototypeBattleController::ToggleMode()
{
    if (auto* Mode = GetWorld()->GetAuthGameMode<APrototypeBattleMode>()) Mode->ToggleRaceMode();
}
void APrototypeBattleController::PickSlot0()
{
    if (auto* Mode = GetWorld()->GetAuthGameMode<APrototypeBattleMode>()) Mode->TogglePickSlot(0);
}
void APrototypeBattleController::PickSlot1()
{
    if (auto* Mode = GetWorld()->GetAuthGameMode<APrototypeBattleMode>()) Mode->TogglePickSlot(1);
}
void APrototypeBattleController::PickSlot2()
{
    if (auto* Mode = GetWorld()->GetAuthGameMode<APrototypeBattleMode>()) Mode->TogglePickSlot(2);
}
void APrototypeBattleController::PickSlot3()
{
    if (auto* Mode = GetWorld()->GetAuthGameMode<APrototypeBattleMode>()) Mode->TogglePickSlot(3);
}
void APrototypeBattleController::PickSlot4()
{
    if (auto* Mode = GetWorld()->GetAuthGameMode<APrototypeBattleMode>()) Mode->TogglePickSlot(4);
}
void APrototypeBattleController::PickSlot5(){if(auto* Mode=GetWorld()->GetAuthGameMode<APrototypeBattleMode>())Mode->TogglePickSlot(5);}
void APrototypeBattleController::PickSlot6(){if(auto* Mode=GetWorld()->GetAuthGameMode<APrototypeBattleMode>())Mode->TogglePickSlot(6);}
void APrototypeBattleController::PickSlot7(){if(auto* Mode=GetWorld()->GetAuthGameMode<APrototypeBattleMode>())Mode->TogglePickSlot(7);}

void APrototypeBattleController::OnLobbyClick()
{
    if (LastTouchTime>=0. && FPlatformTime::Seconds()-LastTouchTime<.25) return;
    float X=0,Y=0;
    if(GetMousePosition(X,Y)) DispatchScreenPoint(FVector2D(X,Y));
}
void APrototypeBattleController::OnTouchPressed(ETouchIndex::Type Finger,FVector Location)
{
    if(Finger!=ETouchIndex::Touch1) return;
    LastTouchTime=FPlatformTime::Seconds();
    DispatchScreenPoint(FVector2D(Location.X,Location.Y));
}
void APrototypeBattleController::DispatchScreenPoint(const FVector2D& Point)
{
    auto* Mode=GetWorld()?GetWorld()->GetAuthGameMode<APrototypeBattleMode>():nullptr;
    if(!Mode || Mode->IsAutomationBypass()) return;
    int32 Width=0,Height=0;GetViewportSize(Width,Height);
    const FVector2D Mouse=FLobbyClickUI::FromViewport(Point,FVector2D(Width,Height));
    if(MobileUX::Enabled())
    {
        switch(MobileUX::Hit(Mouse))
        {
        case 0: Mode->ToggleFaceView();return;
        case 1: Mode->ResetMatch();return;
        case 2: UKismetSystemLibrary::QuitGame(this,this,EQuitPreference::Quit,false);return;
        default: break;
        }
    }
    if (MobileUX::Enabled() && Mode->IsArenaExploring() && MobileUX::HitStart(Mouse))
    { Mode->EnterArena(); return; }
    if (Mode->HasAvatarSelection() && Mode->GetMatchFlow().State == EMatchFlowState::Lobby)
        for(int32 I=0; I<6; ++I)
            if(FLobbyClickUI::Contains(FLobbyClickUI::AvatarPos(I), FVector2D(FLobbyClickUI::AvatarW, FLobbyClickUI::BtnH), Mouse.X, Mouse.Y))
            { Mode->SelectAvatar(I); return; }
    if (Mode->HandleLaunchClick(Mouse)) return;
    if (Mode->HandleTuningClick(Mouse)) return;
    const ELobbyClickAction Action = FLobbyClickUI::HitTest(Mouse.X, Mouse.Y, Mode->GetMatchFlow().State);
    switch (Action)
    {
    case ELobbyClickAction::Race5:
        Mode->SelectRaceMode(ERaceMode::RaceTo5);
        UE_LOG(LogTemp, Display, TEXT("M1_CLICK action=race5"));
        break;
    case ELobbyClickAction::Race8:
        Mode->SelectRaceMode(ERaceMode::RaceTo8);
        UE_LOG(LogTemp, Display, TEXT("M1_CLICK action=race8"));
        break;
    case ELobbyClickAction::Start:
        Mode->Launch();
        UE_LOG(LogTemp, Display, TEXT("M1_CLICK action=start"));
        break;
    case ELobbyClickAction::Pick0:
    case ELobbyClickAction::Pick1:
    case ELobbyClickAction::Pick2:
    case ELobbyClickAction::Pick3:
    case ELobbyClickAction::Pick4:
    case ELobbyClickAction::Pick5:
    case ELobbyClickAction::Pick6:
    case ELobbyClickAction::Pick7:
        Mode->TogglePickSlot(static_cast<int32>(Action) - static_cast<int32>(ELobbyClickAction::Pick0));
        UE_LOG(LogTemp, Display, TEXT("PICK_CLICK slot=%d"), static_cast<int32>(Action) - static_cast<int32>(ELobbyClickAction::Pick0));
        break;
    case ELobbyClickAction::ConfirmPick:
        Mode->ConfirmPick();
        UE_LOG(LogTemp, Display, TEXT("PICK_CLICK action=confirm"));
        break;
    case ELobbyClickAction::BackLobby:
        Mode->ResetMatch();
        UE_LOG(LogTemp, Display, TEXT("PICK_CLICK action=back"));
        break;
    case ELobbyClickAction::PrepLaunch:
        Mode->Launch();
        UE_LOG(LogTemp, Display, TEXT("PICK_CLICK action=prep_launch"));
        break;
    case ELobbyClickAction::NextRound:
        Mode->ContinueFromRoundSettle();
        UE_LOG(LogTemp, Display, TEXT("P2_CLICK action=next_round"));
        break;
    case ELobbyClickAction::Rematch:
        Mode->RematchFromMatchSettle();
        UE_LOG(LogTemp, Display, TEXT("P2_CLICK action=rematch"));
        break;
    case ELobbyClickAction::ToLobby:
        Mode->ResetMatch();
        UE_LOG(LogTemp, Display, TEXT("P2_CLICK action=to_lobby"));
        break;
    case ELobbyClickAction::LockBlind:
        Mode->LockBlind();
        UE_LOG(LogTemp, Display, TEXT("P2_CLICK action=lock_blind"));
        break;
    case ELobbyClickAction::ConfirmBlind:
        Mode->ConfirmBlind();
        UE_LOG(LogTemp, Display, TEXT("P2_CLICK action=confirm_blind"));
        break;
    case ELobbyClickAction::OpenCollect:
        Mode->OpenCollection();
        break;
    case ELobbyClickAction::CollectBack:
    case ELobbyClickAction::CollectDetailBack:
        Mode->CloseCollection();
        break;
    case ELobbyClickAction::Collect0:
    case ELobbyClickAction::Collect1:
    case ELobbyClickAction::Collect2:
    case ELobbyClickAction::Collect3:
    case ELobbyClickAction::Collect4:
    case ELobbyClickAction::Collect5:
    case ELobbyClickAction::Collect6:
    case ELobbyClickAction::Collect7:
        Mode->SelectCollectionSlot(static_cast<int32>(Action) - static_cast<int32>(ELobbyClickAction::Collect0));
        break;
    case ELobbyClickAction::EnterArena:
        Mode->EnterArena();
        break;
    case ELobbyClickAction::FireSkill:
        Mode->FireActiveSkill();
        break;
    default:
        break;
    }
}
APrototypeBattleMode::APrototypeBattleMode()
{
    PrimaryActorTick.bCanEverTick = true;
    DefaultPawnClass = nullptr;
    PlayerControllerClass = APrototypeBattleController::StaticClass();
    HUDClass = APrototypeBattleHUD::StaticClass();
}
void APrototypeBattleMode::BeginPlay()
{
    Super::BeginPlay();
    Beys.SetNum(2);
    ArenaScoreDisplays.SetNum(2);
    for (TActorIterator<AActor> It(GetWorld()); It; ++It)
    {
        if (It->ActorHasTag(TEXT("RankedArena"))) bRankedArena = true;
        for (int32 I = 0; I < 2; ++I)
            if (It->ActorHasTag(I == 0 ? TEXT("ArenaScoreP1") : TEXT("ArenaScoreP2")))
                ArenaScoreDisplays[I] = It->FindComponentByClass<UStaticMeshComponent>();
        if (It->ActorHasTag(TEXT("BattleP1"))) Beys[0] = *It;
        if (It->ActorHasTag(TEXT("BattleP2"))) Beys[1] = *It;
        if (It->ActorHasTag(TEXT("BattleBowl"))) Bowl = It->FindComponentByClass<UStaticMeshComponent>();
        if (It->ActorHasTag(TEXT("BattleGround"))) Ground = It->FindComponentByClass<UStaticMeshComponent>();
        if (It->ActorHasTag(TEXT("FaceBackdrop"))) FaceBackdrop = *It;
        if (It->ActorHasTag(TEXT("FaceCameraCharacter")))
        {
            FaceCharacter = *It;
            FVector Origin, Extent;
            It->GetActorBounds(false, Origin, Extent);
            FaceAnchor = FVector(Origin.X, Origin.Y, Origin.Z + Extent.Z * .82f);
            FaceAnchor += FVector(-Origin.X, -Origin.Y, 0).GetSafeNormal() * 20.f;
        }
        if (It->ActorHasTag(TEXT("BattleCamera")))
        {
            BattleView = Cast<ACameraActor>(*It);
            PreparationViewLocation = It->GetActorLocation();
            PreparationViewRotation = It->GetActorRotation();
            if (BattleView) {
                auto* Camera=BattleView->GetCameraComponent(); PreparationFOV=Camera->FieldOfView;
                Camera->PostProcessSettings.bOverride_MotionBlurAmount=true;
                Camera->PostProcessSettings.MotionBlurAmount=0.f;
            }
            if (auto* PC = UGameplayStatics::GetPlayerController(this, 0)) PC->SetViewTarget(*It);
        }
    }
    if (bRankedArena)
    {
        bTutorialPending=!IFileManager::Get().FileExists(*(FPaths::ProjectSavedDir()/TEXT("TutorialCompleted.txt")));
    }
    if (bRankedArena)
        for (int32 I = 0; I <= 10; ++I)
            ArenaScoreDigits.Add(LoadObject<UStaticMesh>(nullptr, *FString::Printf(TEXT("/Game/Beyblade/Arena/StarCrown_v1/SM_Score_%d.SM_Score_%d"), I, I)));
    FParse::Value(FCommandLine::Get(), TEXT("ProtoAuto="), AutoMatches);
    if (AutoMatches <= 0)
    {
        for (TActorIterator<AActor> It(GetWorld()); It; ++It)
            if (It->ActorHasTag(TEXT("BeyWorldLabel"))) It->SetActorHiddenInGame(true);
        const FString File = FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir() / TEXT("FaceCamera.ini"));
        if (MobileUX::Enabled()) { FacePitch=-43.f; FaceHeight=220.f; bFaceLocked=true; }
        GConfig->GetFloat(TEXT("FaceCamera"), TEXT("Pitch"), FacePitch, File);
        GConfig->GetFloat(TEXT("FaceCamera"), TEXT("Height"), FaceHeight, File);
        GConfig->GetBool(TEXT("FaceCamera"), TEXT("Locked"), bFaceLocked, File);
        FacePitch = FMath::Clamp(FacePitch, -80.f, 20.f);
        FaceHeight = FMath::Clamp(FaceHeight, -100.f, 350.f);
        // Pool slots 0..4: ChiFeng / BiLei / ChangXuan / HengRen / ChiWen (ChiWen may be missing -> nullptr ok)
        for (const TCHAR* Name : {TEXT("Chifeng"), TEXT("Bilei"), TEXT("Changxuan"), TEXT("Hengren"), TEXT("Chiwen"), TEXT("Huangkai"), TEXT("Cuipan"), TEXT("Shuanghuan")})
        {
            const FString Path = FString::Printf(TEXT("/Game/Beyblade/Art/Tripo_v1/SM_%s.SM_%s"), Name, Name);
            ImportedBeys.Add(LoadObject<UStaticMesh>(nullptr, *Path));
        }
        BeyArt.SetNum(2);
        ScrapeSound = LoadObject<USoundBase>(nullptr, TEXT("/Game/Beyblade/Audio/S_BeyScrape.S_BeyScrape"));
        for (int32 I = 1; I <= 3; ++I)
        {
            const FString Path = FString::Printf(TEXT("/Game/Beyblade/Audio/S_BeyContact%d.S_BeyContact%d"), I, I);
            ContactSounds.Add(LoadObject<USoundBase>(nullptr, *Path));
            if (!ContactSounds.Last()) UE_LOG(LogTemp, Warning, TEXT("COLLISION_AUDIO_MISSING %s"), *Path);
        }
    }
    FeelSettings.Load(FPaths::ProjectSavedDir()/TEXT("IndustrialFeel.ini"));
    for (int32 I=0; I<4; ++I) if (!FeelLabTypes::Get(I).Valid) Error=TEXT("Industrial feel type preset missing or invalid.");
    Simulation.ArenaScale=Bowl && Bowl->GetStaticMesh() && (Bowl->GetStaticMesh()->GetName().Contains(TEXT("80_LowWall")) || Bowl->GetStaticMesh()->GetName().Contains(TEXT("StarCrown_Arena80"))) ? .8 : 1.;
    const bool HasSeed = FParse::Value(FCommandLine::Get(), TEXT("ProtoSeed="), Seed);
    if (AutoMatches < 0 || (AutoMatches > 0 && !HasSeed))
        Error = TEXT("ProtoAuto requires explicit -ProtoSeed=<integer> and a positive count.");
    if (!Beys[0] || !Beys[1] || !Bowl || !Ground) Error = TEXT("Main is missing tagged battle actors. Run configure_combat.py.");
    if (!HasSeed) Seed = FMath::Rand();
    Simulation.Random.Initialize(Seed);
	// Tier2b demo loadout: Grade1 Attack (P1) vs Defense (P2). Feel85 frozen kick constants unchanged.
	Simulation.ApplyLoadout(0, MakeLoadout(EBeyType::Attack, EBeyGrade::Grade1));
	Simulation.ApplyLoadout(1, MakeLoadout(EBeyType::Defense, EBeyGrade::Grade1));
	// M2 finish fields on interactive Main only; ProtoAuto keeps spinout goldens.
	Simulation.bEnableBurstTrapXtr = (AutoMatches <= 0);
    const FString RunId = FDateTime::UtcNow().ToString(TEXT("%Y%m%d_%H%M%S")) + TEXT("_") + FGuid::NewGuid().ToString(EGuidFormats::Digits);
    LogPath = FPaths::ProjectSavedDir() / TEXT("BattleLogs") / (RunId + TEXT(".csv"));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(LogPath), true);
    const FString Header = FString::Printf(TEXT("# run_id=%s seed=%d fixed_hz=60 units=m SPIN_KICK=1.45 RESTITUTION=0.78 move_multiplier=%d weight=50/50 ringout=%d natural_spin=per_type radius=0.22 rim_gate_r=2 rim_gate_speed=2.25 launch_pow=1.55..1.95 timeout=residual_momentum spinout=grade1_decay time_limit_s=%.0f contact=feel_trial_%d kick_reference_speed=%.3f\nmatch,first_hit,hit_count,end_t,end_reason,winner\n"), *RunId, Seed, FeelSettings.Move, FeelSettings.Ringout, AutoMatches > 0 ? FBattleSimulation::TimeLimitSeconds : 120., FBattleSimulation::ContactFeelTrial, FBattleSimulation::KickReferenceSpeed);
    if (!FFileHelper::SaveStringToFile(Header, *LogPath, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM))
        Error = TEXT("Cannot create independent match log.");
    double Height;
    if (Error.IsEmpty() && (!SampleHeight(FVector2D(0, 0), Height) || FMath::Abs(Height - 0.42) > 0.02))
        Error = TEXT("Bowl triangle collision probe failed; refusing invisible/fallback floor.");
    Ready = Error.IsEmpty();
    if (!Ready)
    {
        UE_LOG(LogTemp, Error, TEXT("BATTLE_INIT_FAILED: %s"), *Error);
        if (AutoMatches > 0) FPlatformMisc::RequestExitWithStatus(false, 1);
        return;
    }
    if(AutoMatches<=0)
    {
        for(const TCHAR* Name:{TEXT("S_SkillCue"),TEXT("S_WinCue"),TEXT("S_LoseCue")})
            FeedbackSounds.Add(LoadObject<USoundBase>(nullptr,*FString::Printf(TEXT("/Game/Beyblade/Audio/%s.%s"),Name,Name)));
        for(const TCHAR* Name:{TEXT("S_LaunchCount"),TEXT("S_LaunchPull"),TEXT("S_LaunchRelease")})
            LaunchSounds.Add(LoadObject<USoundBase>(nullptr,*FString::Printf(TEXT("/Game/Beyblade/Audio/%s.%s"),Name,Name)));
        if(FaceCharacter)
            SetupLaunchHero();
    }
    Simulation.Reset(); Accumulator = 0;
    Falling[0] = Falling[1] = false;
    FallTime = FallDuration = 0;
    WinnerPresentHold = false;
    ApplyTransforms();
    if (bRankedArena && AutoMatches <= 0)
    {
        FActorSpawnParameters Params; Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        ArenaWalker = GetWorld()->SpawnActor<AArenaWalker>(FVector(0, 340, 110), FRotator(0, -90, 0), Params);
        if(bAvatarSelection && ArenaWalker && HeroOriginal && HeroLaunchAnimation) ArenaWalker->PreviewAvatar(HeroOriginal->GetSkeletalMeshAsset(),HeroLaunchAnimation);
    }
    if (AutoMatches > 0)
    {
        // Automation bypasses lobby: preserve historical ProtoAuto seed batches.
        SkillShell.ResetForBout();
        MatchFlow.State = EMatchFlowState::Fighting;
        Grade1Balance::EnsureLoaded();
		ContentStrings::EnsureLoaded();
		UE_LOG(LogTemp, Display, TEXT("GRADE1_DATA_ENSURE csv=%d"), Grade1Balance::WasLoadedFromCsv() ? 1 : 0);
		UE_LOG(LogTemp, Display, TEXT("BATTLE_READY seed=%d log=%s auto=%d"), Seed, *LogPath, AutoMatches);
        Launch();
    }
    else
    {
        MatchFlow.State = EMatchFlowState::Lobby;
        MatchFlow.ResetMatchPool();
        if (UBeybladePlayerSaveGame* Save = BeybladePlayerSave::LoadOrCreateSlot0())
        {
            ContactMasterVolume = Save->bMute ? 0.f : FMath::Clamp(Save->MasterVolume, 0.f, 1.f);
            ERaceMode Restored = ERaceMode::RaceTo5;
            if (BeybladePlayerSave::TryParseMode(Save->LastMode, Restored))
                MatchFlow.SetMode(Restored);
            UE_LOG(LogTemp, Display, TEXT("SAVE_LOAD_SLOT0 ok version=%d last_mode=%s vol=%.2f lang=%s mute=%d wins=%d"),
                Save->SaveVersion, *Save->LastMode, Save->MasterVolume, *Save->Language, Save->bMute ? 1 : 0, Save->MatchWins);
        }
        else
        {
            UE_LOG(LogTemp, Warning, TEXT("SAVE_LOAD_SLOT0 failed"));
        }
        if (bRankedArena) MatchFlow.SetMode(ERaceMode::RaceTo8);
        Grade1Balance::EnsureLoaded();
		ContentStrings::EnsureLoaded();
		UE_LOG(LogTemp, Display, TEXT("GRADE1_DATA_ENSURE csv=%d"), Grade1Balance::WasLoadedFromCsv() ? 1 : 0);
		UE_LOG(LogTemp, Display, TEXT("BATTLE_READY seed=%d log=%s flow=lobby mode=%d"), Seed, *LogPath, MatchFlow.Target());
        UE_LOG(LogTemp, Display, TEXT("M1_LOBBY mode=%s score=0:0 hint=1/2 SPACE enter pick"), MatchFlow.ModeLabel());
#if !UE_BUILD_SHIPPING
        if(FParse::Param(FCommandLine::Get(),TEXT("UIPickPreview"))) Launch();
        if(FParse::Param(FCommandLine::Get(),TEXT("UICollectionPreview"))) OpenCollection();
        if(bAvatarSelection && FParse::Param(FCommandLine::Get(),TEXT("AvatarTestAll")))
        {
            for(int32 I=0;I<6;++I) SelectAvatar(I);
            SelectAvatar(0);
        }
        if(FParse::Param(FCommandLine::Get(),TEXT("BoutPreview")))
        {
            Launch();for (int32 I=0; I<MatchFlow.Pick.Required; ++I) TogglePickSlot(I);ConfirmPick();
            if(FParse::Param(FCommandLine::Get(),TEXT("BoutAutoLaunch")))Launch();
        }
#endif
    }
}
bool APrototypeBattleMode::SampleHeight(const FVector2D& Position, double& Height) const
{
    if (!Bowl) return false;
    FHitResult Hit;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(BattleBowl), true);
    const FVector XY(Position.X * 100, Position.Y * 100, 0);
    if (!Bowl->LineTraceComponent(Hit, XY + FVector(0, 0, 600), XY - FVector(0, 0, 200), Query)) return false;
    Height = Hit.ImpactPoint.Z / 100;
    return true;
}
bool APrototypeBattleMode::SweepBowlObstacle(const FVector2D& Start,const FVector2D& End,FVector2D& Position,FVector2D& Normal) const
{
    if (!Bowl || !Bowl->GetStaticMesh()) return false;
    const FString MeshName=Bowl->GetStaticMesh()->GetName();
    if (!MeshName.Contains(TEXT("industrial-bowl")) && !MeshName.Contains(TEXT("Arena80_LowWall"))) return false;
    return StadiumObstacles::Sweep(Start,End,Simulation.ArenaScale,FBattleSimulation::Radius,Position,Normal);
}
double APrototypeBattleMode::GroundFloorZ() const
{
    if (!Ground) return 0.5;
    return Ground->Bounds.Origin.Z + Ground->Bounds.BoxExtent.Z + 0.5;
}
bool APrototypeBattleMode::IsRingoutPresenting() const
{
    return (Falling[0] || Falling[1]) && FallTime < FallDuration;
}
void APrototypeBattleMode::SelectRaceMode(ERaceMode Mode)
{
    if (!Ready || AutoMatches > 0) return;
    MatchFlow.SetMode(Mode);
    UE_LOG(LogTemp, Display, TEXT("M1_MODE mode=%s"), MatchFlow.ModeLabel());
    if (UBeybladePlayerSaveGame* Save = BeybladePlayerSave::LoadOrCreateSlot0())
    {
        Save->LastMode = BeybladePlayerSave::ModeToPersist(MatchFlow.Mode);
        if (BeybladePlayerSave::SaveSlot0(Save))
            UE_LOG(LogTemp, Display, TEXT("SAVE_SLOT0 last_mode=%s"), *Save->LastMode);
    }
}
void APrototypeBattleMode::ToggleRaceMode()
{
    if (!Ready || AutoMatches > 0) return;
    MatchFlow.ToggleMode();
    UE_LOG(LogTemp, Display, TEXT("M1_MODE mode=%s"), MatchFlow.ModeLabel());
    if (UBeybladePlayerSaveGame* Save = BeybladePlayerSave::LoadOrCreateSlot0())
    {
        Save->LastMode = BeybladePlayerSave::ModeToPersist(MatchFlow.Mode);
        if (BeybladePlayerSave::SaveSlot0(Save))
            UE_LOG(LogTemp, Display, TEXT("SAVE_SLOT0 last_mode=%s"), *Save->LastMode);
    }
}
void APrototypeBattleMode::TogglePickSlot(int32 PoolIndex)
{
    if (!Ready || AutoMatches > 0) return;
    if (MatchFlow.State == EMatchFlowState::BlindPick)
    {
        if (!MatchFlow.TryToggleBlindP1(PoolIndex)) return;
        UE_LOG(LogTemp, Display, TEXT("BLIND_TOGGLE P1 slot=%d locked=%d"), PoolIndex, MatchFlow.bBlindLockedP1 ? 1 : 0);
        return;
    }
    if (!MatchFlow.TryTogglePick(PoolIndex)) return;
    UE_LOG(LogTemp, Display, TEXT("PICK_TOGGLE slot=%d count=%d can=%d"), PoolIndex, MatchFlow.Pick.Count, MatchFlow.Pick.CanConfirm() ? 1 : 0);
}
void APrototypeBattleMode::ConfirmPick()
{
    if (!Ready || AutoMatches > 0) return;
    if (!MatchFlow.TryConfirmPick())
    {
        UE_LOG(LogTemp, Display, TEXT("PICK_CONFIRM rejected count=%d"), MatchFlow.Pick.Count);
        return;
    }
    if (bRankedArena && BattleView)
    {
        const FVector View(0, 420, 1450);
        BattleView->SetActorLocationAndRotation(View, (FVector(0, 0, 60) - View).Rotation());
    }
    UE_LOG(LogTemp, Display, TEXT("PICK_CONFIRM lineup=%d,%d,%d -> prep"),
        MatchFlow.Pick.Lineup[0], MatchFlow.Pick.Lineup[1], MatchFlow.Pick.Lineup[2]);
}
void APrototypeBattleMode::LockBlind()
{
    if (!Ready || AutoMatches > 0) return;
    if (!MatchFlow.TryLockBlindP1())
    {
        UE_LOG(LogTemp, Display, TEXT("BLIND_LOCK_P1 rejected choice=%d"), MatchFlow.BlindChoiceP1);
        return;
    }
    // Local dual-lock stub. ONLINE_RESERVE: wait remote; server adjudicates; no peek; no countdown hosting.
    MatchFlow.TryAutoLockP2Local();
    UE_LOG(LogTemp, Display, TEXT("BLIND_LOCK P1=%d P2=%d revealed=%d"),
        MatchFlow.BlindChoiceP1, MatchFlow.BlindChoiceP2, MatchFlow.bBlindRevealed ? 1 : 0);
}
void APrototypeBattleMode::ConfirmBlind()
{
    if (!Ready || AutoMatches > 0) return;
    if (!MatchFlow.TryConfirmBlind())
    {
        UE_LOG(LogTemp, Display, TEXT("BLIND_CONFIRM rejected revealed=%d"), MatchFlow.bBlindRevealed ? 1 : 0);
        return;
    }
    UE_LOG(LogTemp, Display, TEXT("BLIND_CONFIRM P1=%d P2=%d -> prep"), MatchFlow.BlindChoiceP1, MatchFlow.BlindChoiceP2);
}
void APrototypeBattleMode::ContinueFromRoundSettle()
{
    if (!Ready || AutoMatches > 0) return;
    if (bTutorialBout && MatchFlow.State==EMatchFlowState::RoundSettle)
    {
        bTutorialBout=false; MatchFlow.State=EMatchFlowState::Prep;
        UE_LOG(LogTemp,Display,TEXT("TUTORIAL_DONE -> prep without scoring"));
        return;
    }
    if (!MatchFlow.TryContinueRound()) return;
    UE_LOG(LogTemp, Display, TEXT("P2_NEXT state=%s lineup=%d used=%d"),
        MatchFlow.StateLabel(), MatchFlow.CurrentLineupIndex, MatchFlow.CountUsed());
}
void APrototypeBattleMode::RematchFromMatchSettle()
{
    if (!Ready || AutoMatches > 0) return;
    if (!MatchFlow.TryRematchFromMatchSettle()) return;
    Simulation.Reset(); Accumulator = 0;
    Falling[0] = Falling[1] = false;
    FallTime = FallDuration = 0;
    WinnerPresentHold = false;
    ApplyTransforms();
    UE_LOG(LogTemp, Display, TEXT("P2_REMATCH_TO_LOBBY"));
}
void APrototypeBattleMode::ApplyCurrentLoadouts()
{
    if (MatchFlow.bBlindPhase && MatchFlow.BlindChoiceP1 >= 0)
    {
        Simulation.ApplyLoadout(0, MakeLoadout(MatchFlow.Pick.Pool[MatchFlow.BlindChoiceP1].Type, EBeyGrade::Grade1));
        if (MatchFlow.BlindChoiceP2 >= 0)
            Simulation.ApplyLoadout(1, MakeLoadout(MatchFlow.Pick.Pool[MatchFlow.BlindChoiceP2].Type, EBeyGrade::Grade1));
        else
            Simulation.ApplyLoadout(1, MakeLoadout(EBeyType::Defense, EBeyGrade::Grade1));
        return;
    }
    const FBeyLoadout P1 = MatchFlow.Pick.LoadoutAtLineup(MatchFlow.CurrentLineupIndex);
    Simulation.ApplyLoadout(0, P1);
    Simulation.ApplyLoadout(1, MakeLoadout(EBeyType::Defense, EBeyGrade::Grade1));
}

void APrototypeBattleMode::StartBattleInternal()
{
    if (IronWallFx) IronWallFx->ResetShield();
    if (ChifengFx) ChifengFx->ResetEffect();
    if (ChangxuanFx) ChangxuanFx->ResetEffect();
    if (HengrenFx) HengrenFx->ResetEffect();
    if (ChiwenFx) ChiwenFx->ResetEffect();
    if (GoldFx) GoldFx->ResetShield();
    if (StoneFx) StoneFx->ResetEffect();
    if (FrostFx) FrostFx->ResetEffect();
    ApplyCurrentLoadouts();
    SkillShell.ResetForBout();
    {
        const int32 P1Slot = MatchFlow.bBlindPhase && MatchFlow.BlindChoiceP1 >= 0 ? MatchFlow.BlindChoiceP1
            : (MatchFlow.Pick.Count > MatchFlow.CurrentLineupIndex ? MatchFlow.Pick.Lineup[MatchFlow.CurrentLineupIndex] : 0);
        const EBeyType P1Type = MatchFlow.Pick.Pool[FMath::Clamp(P1Slot, 0, FPickRegular::PoolSize - 1)].Type;
        SkillShell.ConfigureForPoolSlot(P1Slot, P1Type);
    }
    Simulation.Reset();
    Simulation.Launch(); ++Match; Accumulator = 0; SkillUses=0;
    bTutorialBout=AutoMatches<=0 && bTutorialPending && bRankedArena;
    TrailHistory.Reset();
    VisualTilt[0]=VisualTilt[1]=FVector2D::ZeroVector;
    RenderYaw[0]=RenderYaw[1]=0.;
    LastImpactTime=-1.; LastImpactStrength=0.;
    if (AutoMatches<=0)
    {
        FeelLabTuning::Apply(Simulation,FeelSettings.Move);
        Simulation.bGyroTrial = !bRankedArena && FParse::Param(FCommandLine::Get(),TEXT("GyroTrial"));
        Simulation.bGyroPush = bRankedArena && bAvatarSelection;
        if (Simulation.bGyroPush) UE_LOG(LogTemp,Display,TEXT("UNIFIED_GYRO_PUSH coefficient=0.015"));
        if (Simulation.bGyroTrial) UE_LOG(LogTemp,Display,TEXT("GYRO_TRIAL_ENABLED"));
        if (Simulation.bGyroTrial && FParse::Param(FCommandLine::Get(),TEXT("GyroLongTrial")))
        {
            Simulation.FrameLimit = 300 * 60;
            UE_LOG(LogTemp,Display,TEXT("GYRO_LONG_TRIAL seconds=300"));
        }
        if(bRankedArena) Simulation.FrameLimit=(bTutorialBout?TutorialSeconds:RankedBoutSeconds)*60;
        Simulation.bStarCrownRim = bRankedArena;
        for (int32 I=0;I<2;++I) Simulation.Position[I]*=Simulation.ArenaScale;
        for (int32 I=0;I<2;++I)
        {
            const int32 Slot = I==0 ? (MatchFlow.bBlindPhase && MatchFlow.BlindChoiceP1>=0 ? MatchFlow.BlindChoiceP1 :
                (MatchFlow.Pick.Count>MatchFlow.CurrentLineupIndex ? MatchFlow.Pick.Lineup[MatchFlow.CurrentLineupIndex] : 0)) :
                (MatchFlow.bBlindPhase && MatchFlow.BlindChoiceP2>=0 ? MatchFlow.BlindChoiceP2 : 1);
            FeelLabTypes::ApplyBey(Simulation,I,Slot);
            UE_LOG(LogTemp,Display,TEXT("BALANCE_V14 player=%d slot=%d natural_s=%.0f hp=%.0f attack=%.2f reduction=%.2f"),
                I+1,Slot,Simulation.NaturalSpinSeconds[I],Simulation.MaxDurability[I],Simulation.Attack[I],Simulation.DamageReduction[I]);
            Simulation.Mass[I]=FeelLabTuning::MassForLevel(50);
        }
        Simulation.SweepObstacle=[this](const FVector2D& A,const FVector2D& B,FVector2D& P,FVector2D& N) {return SweepBowlObstacle(A,B,P,N);};
        Simulation.bWeightCollision=true;
        Simulation.bTacticalSteering=true;
        LaunchSetup.Apply(Simulation);
        Simulation.RingoutStrength=FeelSettings.Ringout/100.;
        UE_LOG(LogTemp,Display,TEXT("INDUSTRIAL_FEEL86 move_multiplier=%d weight=50/50 ringout=%d natural_s=%.0f/%.0f move_mps=%.3f/%.3f"),
            FeelSettings.Move,FeelSettings.Ringout,Simulation.NaturalSpinSeconds[0],Simulation.NaturalSpinSeconds[1],Simulation.BaseMoveSpeed*Simulation.TypeMoveScale[0],Simulation.BaseMoveSpeed*Simulation.TypeMoveScale[1]);
    }
    if (AutoMatches<=0)
    {
        SkillShell.BeginEffects(Simulation,0);
        OpponentSkill.ResetForBout();
        const int32 P2Slot=MatchFlow.bBlindPhase && MatchFlow.BlindChoiceP2>=0 ? MatchFlow.BlindChoiceP2 : 1;
        OpponentSkill.ConfigureForPoolSlot(P2Slot,Simulation.Type[1]);
        OpponentSkill.BeginEffects(Simulation,1);
    }
    Falling[0] = Falling[1] = false;
    FallTime = FallDuration = 0;
    WinnerPresentHold = false;
    ApplyTransforms();
    UE_LOG(LogTemp, Display, TEXT("M1_BATTLE_START match=%d mode=%s target=%d"), Match, MatchFlow.ModeLabel(), MatchFlow.Target());
}
void APrototypeBattleMode::ResetMatch()
{
    if (IronWallFx) IronWallFx->ResetShield();
    if (ChifengFx) ChifengFx->ResetEffect();
    if (ChangxuanFx) ChangxuanFx->ResetEffect();
    if (HengrenFx) HengrenFx->ResetEffect();
    if (ChiwenFx) ChiwenFx->ResetEffect();
    if (GoldFx) GoldFx->ResetShield();
    if (StoneFx) StoneFx->ResetEffect();
    if (FrostFx) FrostFx->ResetEffect();
    if (!Ready || AutoMatches > 0) return;
    bTutorialBout=false;
    if (IsArenaExploring()) { UGameplayStatics::OpenLevel(this, TEXT("/Game/Maps/StadiumIndustrialPolish_v1")); return; }
    // Tier1: ignore R while ringout fall/settle is playing.
    if (IsRingoutPresenting()) return;
    if (bLaunching) EndLaunchPresentation();
    for(AActor* Bey:Beys) if(Bey)Bey->SetActorHiddenInGame(false);
    if (Simulation.Running)
    {
        Simulation.Running = false; Simulation.Reason = TEXT("reset"); Simulation.Winner = -1;
        // Mid-exit: do not apply match-circle score; return lobby.
        MatchFlow.ReturnToLobby();
        Simulation.Reset(); Accumulator = 0;
        Falling[0] = Falling[1] = false;
        FallTime = FallDuration = 0;
        WinnerPresentHold = false;
        ApplyTransforms();
        UE_LOG(LogTemp, Display, TEXT("M1_ABORT_TO_LOBBY"));
        return;
    }
    // From settle screens or ready: R returns to lobby (M1 / locked「再来一局回大厅」).
    if (MatchFlow.State == EMatchFlowState::RoundSettle || MatchFlow.State == EMatchFlowState::MatchSettle
        || MatchFlow.State == EMatchFlowState::Lobby || MatchFlow.State == EMatchFlowState::PickRegular
        || MatchFlow.State == EMatchFlowState::Prep || MatchFlow.State == EMatchFlowState::BlindPick)
    {
        MatchFlow.ReturnToLobby();
        Simulation.Reset(); Accumulator = 0;
        Falling[0] = Falling[1] = false;
        FallTime = FallDuration = 0;
        WinnerPresentHold = false;
        ApplyTransforms();
        UE_LOG(LogTemp, Display, TEXT("M1_BACK_LOBBY"));
        return;
    }
    Simulation.Reset(); Accumulator = 0;
    Falling[0] = Falling[1] = false;
    FallTime = FallDuration = 0;
    WinnerPresentHold = false;
    ApplyTransforms();
}
void APrototypeBattleMode::Launch()
{
    if (!Ready || Simulation.Running || bLaunching) return;
    // Tier1: ignore SPACE while ringout fall/settle is playing.
    if (IsRingoutPresenting()) return;

    if (AutoMatches > 0)
    {
        StartBattleInternal();
        return;
    }

    if (MatchFlow.State == EMatchFlowState::Lobby)
    {
        if (!MatchFlow.TryEnterPickFromLobby()) return;
        UE_LOG(LogTemp, Display, TEXT("PICK_ENTER mode=%s"), MatchFlow.ModeLabel());
        return;
    }
    if (MatchFlow.State == EMatchFlowState::PickRegular)
    {
        ConfirmPick();
        return;
    }
    if (MatchFlow.State == EMatchFlowState::Prep)
    {
        BeginLaunchPresentation();
        return;
    }
    if (MatchFlow.State == EMatchFlowState::BlindPick)
    {
        MatchFlow.TryAdvanceBlindLocal();
        UE_LOG(LogTemp, Display, TEXT("BLIND_ADVANCE locked=%d/%d revealed=%d state=%s"),
            MatchFlow.bBlindLockedP1 ? 1 : 0, MatchFlow.bBlindLockedP2 ? 1 : 0,
            MatchFlow.bBlindRevealed ? 1 : 0, MatchFlow.StateLabel());
        return;
    }
    if (MatchFlow.State == EMatchFlowState::RoundSettle)
    {
        ContinueFromRoundSettle();
        return;
    }
    if (MatchFlow.State == EMatchFlowState::MatchSettle)
    {
        RematchFromMatchSettle();
        return;
    }
}
void APrototypeBattleMode::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (IronWallFx) IronWallFx->SetShieldEnabled(Simulation.Running && !bLaunching && SkillShell.BeyId == TEXT("bilei") && SkillShell.bFxActive);
    if (ChifengFx) ChifengFx->SetEnabled(Simulation.Running && !bLaunching && SkillShell.BeyId == TEXT("chifeng") && SkillShell.bFxActive);
    if (ChangxuanFx) ChangxuanFx->SetEnabled(Simulation.Running && !bLaunching && SkillShell.BeyId == TEXT("changxuan") && SkillShell.bFxActive);
    if (HengrenFx) HengrenFx->SetEnabled(Simulation.Running && !bLaunching && SkillShell.BeyId == TEXT("hengblade") && SkillShell.bFxActive);
    if (ChiwenFx) ChiwenFx->SetArmed(Simulation.Running && !bLaunching && SkillShell.BeyId == TEXT("chiwen") && SkillShell.bFxActive);
    if (GoldFx) GoldFx->SetShieldEnabled(Simulation.Running && !bLaunching && SkillShell.BeyId == TEXT("huangkai") && SkillShell.bFxActive);
    if (StoneFx) StoneFx->SetEnabled(Simulation.Running && !bLaunching && SkillShell.BeyId == TEXT("cuipan") && SkillShell.bFxActive);
    if (FrostFx) FrostFx->SetEnabled(Simulation.Running && !bLaunching && SkillShell.BeyId == TEXT("shuanghuan") && SkillShell.bFxActive);
    if (AutoMatches <= 0) TickLaunchPresentation(DeltaSeconds);
    UpdateArenaExploration();
    for (int32 I = 0; I < ArenaScoreDisplays.Num(); ++I)
        if (ArenaScoreDisplays[I] && ArenaDisplayedScores[I] != MatchFlow.Score[I])
        {
            // shortcut: race-to-8 scores top out at 10; extend digit meshes with higher targets.
            if (ArenaScoreDigits.IsValidIndex(MatchFlow.Score[I]))
                ArenaScoreDisplays[I]->SetStaticMesh(ArenaScoreDigits[MatchFlow.Score[I]]);
            ArenaDisplayedScores[I] = MatchFlow.Score[I];
        }
    if (BattleView && AutoMatches <= 0 && !bLaunching)
    {
        const bool WatchingBattle = MatchFlow.State == EMatchFlowState::Fighting
            || MatchFlow.State == EMatchFlowState::RoundSettle || MatchFlow.State == EMatchFlowState::MatchSettle;
        const bool UseFaceView = !bLaunching && bFaceView && (WatchingBattle || MatchFlow.State == EMatchFlowState::Prep);
        if (FaceCharacter) FaceCharacter->SetActorHiddenInGame(UseFaceView || IsArenaExploring());
        if (FaceBackdrop) FaceBackdrop->SetActorHiddenInGame(!UseFaceView);
        if (FemaleActor) FemaleActor->SetActorHiddenInGame(UseFaceView);
        const bool LobbyView = MatchFlow.State == EMatchFlowState::Lobby;
        const bool SafePrepView = bRankedArena && MatchFlow.State == EMatchFlowState::Prep;
        const FVector LobbyLocation(-450, 1450, 600);
        const FVector BattleLocation(0, 420, 1450);
        const FVector DesiredLocation = UseFaceView ? FaceAnchor + FVector(0, 0, FaceHeight) : (WatchingBattle || SafePrepView) ? BattleLocation : LobbyView ? LobbyLocation : PreparationViewLocation;
        const FRotator DesiredRotation = UseFaceView ? FRotator(FacePitch, (-FaceAnchor).Rotation().Yaw, 0)
            : (WatchingBattle || SafePrepView) ? (FVector(0, 0, 60) - BattleLocation).Rotation() : LobbyView ? (FVector(-450, 0, 100) - LobbyLocation).Rotation() : PreparationViewRotation;
        const double Age=GetWorld()->GetRealTimeSeconds()-LastImpactTime;
        const double Shake=Simulation.Running && Age<.10 && LastImpactStrength>=.5 ? 1.3*LastImpactStrength*FMath::Exp(-Age*32.) : 0.;
        const FVector ImpactOffset(FMath::Sin(Age*155.)*Shake,0,FMath::Cos(Age*193.)*Shake*.5);
        BattleView->SetActorLocationAndRotation(
            FMath::VInterpTo(BattleView->GetActorLocation(), DesiredLocation + ImpactOffset, DeltaSeconds, 3.f),
            FMath::RInterpTo(BattleView->GetActorRotation(), DesiredRotation, DeltaSeconds, 3.f));
        auto* Camera = BattleView->GetCameraComponent();
        Camera->SetFieldOfView(FMath::FInterpTo(Camera->FieldOfView, UseFaceView ? 80.f : LobbyView ? 70.f : PreparationFOV, DeltaSeconds, 3.f));
    }
    if (!Ready) return;
    for (int32 I=0;I<2;++I)
    {
        VisualTilt[I]*=FMath::Exp(-DeltaSeconds/.6);
        if (Simulation.Running) RenderYaw[I]=FMath::Fmod(RenderYaw[I]+VisualSpinRate(Simulation.bStagedMobility ? Simulation.MobilityFactor[I] : Simulation.Spin[I], Simulation.Type[I])*DeltaSeconds*(I==0 ? 1. : -1.),360.);
    }
    if (AutoMatches <= 0) ApplyBeyArt();
    if(bLaunching) {ApplyTransforms();return;}
    if (!Simulation.Running)
    {
        if (IsRingoutPresenting())
        {
            FallTime = FMath::Min(FallDuration, FallTime + DeltaSeconds);
            ApplyTransforms();
        }
        return;
    }
    if(AutoMatches<=0 && LastImpactStrength>=.65 && GetWorld()->GetRealTimeSeconds()-LastImpactTime<.035) return;
    Accumulator += DeltaSeconds;
    while (Accumulator + 1.e-9 >= FBattleSimulation::Step && Simulation.Running)
    {
        Accumulator -= FBattleSimulation::Step;
        const int32 PreviousHits = Simulation.Hits;
        const double PreviousDurability[2]={Simulation.Durability[0],Simulation.Durability[1]};
        Simulation.Tick();
        if(AutoMatches<=0)
        {
            FVector TrailPositions[2];
            for(int32 I=0;I<2;++I)
            {
                const FVector2D P=Simulation.Position[I];
                TrailPositions[I]=FVector(P.X*100,P.Y*100,FBattleSimulation::BowlHeight(P.Size()/Simulation.ArenaScale)*100+15);
            }
            TrailHistory.Record(Simulation.Frames,TrailPositions[0],TrailPositions[1]);
        }
        if(GoldFx && SkillShell.BeyId==TEXT("huangkai") && SkillShell.bFxActive && Simulation.Hits>PreviousHits)
            GoldFx->NotifyHit(FVector(Simulation.Position[1].X-Simulation.Position[0].X,Simulation.Position[1].Y-Simulation.Position[0].Y,0));
        // Capture the charged contact before AfterStep consumes the next-hit skill.
        if (ChiwenFx && SkillShell.BeyId == TEXT("chiwen") && SkillShell.bFxActive && Simulation.Hits > PreviousHits)
            ChiwenFx->ConsumeHit(FVector(Simulation.Position[1].X-Simulation.Position[0].X, Simulation.Position[1].Y-Simulation.Position[0].Y, 0));
        if (AutoMatches<=0)
        {
            SkillShell.AfterStep(Simulation,0,FBattleSimulation::Step);
            OpponentSkill.AfterStep(Simulation,1,FBattleSimulation::Step);
            if (IronWallFx) IronWallFx->SetShieldEnabled(Simulation.Running && SkillShell.BeyId == TEXT("bilei") && SkillShell.bFxActive);
            if (ChifengFx) ChifengFx->SetEnabled(Simulation.Running && SkillShell.BeyId == TEXT("chifeng") && SkillShell.bFxActive);
            if (ChangxuanFx) ChangxuanFx->SetEnabled(Simulation.Running && SkillShell.BeyId == TEXT("changxuan") && SkillShell.bFxActive);
            if (HengrenFx) HengrenFx->SetEnabled(Simulation.Running && SkillShell.BeyId == TEXT("hengblade") && SkillShell.bFxActive);
            if (ChiwenFx) ChiwenFx->SetArmed(Simulation.Running && SkillShell.BeyId == TEXT("chiwen") && SkillShell.bFxActive);
            if (GoldFx) GoldFx->SetShieldEnabled(Simulation.Running && SkillShell.BeyId == TEXT("huangkai") && SkillShell.bFxActive);
            if (StoneFx) StoneFx->SetEnabled(Simulation.Running && SkillShell.BeyId == TEXT("cuipan") && SkillShell.bFxActive);
            if (FrostFx) FrostFx->SetEnabled(Simulation.Running && SkillShell.BeyId == TEXT("shuanghuan") && SkillShell.bFxActive);
        }
        if (AutoMatches == 0 && Simulation.WallHitPlayer >= 0 && Simulation.WallClosing > .25)
        {
            if (IronWallFx && Simulation.WallHitPlayer == 0) IronWallFx->NotifyHit(FVector(Simulation.Position[0].X, Simulation.Position[0].Y, 0));
            const double Now = GetWorld()->GetRealTimeSeconds();
            if (Now - LastContactAudioTime >= .07 && ContactSounds.Num() == 3)
            {
                LastContactAudioTime = Now;
                const float Strength = FMath::Clamp(static_cast<float>(Simulation.WallClosing / FBattleSimulation::KickReferenceSpeed), 0.f, 1.f);
                UGameplayStatics::SpawnSound2D(this, ContactSounds[Strength > .6 ? 1 : 0], ContactMasterVolume * (.18f + .3f * Strength), 1.08f);
                const FVector2D N = Simulation.Position[Simulation.WallHitPlayer].GetSafeNormal();
                const FVector Point=GetBeyLocation(Simulation.WallHitPlayer)+FVector(N.X*22.,N.Y*22.,12.);
                for (int32 J = 0; J < 2 && Strength > .35; ++J)
                    DrawDebugLine(GetWorld(), Point, Point + FVector(-N.X * (4 + J * 3), -N.Y * (4 + J * 3), 3 + J * 3), FColor(255, 205, 100), false, .06f, 0, .6f);
                UE_LOG(LogTemp, Display, TEXT("WALL_CONTACT player=%d speed=%.3f count=%d"), Simulation.WallHitPlayer + 1, Simulation.WallClosing, Simulation.WallHits);
            }
        }
        if (AutoMatches == 0 && ScrapeSound && Simulation.ScrapeSpeed > .25 && GetWorld()->GetRealTimeSeconds() - LastScrapeTime > .18)
        {
            LastScrapeTime = GetWorld()->GetRealTimeSeconds();
            UGameplayStatics::SpawnSound2D(this, ScrapeSound, ContactMasterVolume * .15f * FMath::Clamp(static_cast<float>(Simulation.ScrapeSpeed), 0.f, 1.f));
        }
        // QA filming only: -ProtoDemoRingout + -ProtoAuto=<n> forces a near-rim ringout at 1s.
        // NEVER active during interactive Play (AutoMatches==0), even if the editor cmdline still has the flag.
        // Does not change frozen feel constants.
        if (AutoMatches > 0 && FParse::Param(FCommandLine::Get(), TEXT("ProtoDemoRingout")) && Simulation.Frames == 60)
        {
            Simulation.Position[0] = FVector2D(2.29, 0.05);
            Simulation.Position[1] = FVector2D(1.95, -0.15);
            UE_LOG(LogTemp, Warning, TEXT("BATTLE_DEMO_RINGOUT forced P1 outside for filming (AutoMatches=%d)"), AutoMatches);
        }
        if (Simulation.Hits != PreviousHits)
        {
            if (IronWallFx) IronWallFx->NotifyHit(FVector(Simulation.Position[1].X - Simulation.Position[0].X, Simulation.Position[1].Y - Simulation.Position[0].Y, 0));
            if (ChifengFx) ChifengFx->NotifyHit(FVector(Simulation.Position[1].X - Simulation.Position[0].X, Simulation.Position[1].Y - Simulation.Position[0].Y, 0));
            if (HengrenFx) HengrenFx->NotifyHit(FVector(Simulation.Position[1].X - Simulation.Position[0].X, Simulation.Position[1].Y - Simulation.Position[0].Y, 0));
            const double Now = GetWorld()->GetRealTimeSeconds();
            const double Strength = FMath::Clamp(Simulation.LastClosing / FBattleSimulation::KickReferenceSpeed, 0., 1.);
            LastImpactTime = Now; LastImpactStrength = Strength;
            for(int32 I=0;I<2;++I) ImpactDamage[I]=FMath::Max(0.,PreviousDurability[I]-Simulation.Durability[I]);
            const FVector2D Normal = (Simulation.Position[1] - Simulation.Position[0]).GetSafeNormal();
            VisualTilt[0] += Normal * (12. * Strength);
            VisualTilt[1] -= Normal * (12. * Strength);
            for (int32 I = 0; I < 2; ++I) VisualTilt[I] = VisualTilt[I].GetClampedToMaxSize(25.);
            if (AutoMatches == 0 && Strength > .4)
            {
                FVector Point = (GetBeyLocation(0) + GetBeyLocation(1)) * .5 + FVector(0, 0, 15);
                FRandomStream Effects(Simulation.Frames * 71 + Simulation.Hits);
                // shortcut: development-build streaks; replace with Niagara before a shipping build.
                for (int32 N = 0; N < 5 + FMath::RoundToInt(Strength * 6); ++N)
                {
                    const FVector Ray = Effects.VRand() * Effects.FRandRange(8.f, 24.f) * Strength;
                    DrawDebugLine(GetWorld(), Point, Point + Ray, FColor(255, 210, 105), false, .12f, 0, 1.2f);
                }
            }
            if (AutoMatches <= 0 && ContactMasterVolume > 0 && ContactSounds.Num() == 3 && Now - LastContactAudioTime >= .032)
            {
                const int32 Variant = Strength < .33 ? 0 : Strength < .66 ? 1 : 2;
                if (USoundBase* Sound = ContactSounds[Variant])
                {
                    LastContactAudioTime = Now;
                    const float Volume = ContactMasterVolume * (.25f + .5f * FMath::Clamp(static_cast<float>(Simulation.LastClosing / 4.), 0.f, 1.f));
                    const float Pitch = 1.f + .04f * ((Simulation.Hits % 5) - 2);
                    // Screen-space impact keeps volume consistent across the selectable cameras.
                    UAudioComponent* Audio = UGameplayStatics::SpawnSound2D(this, Sound, Volume, Pitch);
                    UE_LOG(LogTemp, Display, TEXT("COLLISION_AUDIO hit=%d variant=%d volume=%.3f playing=%d"), Simulation.Hits, Variant + 1, Volume, Audio && Audio->IsPlaying() ? 1 : 0);
                }
            }
            UE_LOG(LogTemp, Display, TEXT("BATTLE_CONTACT match=%d frame=%d closing=%.6f kick_scale=%.6f before_a=%.6f before_b=%.6f after_a=%.6f after_b=%.6f translational_energy_ratio=%.6f"),
                Match, Simulation.Frames, Simulation.LastClosing, Simulation.LastKickScale,
                Simulation.LastSpeedBefore[0], Simulation.LastSpeedBefore[1],
                Simulation.LastSpeedAfter[0], Simulation.LastSpeedAfter[1], Simulation.LastEnergyRatio);
        }
        CheckSurfaceBoundary();
        if (!Ready) return;
        if (!Simulation.Running) FinishMatch();
        if (Simulation.Hits!=PreviousHits && Simulation.LastKickScale>=.65 && AutoMatches<=0) {Accumulator=0.;break;}
    }
    ApplyTransforms();
    if (((IronWallFx && IronWallFx->IsVisible()) || (ChifengFx && ChifengFx->IsVisible()) || (ChangxuanFx && ChangxuanFx->IsVisible()) || (HengrenFx && HengrenFx->IsVisible()) || (ChiwenFx && ChiwenFx->IsVisible()) || (GoldFx && GoldFx->IsVisible()) || (StoneFx && StoneFx->IsVisible())) && Simulation.Running)
    {
        const FVector2D P = Simulation.Position[0];
        double Left, Right, Back, Front;
        if (SampleHeight(P + FVector2D(-.05, 0), Left) && SampleHeight(P + FVector2D(.05, 0), Right)
            && SampleHeight(P + FVector2D(0, -.05), Back) && SampleHeight(P + FVector2D(0, .05), Front))
        {
            const FVector Normal = FVector(-(Right - Left) / .1, -(Front - Back) / .1, 1.).GetSafeNormal();
            if (IronWallFx) IronWallFx->SetGroundNormal(Normal);
            if (ChifengFx) ChifengFx->SetGroundNormal(Normal);
            if (ChangxuanFx) ChangxuanFx->SetGroundNormal(Normal);
            if (HengrenFx) HengrenFx->SetGroundNormal(Normal);
            if (ChiwenFx) ChiwenFx->SetGroundNormal(Normal);
            if (GoldFx) GoldFx->SetGroundNormal(Normal);
            if (StoneFx) StoneFx->SetGroundNormal(Normal);
        }
        else
        {
            if (IronWallFx) IronWallFx->SetGroundNormal(FVector::UpVector);
            if (ChifengFx) ChifengFx->SetGroundNormal(FVector::UpVector);
            if (ChangxuanFx) ChangxuanFx->SetGroundNormal(FVector::UpVector);
            if (HengrenFx) HengrenFx->SetGroundNormal(FVector::UpVector);
            if (ChiwenFx) ChiwenFx->SetGroundNormal(FVector::UpVector);
            if (GoldFx) GoldFx->SetGroundNormal(FVector::UpVector);
            if (StoneFx) StoneFx->SetGroundNormal(FVector::UpVector);
        }
    }
    if(FrostFx && FrostFx->IsVisible() && Simulation.Running) {
        const FVector2D P=Simulation.Position[1];double L,R,B,F;
        if(SampleHeight(P+FVector2D(-.05,0),L)&&SampleHeight(P+FVector2D(.05,0),R)&&SampleHeight(P+FVector2D(0,-.05),B)&&SampleHeight(P+FVector2D(0,.05),F))
            FrostFx->SetGroundNormal(FVector(-(R-L)/.1,-(F-B)/.1,1.).GetSafeNormal());
        else FrostFx->SetGroundNormal(FVector::UpVector);
    }
    if (!Simulation.Running && AutoMatches > 0)
    {
        if (Match < AutoMatches) Launch();
        else { UE_LOG(LogTemp, Display, TEXT("BATTLE_AUTO_COMPLETE matches=%d"), Match); FPlatformMisc::RequestExit(false); }
    }
}
void APrototypeBattleMode::CheckSurfaceBoundary()
{
    bool Out[2] = {false, false};
    for (int32 I = 0; I < 2; ++I)
    {
        double Height;
        Out[I] = Simulation.Position[I].Size() > 2.28*Simulation.ArenaScale || !SampleHeight(Simulation.Position[I], Height);
        // The visible circular rim is polygonal: its chord falls just inside radius 2.28.
        if (Out[I] && Simulation.Position[I].Size() < 2.2*Simulation.ArenaScale)
        {
            Error = TEXT("Missing collision inside playable bowl."); Ready = false;
            UE_LOG(LogTemp, Error, TEXT("BATTLE_SURFACE_FAILED inside bowl"));
            Simulation.Running = false;
            if (AutoMatches > 0) FPlatformMisc::RequestExitWithStatus(false, 1);
            return;
        }
    }
    if (Out[0] || Out[1])
    {
        Simulation.Running = false; Simulation.Reason = TEXT("ringout");
        Simulation.Winner = Out[0] == Out[1] ? -1 : (Out[0] ? 1 : 0);
    }
}
void APrototypeBattleMode::ApplyTransforms()
{
    for (int32 I = 0; I < 2; ++I)
    {
        if (Falling[I])
        {
            const double FloorZ = GroundFloorZ();
            Beys[I]->SetActorLocation(RingoutLocation(FallStart[I], FloorZ, FallTime), false);
            Beys[I]->SetActorRotation(RingoutRotation(FallTime, FallDuration, I), ETeleportType::None);
            continue;
        }
        FVector2D P = Simulation.Position[I];
        // Tier1 presentation: keep winner clearly inside the playable bowl (not parked on the rim).
        if (WinnerPresentHold && Simulation.Winner == I) P = WinnerPresentPos;
        double Height = 1.07;
        if (P.Size() <= 2.28*Simulation.ArenaScale && !SampleHeight(P, Height) && Simulation.Reason != TEXT("ringout"))
        {
            Error = TEXT("Missing visible bowl collision under bey."); Ready = false;
            UE_LOG(LogTemp, Error, TEXT("BATTLE_SURFACE_FAILED x=%f y=%f"), P.X, P.Y);
            if (AutoMatches > 0) FPlatformMisc::RequestExitWithStatus(false, 1);
            return;
        }
        if (WinnerPresentHold && Simulation.Winner == I && P.Size() > 2.28*Simulation.ArenaScale)
        {
            // Held inward; sample may miss outside rim 鈥?keep last bowl-center height band.
            Height = FBattleSimulation::BowlHeight(P.Size()/Simulation.ArenaScale);
        }
        // Visual spin only; the simulation's momentum and collision rules stay unchanged.
        const double VisualYaw = AutoMatches > 0 ? Simulation.YawDeg[I] : RenderYaw[I];
        const double WobbleEnergy = Simulation.bStagedMobility ? Simulation.MobilityFactor[I] : Simulation.Spin[I];
        const double WobbleThreshold = Simulation.bStagedMobility ? .5 : .22;
        const double Remaining = MobilityProfile::RemainingSpinSeconds(Simulation.Spin[I], FBattleSimulation::SpinStopThreshold, Simulation.SpinDecay[I] * Simulation.SkillEnemyDecayMul[1-I]);
        const double Wobble = !Simulation.Running ? 0. : Simulation.bGyroTrial
            ? FMath::Clamp((5. - Remaining) / 5., 0., 1.) * 15.
            : FMath::Clamp((WobbleThreshold - WobbleEnergy) / WobbleThreshold, 0., 1.) * 8.;
        const double Phase = Simulation.Frames * FBattleSimulation::Step * 13. + I * PI;
        const FVector2D Tilt = ((Simulation.bGyroTrial ? Simulation.GyroTilt[I] : VisualTilt[I]) + FVector2D(FMath::Sin(Phase), FMath::Cos(Phase)) * Wobble) * VisualTiltScale(Simulation.Spin[I]);
        const double Pitch = Tilt.X, Roll = Tilt.Y;
        FVector Location(P.X * 100, P.Y * 100, Height * 100 + 0.5);
        // Approved refined launch: hold at the rigged LaunchSocket, then a .7 s smooth flight.
        const bool bHasHand = bLaunchHeroReady && (I == 0 || FemalePose != nullptr);
        if (bLaunching && bHasHand && LaunchAge < LabLaunch::Release)
        {
            Location = LaunchHands[I];
            Beys[I]->SetActorScale3D(BeyBaseScale[I] * .2);
            if (BeyArt[I]) BeyArt[I]->SetWorldScale3D(BeyArtBaseScale[I] * .2);
        }
        if (bLaunching && LaunchAge >= LabLaunch::Release)
        {
            const double T = LabLaunch::Flight(LaunchAge);
            const FVector Start = bHasHand ? LaunchHands[I] : Location + FVector(100, 60, 150);
            Location = FMath::Lerp(Start, Location, T) + FVector(0, 0, 55. * FMath::Sin(T * PI));
            Beys[I]->SetActorScale3D(BeyBaseScale[I] * FMath::Lerp(.2, 1., T));
            if (BeyArt[I]) BeyArt[I]->SetWorldScale3D(BeyArtBaseScale[I] * FMath::Lerp(.2, 1., T));
        }
        Beys[I]->SetActorLocationAndRotation(Location, FRotator(Pitch, FMath::Fmod(VisualYaw, 360.0), Roll), false);

    }
}

void APrototypeBattleMode::OpenCollection()
{
    MatchFlow.EnterCollection();
    UE_LOG(LogTemp, Display, TEXT("COLLECTION_OPEN"));
}

void APrototypeBattleMode::CloseCollection()
{
    if (MatchFlow.State != EMatchFlowState::Collection) return;
    if (MatchFlow.CollectionFocus >= 0)
    {
        MatchFlow.CloseCollectionDetail();
        UE_LOG(LogTemp, Display, TEXT("COLLECTION_DETAIL_CLOSE"));
        return;
    }
    MatchFlow.ExitCollectionToLobby();
    UE_LOG(LogTemp, Display, TEXT("COLLECTION_CLOSE"));
}

void APrototypeBattleMode::SelectCollectionSlot(int32 Index)
{
    if (MatchFlow.State != EMatchFlowState::Collection) return;
    if (MatchFlow.CollectionFocus >= 0) return; // already in detail; ignore grid
    if (Index < 0 || Index >= FCollectionCatalog::Count) return;
    MatchFlow.OpenCollectionDetail(Index);
    UE_LOG(LogTemp, Display, TEXT("COLLECTION_DETAIL id=%s"), FCollectionCatalog::Get(Index).Id);
}

void APrototypeBattleMode::FireActiveSkill()
{
    if (MatchFlow.State != EMatchFlowState::Fighting || !Simulation.Running || bLaunching) return;
    if (!SkillShell.TryFire())
    {
        UE_LOG(LogTemp, Display, TEXT("SKILL_FIRE_BLOCKED hits=%d need=%d"), SkillShell.HitsDealt, SkillShell.Need());
        return;
    }
    ++SkillUses;
    if(FeedbackSounds.IsValidIndex(0) && FeedbackSounds[0]) UGameplayStatics::PlaySound2D(this,FeedbackSounds[0],ContactMasterVolume*.45f);
    if (SkillShell.Kind == EActiveSkillKind::ChiwenNextExtra)
    {
        Simulation.PendingExtraKickMul[0] = SkillShell.ExtraKickMulPending;
        UE_LOG(LogTemp, Display, TEXT("SKILL_FIRE chiwen next_extra=%.2f tier=%d next_need=%d"), SkillShell.ExtraKickMulPending, SkillShell.Tier, SkillShell.Need());
    }
    else
    {
        UE_LOG(LogTemp, Display, TEXT("SKILL_FIRE id=%s duration=%.2f tier=%d next_need=%d"), *SkillShell.BeyId, SkillShell.FxRemainSec, SkillShell.Tier, SkillShell.Need());
    }
    SkillShell.ApplyEffects(Simulation,0);
    if(SkillShell.BeyId==TEXT("huangkai") && Beys.IsValidIndex(0) && Beys[0])
    {
        if(!GoldFx) {
            GoldFx=NewObject<UIronWallEffectComponent>(Beys[0],TEXT("GoldFxEffect"));
            GoldFx->SetupAttachment(Beys[0]->GetRootComponent());GoldFx->RegisterComponent();
            if(!GoldFx->InitializeVisuals(true)) {GoldFx->DestroyComponent();GoldFx=nullptr;}
        }
        if(GoldFx)GoldFx->SetShieldEnabled(true,ContactMasterVolume);
    }
    if(SkillShell.BeyId==TEXT("cuipan") && Beys.IsValidIndex(0) && Beys[0])
    {
        if(!StoneFx) {
            StoneFx=NewObject<UChangxuanEffectComponent>(Beys[0],TEXT("StoneFxEffect"));
            StoneFx->SetupAttachment(Beys[0]->GetRootComponent());StoneFx->RegisterComponent();
            if(!StoneFx->InitializeVisuals(true)) {StoneFx->DestroyComponent();StoneFx=nullptr;}
        }
        if(StoneFx)StoneFx->SetEnabled(true);
    }
    if(SkillShell.BeyId==TEXT("shuanghuan") && Beys.IsValidIndex(1) && Beys[1])
    {
        if(!FrostFx) {
            FrostFx=NewObject<UHengrenEffectComponent>(Beys[1],TEXT("FrostFxEffect"));
            FrostFx->SetupAttachment(Beys[1]->GetRootComponent());FrostFx->RegisterComponent();
            if(!FrostFx->InitializeVisuals(true)) {FrostFx->DestroyComponent();FrostFx=nullptr;}
        }
        if(FrostFx)FrostFx->SetEnabled(true);
    }
    if (SkillShell.BeyId == TEXT("chiwen") && Beys.IsValidIndex(0) && Beys[0])
    {
        if (!ChiwenFx)
        {
            ChiwenFx = NewObject<UChiwenEffectComponent>(Beys[0], TEXT("ChiwenEffect"));
            ChiwenFx->SetupAttachment(Beys[0]->GetRootComponent());ChiwenFx->RegisterComponent();
            if (!ChiwenFx->InitializeVisuals()) { ChiwenFx->DestroyComponent(); ChiwenFx = nullptr; }
        }
        if (ChiwenFx) ChiwenFx->SetArmed(true);
    }
    if (SkillShell.BeyId == TEXT("hengblade") && Beys.IsValidIndex(0) && Beys[0])
    {
        if (!HengrenFx)
        {
            HengrenFx = NewObject<UHengrenEffectComponent>(Beys[0], TEXT("HengrenEffect"));
            HengrenFx->SetupAttachment(Beys[0]->GetRootComponent());
            HengrenFx->RegisterComponent();
            if (!HengrenFx->InitializeVisuals()) { HengrenFx->DestroyComponent(); HengrenFx = nullptr; }
        }
        if (HengrenFx) HengrenFx->SetEnabled(true);
    }
    if (SkillShell.BeyId == TEXT("changxuan") && Beys.IsValidIndex(0) && Beys[0])
    {
        if (!ChangxuanFx)
        {
            ChangxuanFx = NewObject<UChangxuanEffectComponent>(Beys[0], TEXT("ChangxuanEffect"));
            ChangxuanFx->SetupAttachment(Beys[0]->GetRootComponent());
            ChangxuanFx->RegisterComponent();
            if (!ChangxuanFx->InitializeVisuals()) { ChangxuanFx->DestroyComponent(); ChangxuanFx = nullptr; }
        }
        if (ChangxuanFx) ChangxuanFx->SetEnabled(true);
    }
    if (SkillShell.BeyId == TEXT("chifeng") && Beys.IsValidIndex(0) && Beys[0])
    {
        if (!ChifengFx)
        {
            ChifengFx = NewObject<UChifengEffectComponent>(Beys[0], TEXT("ChifengEffect"));
            ChifengFx->SetupAttachment(Beys[0]->GetRootComponent());
            ChifengFx->RegisterComponent();
            if (!ChifengFx->InitializeVisuals()) { ChifengFx->DestroyComponent(); ChifengFx = nullptr; }
        }
        if (ChifengFx) ChifengFx->SetEnabled(true);
    }
    if (SkillShell.BeyId == TEXT("bilei") && Beys.IsValidIndex(0) && Beys[0])
    {
        if (!IronWallFx)
        {
            IronWallFx = NewObject<UIronWallEffectComponent>(Beys[0], TEXT("IronWallEffect"));
            IronWallFx->SetupAttachment(Beys[0]->GetRootComponent());
            IronWallFx->RegisterComponent();
            if (!IronWallFx->InitializeVisuals()) { IronWallFx->DestroyComponent(); IronWallFx = nullptr; }
        }
        if (IronWallFx) IronWallFx->SetShieldEnabled(true, ContactMasterVolume);
    }
}


void APrototypeBattleMode::ApplyBeyArt()
{
    if (ImportedBeys.Num() < FPickRegular::PoolSize || BeyArt.Num() != 2) return;
    const int32 P1 = MatchFlow.bBlindPhase && MatchFlow.BlindChoiceP1 >= 0 ? MatchFlow.BlindChoiceP1
        : MatchFlow.Pick.Count > MatchFlow.CurrentLineupIndex ? MatchFlow.Pick.Lineup[MatchFlow.CurrentLineupIndex] : 0;
    const int32 P2 = MatchFlow.bBlindPhase && MatchFlow.BlindChoiceP2 >= 0 ? MatchFlow.BlindChoiceP2 : 1;
    const int32 Slots[2] = {P1, P2};
    for (int32 I = 0; I < 2; ++I)
    {
        if (!Beys[I]) continue;
        auto* Original = Beys[I]->FindComponentByClass<UStaticMeshComponent>();
        if (!Original) continue;
        // Direct pool-slot -> ImportedBeys[slot]; missing mesh keeps original placeholder visible.
        const int32 Slot = FMath::Clamp(Slots[I], 0, ImportedBeys.Num() - 1);
        UStaticMesh* Mesh = ImportedBeys[Slot];
        if (!BeyArt[I] && Mesh)
        {
            BeyArt[I] = NewObject<UStaticMeshComponent>(Beys[I]);
            BeyArt[I]->SetupAttachment(Beys[I]->GetRootComponent());
            BeyArt[I]->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            BeyArt[I]->SetAbsolute(false, false, true);
            BeyArt[I]->RegisterComponent();
        }
        Original->SetVisibility(Mesh == nullptr);
        if (!BeyArt[I]) continue;
        BeyArt[I]->SetVisibility(Mesh != nullptr);
        if (!Mesh || BeyArt[I]->GetStaticMesh() == Mesh) continue;
        BeyArt[I]->SetStaticMesh(Mesh);
        const FBoxSphereBounds Bounds = Mesh->GetBounds();
        const float Scale = 40.f / (2.f * FMath::Max(Bounds.BoxExtent.X, Bounds.BoxExtent.Y));
        BeyArt[I]->SetWorldScale3D(FVector(Scale));
        const FVector Offset(-Bounds.Origin.X, -Bounds.Origin.Y, Bounds.BoxExtent.Z - Bounds.Origin.Z);
        BeyArt[I]->SetRelativeLocation(Offset * Scale / Beys[I]->GetActorScale3D());
        UE_LOG(LogTemp, Display, TEXT("BEY_ART player=%d slot=%d mesh=%s diameter_cm=40"), I + 1, Slots[I], *Mesh->GetPathName());
    }
}
void APrototypeBattleMode::FinishMatch()
{
    if (IronWallFx) IronWallFx->ResetShield();
    if (ChifengFx) ChifengFx->ResetEffect();
    if (ChangxuanFx) ChangxuanFx->ResetEffect();
    if (HengrenFx) HengrenFx->ResetEffect();
    if (ChiwenFx) ChiwenFx->ResetEffect();
    if (GoldFx) GoldFx->ResetShield();
    if (StoneFx) StoneFx->ResetEffect();
    if (FrostFx) FrostFx->ResetEffect();
    FallTime = 0;
    FallDuration = 0;
    WinnerPresentHold = false;
    const double FloorZ = GroundFloorZ();
    for (int32 I = 0; I < 2; ++I)
    {
        Falling[I] = Simulation.Reason == TEXT("ringout") && Simulation.Winner != I && (AutoMatches == 0 || FParse::Param(FCommandLine::Get(), TEXT("ProtoDemoRingout")));
        if (Falling[I])
        {
            double Height = 1.07;
            SampleHeight(Simulation.Position[I], Height);
            FallStart[I] = FVector(Simulation.Position[I].X * 100, Simulation.Position[I].Y * 100, Height * 100 + 0.5);
            FallDuration = FMath::Max(FallDuration, RingoutFallDuration(FallStart[I], FloorZ));
        }
    }
    // Winner freeze: if near the rim, present slightly inward so loser/winner do not both read as "on the lip".
    if (Simulation.Reason == TEXT("ringout") && Simulation.Winner >= 0 && (AutoMatches == 0 || FParse::Param(FCommandLine::Get(), TEXT("ProtoDemoRingout"))))
    {
        const int32 W = Simulation.Winner;
        FVector2D P = Simulation.Position[W];
        const double R = P.Size();
        const double PresentRadial = 1.65*Simulation.ArenaScale; // metres, well inside OUT_RADIUS 2.28
        if (R > PresentRadial && R > 1.e-6) P *= (PresentRadial / R);
        WinnerPresentPos = P;
        WinnerPresentHold = true;
    }
    const FString Line = FString::Printf(TEXT("%d,%.6f,%d,%.6f,%s,%d\n"), Match,
        Simulation.FirstHitFrame < 0 ? -1.0 : Simulation.FirstHitFrame * FBattleSimulation::Step,
        Simulation.Hits, Simulation.Frames * FBattleSimulation::Step, *Simulation.Reason, Simulation.Winner + 1);
    if (!FFileHelper::SaveStringToFile(Line, *LogPath, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM, &IFileManager::Get(), FILEWRITE_Append))
    {
        Error = TEXT("Cannot append match log."); Ready = false;
        if (AutoMatches > 0) FPlatformMisc::RequestExitWithStatus(false, 1);
    }
    UE_LOG(LogTemp, Display, TEXT("BATTLE_RESULT %s"), *Line.TrimEnd());
    if (AutoMatches <= 0 && Simulation.Reason != TEXT("reset"))
    {
        const int32 Cue=Simulation.Winner==0?1:2;
        if(FeedbackSounds.IsValidIndex(Cue) && FeedbackSounds[Cue]) UGameplayStatics::PlaySound2D(this,FeedbackSounds[Cue],ContactMasterVolume*.45f);
        const EScoreTag Tag = (Simulation.ScoreTag == ESimScoreTag::XTR) ? EScoreTag::XTR
            : (Simulation.ScoreTag == ESimScoreTag::OVR) ? EScoreTag::OVR : EScoreTag::None;
        if(bTutorialBout)
        {
            MatchFlow.OnTutorialEnded(Simulation.Reason,Simulation.Winner);
            const FString TutorialFile=FPaths::ProjectSavedDir()/TEXT("TutorialCompleted.txt");
            bTutorialPending=!FFileHelper::SaveStringToFile(TEXT("completed"),*TutorialFile);
            if(bTutorialPending) UE_LOG(LogTemp,Warning,TEXT("TUTORIAL_SAVE_FAILED %s"),*TutorialFile);
        }
        else MatchFlow.OnBattleEnded(Simulation.Reason, Simulation.Winner, Tag);
        const FRoundScoreDelta& D = MatchFlow.LastDelta;
        UE_LOG(LogTemp, Display, TEXT("M1_SCORE reason=%s tag=%s winner=%d delta=%d:%d total=%d:%d target=%d state=%s"),
            *Simulation.Reason, ScoreTagLabel(D.Tag), Simulation.Winner, D.Delta[0], D.Delta[1],
            MatchFlow.Score[0], MatchFlow.Score[1], MatchFlow.Target(), MatchFlow.StateLabel());
        if (MatchFlow.State == EMatchFlowState::MatchSettle)
        {
            UE_LOG(LogTemp, Display, TEXT("M1_MATCH_OVER winner=P%d final=%d:%d"), MatchFlow.MatchWinner + 1,
                MatchFlow.Score[0], MatchFlow.Score[1]);
        }
    }
}
FString APrototypeBattleMode::Status() const
{
    if (!Ready) return Error;
    if (AutoMatches <= 0 && MatchFlow.State == EMatchFlowState::Lobby)
        return FString::Printf(TEXT("大厅 · %s · 按 SPACE 开始一局计分"), MatchFlow.ModeLabel());
    if (AutoMatches <= 0 && MatchFlow.State == EMatchFlowState::PickRegular)
        return FString::Printf(TEXT("PickRegular selected %d/%d"), MatchFlow.Pick.Count, MatchFlow.Pick.Required);
    if (AutoMatches <= 0 && MatchFlow.State == EMatchFlowState::BlindPick)
    {
        if (!MatchFlow.bBlindRevealed)
            return FString::Printf(TEXT("BlindPick secret P1=%d locked=%d (foe hidden) unused=%d"),
                MatchFlow.BlindChoiceP1, MatchFlow.bBlindLockedP1 ? 1 : 0, MatchFlow.CountUnused());
        return FString::Printf(TEXT("BlindPick REVEAL P1=%s vs P2=%s  SPACE confirm"),
            MatchFlow.Pick.Pool[MatchFlow.BlindChoiceP1].Id,
            MatchFlow.BlindChoiceP2 >= 0 ? MatchFlow.Pick.Pool[MatchFlow.BlindChoiceP2].Id : TEXT("?"));
    }
    if (AutoMatches <= 0 && MatchFlow.State == EMatchFlowState::Prep)
    {
        if (MatchFlow.bBlindPhase)
            return FString::Printf(TEXT("Prep/rope blind P1=%s vs P2=%s  SPACE launch"),
                MatchFlow.BlindChoiceP1 >= 0 ? MatchFlow.Pick.Pool[MatchFlow.BlindChoiceP1].Id : TEXT("?"),
                MatchFlow.BlindChoiceP2 >= 0 ? MatchFlow.Pick.Pool[MatchFlow.BlindChoiceP2].Id : TEXT("DEF"));
        return FString::Printf(TEXT("Prep/rope lineup %s -> %s -> %s bout#%d  SPACE launch"),
            MatchFlow.Pick.Pool[MatchFlow.Pick.Lineup[0]].Id,
            MatchFlow.Pick.Pool[MatchFlow.Pick.Lineup[1]].Id,
            MatchFlow.Pick.Pool[MatchFlow.Pick.Lineup[2]].Id,
            MatchFlow.CurrentLineupIndex + 1);
    }
    if (Simulation.Running) return FString::Printf(TEXT("Battle %d   %.1f / %.0f s   Hits: %d | P1 %s spin%.2f | P2 %s spin%.2f"), Match, Simulation.Frames * FBattleSimulation::Step, Simulation.FrameLimit*FBattleSimulation::Step, Simulation.Hits, Simulation.TypeLabel(0), Simulation.Spin[0], Simulation.TypeLabel(1), Simulation.Spin[1]);
    if (IsRingoutPresenting()) return FString::Printf(TEXT("Ringout landing... %.2f s"), FallTime);
    if (AutoMatches <= 0 && MatchFlow.State == EMatchFlowState::RoundSettle)
    {
        const FString Result = MatchFlow.LastWinner < 0 ? TEXT("平局") : FString::Printf(TEXT("P%d胜"), MatchFlow.LastWinner + 1);
        const FString Delta = MatchFlow.LastDelta.bDraw
            ? TEXT("各+1")
            : FString::Printf(TEXT("+%d"), MatchFlow.LastDelta.PointsToWinner);
        const FString TagPart = (MatchFlow.LastDelta.Tag == EScoreTag::None)
            ? FString()
            : FString::Printf(TEXT(" · %s"), ScoreTagLabel(MatchFlow.LastDelta.Tag));
        return FString::Printf(TEXT("第%d局结束 · %s · %s%s · %s · 比分 %d:%d（抢%d）"),
            MatchFlow.RoundIndex, *Result, FMatchFlow::ReasonLabelCN(MatchFlow.LastReason), *TagPart, *Delta,
            MatchFlow.Score[0], MatchFlow.Score[1], MatchFlow.Target());
    }
    if (AutoMatches <= 0 && MatchFlow.State == EMatchFlowState::MatchSettle)
    {
        return FString::Printf(TEXT("比赛结束 · P%d胜 · 最终 %d:%d（抢%d）"),
            MatchFlow.MatchWinner + 1, MatchFlow.Score[0], MatchFlow.Score[1], MatchFlow.Target());
    }
    if (Simulation.Reason.IsEmpty()) return TEXT("Ready - press SPACE to launch both tops");
    const FString Result = Simulation.Winner < 0 ? TEXT("DRAW") : FString::Printf(TEXT("P%d WINS"), Simulation.Winner + 1);
    if (Simulation.Reason == TEXT("timeout"))
    {
        // Show residual momenta so the player can see why the timeout winner was chosen.
        return FString::Printf(TEXT("%s | timeout (momentum %.3f vs %.3f) | %.2f s | %d hits"),
            *Result, Simulation.TimeoutMomentum[0], Simulation.TimeoutMomentum[1],
            Simulation.Frames * FBattleSimulation::Step, Simulation.Hits);
    }
    if (Simulation.Reason == TEXT("spinout"))
    {
        return FString::Printf(TEXT("%s | spinout | %.2f s | %d hits | P1 %s spin%.3f | P2 %s spin%.3f"),
            *Result, Simulation.Frames * FBattleSimulation::Step, Simulation.Hits,
            Simulation.TypeLabel(0), Simulation.Spin[0], Simulation.TypeLabel(1), Simulation.Spin[1]);
    }
    return FString::Printf(TEXT("%s | %s | %.2f s | %d hits"), *Result, *Simulation.Reason, Simulation.Frames * FBattleSimulation::Step, Simulation.Hits);
}

bool APrototypeBattleMode::SavePlayerSlot0()
{
	UBeybladePlayerSaveGame* Save = BeybladePlayerSave::LoadOrCreateSlot0();
	if (!Save) return false;
	Save->LastMode = BeybladePlayerSave::ModeToPersist(MatchFlow.Mode);
	const bool Ok = BeybladePlayerSave::SaveSlot0(Save);
	UE_LOG(LogTemp, Display, TEXT("SAVE_SLOT0 manual ok=%d last_mode=%s"), Ok ? 1 : 0, *Save->LastMode);
	return Ok;
}

bool APrototypeBattleMode::LoadPlayerSlot0()
{
	UBeybladePlayerSaveGame* Save = BeybladePlayerSave::LoadSlot0();
	if (!Save)
	{
		UE_LOG(LogTemp, Warning, TEXT("LOAD_SLOT0 missing"));
		return false;
	}
	ERaceMode Restored = ERaceMode::RaceTo5;
	if (BeybladePlayerSave::TryParseMode(Save->LastMode, Restored) && MatchFlow.State == EMatchFlowState::Lobby)
		MatchFlow.SetMode(Restored);
	UE_LOG(LogTemp, Display, TEXT("LOAD_SLOT0 ok version=%d last_mode=%s vol=%.2f lang=%s"),
		Save->SaveVersion, *Save->LastMode, Save->MasterVolume, *Save->Language);
	return true;
}


void APrototypeBattleMode::AdjustLaunch(int32 Angle,int32 Power)
{
    if(MatchFlow.State==EMatchFlowState::Prep && !bLaunching)LaunchSetup.Adjust(Angle,Power);
}
bool APrototypeBattleMode::HandleLaunchClick(const FVector2D& Point)
{
    if(bLaunching)return true;
    if(MatchFlow.State!=EMatchFlowState::Prep)return false;
    const int32 Hit=FLaunchSetup::Hit(Point);
    if(Hit<0)return false;
    AdjustLaunch(Hit==0?-5:Hit==1?5:0,Hit==2?-5:Hit==3?5:0);return true;
}
void APrototypeBattleMode::PlayLaunchSound(int32 Index)
{
    if(LaunchSounds.IsValidIndex(Index) && LaunchSounds[Index]) {UGameplayStatics::PlaySound2D(this,LaunchSounds[Index],ContactMasterVolume*.65f);UE_LOG(LogTemp,Display,TEXT("LAUNCH_AUDIO index=%d age=%.2f"),Index,LaunchAge);}
}
void APrototypeBattleMode::SetupLaunchHero()
{
    bAvatarSelection=MobileUX::Enabled() || FParse::Param(FCommandLine::Get(),TEXT("AvatarSelection"));
    bAIAvatars=bAvatarSelection || FParse::Param(FCommandLine::Get(),TEXT("AIAvatars"));
    if(bAIAvatars){SetupAIAvatars();if(bAvatarSelection)SelectAvatar(0);return;}

    for (int32 I = 0; I < 2; ++I)
        if (Beys.IsValidIndex(I) && Beys[I]) BeyBaseScale[I] = Beys[I]->GetActorScale3D();
    HeroOriginal = FaceCharacter ? FaceCharacter->FindComponentByClass<USkeletalMeshComponent>() : nullptr;
    if (!HeroOriginal)
    {
        UE_LOG(LogTemp, Error, TEXT("LAUNCH_HERO_MISSING_SKELETAL_MESH"));
        return;
    }
    HeroForward = FaceCharacter->GetActorForwardVector();
    HeroRight = FaceCharacter->GetActorRightVector();
    USkeletalMesh* OriginalMesh = HeroOriginal->GetSkeletalMeshAsset();
    UE_LOG(LogTemp, Display, TEXT("LAUNCH_HERO_ACTOR loc=%s scale=%.4f mesh=%s skeleton=%s"),
        *FaceCharacter->GetActorLocation().ToString(), FaceCharacter->GetActorScale3D().X,
        OriginalMesh ? *OriginalMesh->GetName() : TEXT("None"),
        OriginalMesh && OriginalMesh->GetSkeleton() ? *OriginalMesh->GetSkeleton()->GetName() : TEXT("None"));

    USkeletalMesh* RefinedIdle = LoadObject<USkeletalMesh>(nullptr, TEXT("/Game/FeelLab/Characters/PortraitRefinedV3/Male/SK_MaleIdleLit.SK_MaleIdleLit"));
    if (!OriginalMesh || !RefinedIdle || !RefinedIdle->GetSkeleton())
    { UE_LOG(LogTemp, Error, TEXT("REFINED_IDLE_MISSING_ASSET")); return; }
    // Preserve the industrial character's height; its previous skeleton uses different units.
    const double TargetHeight = 2. * OriginalMesh->GetBounds().BoxExtent.Z * HeroOriginal->GetComponentScale().Z;
    for (const TCHAR* Name : {TEXT("standing_relax"), TEXT("walk"), TEXT("run"), TEXT("jump"),
        TEXT("agree"), TEXT("defeat_02"), TEXT("fold_arms"), TEXT("turn")})
    {
        const FString Path = FString::Printf(TEXT("/Game/FeelLab/Characters/MaleLauncher_v1/SK_MaleLauncher_Anim_%s_001.SK_MaleLauncher_Anim_%s_001"), Name, Name);
        auto* Clip = LoadObject<UAnimSequence>(nullptr, *Path);
        if (!Clip || Clip->GetSkeleton() != RefinedIdle->GetSkeleton())
        { UE_LOG(LogTemp, Error, TEXT("REFINED_IDLE_INCOMPATIBLE_CLIP %s"), Name); return; }
        HeroAnimations.Add(Clip);
    }
    // Import authored normals: recomputing on this small-unit mesh darkens the dense face geometry.
    HeroOriginal->SetSkeletalMesh(RefinedIdle);
    HeroOriginal->EmptyOverrideMaterials();
    HeroOriginal->SetWorldScale3D(FVector(TargetHeight / (2. * RefinedIdle->GetBounds().BoxExtent.Z)));
    HeroOriginal->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    HeroOriginal->PlayAnimation(HeroAnimations[0], true);
    HeroOriginal->TickAnimation(0.f, false); HeroOriginal->RefreshBoneTransforms();

    USkeletalMesh* LaunchMesh = LoadObject<USkeletalMesh>(nullptr, TEXT("/Game/FeelLab/Characters/PortraitRefinedV3/Male/SK_MaleLaunch.SK_MaleLaunch"));
    HeroLaunchAnimation = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/FeelLab/Characters/PortraitRefinedV3/Male/A_Launch.A_Launch"));
    const bool bSocket = LaunchMesh && LaunchMesh->GetRefSkeleton().FindBoneIndex(TEXT("LaunchSocket")) >= 0;
    if (!LaunchMesh || !HeroLaunchAnimation || !bSocket)
    {
        UE_LOG(LogTemp, Error, TEXT("LAUNCH_APPROVED_ASSET_MISSING mesh=%d anim=%d socket=%d"),
            LaunchMesh ? 1 : 0, HeroLaunchAnimation ? 1 : 0, bSocket ? 1 : 0);
        return;
    }
    HeroPose = NewObject<USkeletalMeshComponent>(FaceCharacter);
    HeroPose->SetupAttachment(HeroOriginal);
    HeroPose->SetSkeletalMesh(LaunchMesh);
    HeroPose->SetRelativeRotation(FRotator(0, -90, 0));
    // Same call order as the approved build: world scale before registration.
    const double CharacterScale = TargetHeight / (2. * LaunchMesh->GetBounds().BoxExtent.Z);
    HeroPose->SetWorldScale3D(FVector(CharacterScale));
    HeroPose->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    HeroPose->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    HeroPose->RegisterComponent();
    HeroPose->PlayAnimation(HeroLaunchAnimation, false);
    HeroPose->SetPlayRate(0.f);
    HeroPose->SetPosition(0.f, false);
    HeroPose->SetVisibility(false);
    FaceCharacter->SetActorHiddenInGame(false);
    bLaunchHeroReady = true;
    UE_LOG(LogTemp, Display, TEXT("LAUNCH_HERO_READY bones=%d duration=%.3f"), HeroPose->GetNumBones(), HeroLaunchAnimation->GetPlayLength());
    // Numeric pose check: standing reads z-extent ~106, prone collapses below ~40.
    const FBoxSphereBounds HBounds = HeroOriginal->Bounds;
    UE_LOG(LogTemp, Display, TEXT("LAUNCH_HERO_POSE z=%.1f extent=(%.1f,%.1f,%.1f)"),
        HBounds.BoxExtent.Z, HBounds.BoxExtent.X, HBounds.BoxExtent.Y, HBounds.BoxExtent.Z);

    USkeletalMesh* FemaleMesh = LoadObject<USkeletalMesh>(nullptr, TEXT("/Game/FeelLab/Characters/PortraitRefinedV3/Female/SK_FemaleLaunch.SK_FemaleLaunch"));
    FemaleLaunchAnimation = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/FeelLab/Characters/PortraitRefinedV3/Female/A_Launch.A_Launch"));
    if (FemaleMesh && FemaleLaunchAnimation && FemaleMesh->GetRefSkeleton().FindBoneIndex(TEXT("LaunchSocket")) >= 0)
    {
        // Industrial map is centred on the bowl: mirror the measured male position instead of copying the old map.
        const FVector MaleLocation = FaceCharacter->GetActorLocation();
        FVector Opposite(-MaleLocation.X, -MaleLocation.Y, MaleLocation.Z);
        // Opposite floor height is not guaranteed to match the male's spot: trace it instead of copying Z.
        FHitResult GroundHit;
        FCollisionQueryParams GroundParams(SCENE_QUERY_STAT(LaunchFemaleGround), true, FaceCharacter);
        if (GetWorld()->LineTraceSingleByChannel(GroundHit, Opposite + FVector(0, 0, 500), Opposite - FVector(0, 0, 500), ECC_Visibility, GroundParams))
        {
            Opposite.Z = GroundHit.ImpactPoint.Z + 1.0;
        }
        FActorSpawnParameters Params;
        Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        AActor* Female = GetWorld()->SpawnActor<AActor>(AActor::StaticClass(), Opposite,
            FRotator(0, FaceCharacter->GetActorRotation().Yaw + 90., 0), Params);
        if (Female)
        {
            Female->Tags.Add(TEXT("OpponentCharacter"));
            FemaleActor = Female;
            USceneComponent* Root = NewObject<USceneComponent>(Female, TEXT("FemaleRoot"));
            Female->SetRootComponent(Root);
            Root->RegisterComponent();
            Female->SetActorLocationAndRotation(Opposite, FRotator(0, FaceCharacter->GetActorRotation().Yaw + 90., 0));
            FemalePose = NewObject<USkeletalMeshComponent>(Female, TEXT("FemaleMesh"));
            FemalePose->SetupAttachment(Root);
            FemalePose->SetSkeletalMesh(FemaleMesh);
            FemalePose->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            FemalePose->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
            FemalePose->RegisterComponent();
            FemalePose->SetWorldScale3D(FVector(CharacterScale));
            FemalePose->SetVisibility(true, true);
            FemalePose->PlayAnimation(FemaleLaunchAnimation, false);
            FemalePose->SetPlayRate(0.f);
            FemalePose->SetPosition(0.f, false);
            FemalePose->TickAnimation(0.f, false);
            FemalePose->RefreshBoneTransforms();
            UE_LOG(LogTemp, Display, TEXT("FEMALE_LAUNCH_READY loc=%s yaw=%.1f bones=%d duration=%.3f"),
                *Opposite.ToString(), FaceCharacter->GetActorRotation().Yaw + 90., FemalePose->GetNumBones(), FemaleLaunchAnimation->GetPlayLength());
        }
    }
    else UE_LOG(LogTemp, Error, TEXT("FEMALE_LAUNCH_MISSING_ASSET"));
}
void APrototypeBattleMode::PoseLaunchHero()
{
    if (!HeroPose) return;
    const double HeroTime = bAvatarSelection && SelectedAvatar==3 ? LaunchAge * (75. / 87.) : LaunchAge;
    HeroPose->SetPosition(float(FMath::Min(HeroTime, LabLaunch::Duration)), false);
    HeroPose->TickAnimation(0.f, false);
    HeroPose->RefreshBoneTransforms();
    if (LaunchAge <= LabLaunch::Release) LaunchHands[0] = HeroPose->GetSocketLocation(TEXT("LaunchSocket"));
    if (FemalePose)
    {
        const double FemaleTime = !bAvatarSelection && FParse::Param(FCommandLine::Get(),TEXT("DeepSeekDoubao")) ? LaunchAge * (75. / 87.) : LaunchAge;
        FemalePose->SetPosition(float(FMath::Min(FemaleTime, LabLaunch::Duration)), false);
        FemalePose->TickAnimation(0.f, false);
        FemalePose->RefreshBoneTransforms();
        if (LaunchAge <= LabLaunch::Release) LaunchHands[1] = FemalePose->GetSocketLocation(TEXT("LaunchSocket"));
    }
}
void APrototypeBattleMode::BeginLaunchPresentation()
{
    if (bLaunching) return;
    if (!bLaunchHeroReady || !HeroPose || !HeroLaunchAnimation)
    {
        // Assets missing: keep the industrial state machine intact instead of stalling in Prep.
        if (!MatchFlow.TryLaunchFromPrep()) return;
        StartBattleInternal();
        UE_LOG(LogTemp, Warning, TEXT("LAUNCH_FALLBACK_NO_HERO"));
        return;
    }
    ApplyBeyArt();
    for (int32 I = 0; I < 2; ++I)
    {
        if (Beys.IsValidIndex(I) && Beys[I]) BeyBaseScale[I] = Beys[I]->GetActorScale3D();
        BeyArtBaseScale[I] = BeyArt.IsValidIndex(I) && BeyArt[I] ? BeyArt[I]->GetComponentScale() : FVector::OneVector;
    }
    FaceCharacter->SetActorHiddenInGame(false);
    if (FemaleActor) FemaleActor->SetActorHiddenInGame(false);
    HeroOriginal->SetVisibility(false, false);
    HeroPose->SetVisibility(true);
    bLaunching = true; LaunchAge = 0.; LaunchBeat = -1;
    for (AActor* Bey : Beys) if (Bey) Bey->SetActorHiddenInGame(false);
    PoseLaunchHero();
    ApplyTransforms();
    UE_LOG(LogTemp, Display, TEXT("LAUNCH_BEGIN angle=%d power=%d"), LaunchSetup.Angle, LaunchSetup.Power);
}
void APrototypeBattleMode::TickLaunchPresentation(float DeltaSeconds)
{
    if (!bLaunching) return;
    const double Before = LaunchAge;
    LaunchAge += FMath::Clamp(DeltaSeconds, 0.f, .1f);
    if (Before < LabLaunch::Release && LaunchAge >= LabLaunch::Release)
    {
        // Evaluate the exact release frame so the flight start does not drift with frame rate.
        const double Now = LaunchAge; LaunchAge = LabLaunch::Release; PoseLaunchHero(); LaunchAge = Now;
    }
    PoseLaunchHero();
    const int32 Beat = LaunchAge < 1.6 ? -1 : FMath::FloorToInt((LaunchAge - 1.6) / (1.3 / 3.));
    if (Beat < 3 && Beat != LaunchBeat) { LaunchBeat = Beat; PlayLaunchSound(0); }
    if (!bAIAvatars && Before < 2.6333333333 && LaunchAge >= 2.6333333333) PlayLaunchSound(1);
    if (Before < LabLaunch::Release && LaunchAge >= LabLaunch::Release)
    {
        UE_LOG(LogTemp, Display, TEXT("APPROVED_LAUNCH_RELEASE socket=%s female=%s"),
            *LaunchHands[0].ToString(), *LaunchHands[1].ToString());

        if (!MatchFlow.TryLaunchFromPrep()) { EndLaunchPresentation(); return; }
        StartBattleInternal();
        PlayLaunchSound(2);
        for (AActor* B : Beys) if (B) B->SetActorHiddenInGame(false);
    }
    if (BattleView && FemaleActor)
    {
        const FVector Mid = (FaceCharacter->GetActorLocation() + FemaleActor->GetActorLocation()) * .5;
        const double Span = FVector::Distance(FaceCharacter->GetActorLocation(), FemaleActor->GetActorLocation());
        const FVector View = Mid + HeroRight * FMath::Max(850., Span * 1.45) + FVector(0, 0, 500);
        BattleView->SetActorLocationAndRotation(View, (Mid + FVector(0, 0, 110) - View).Rotation());
        BattleView->GetCameraComponent()->SetFieldOfView(55.f);
    }
    if (LaunchAge >= LabLaunch::Duration)
    {
        EndLaunchPresentation();
        if (ContactSounds.Num() > 0 && ContactSounds[0]) UGameplayStatics::PlaySound2D(this, ContactSounds[0], ContactMasterVolume * .4f, 1.25f);
        UE_LOG(LogTemp, Display, TEXT("APPROVED_LAUNCH_LANDED simulation_frame=%d"), Simulation.Frames);
    }
}
void APrototypeBattleMode::EndLaunchPresentation()
{
    bLaunching = false; Accumulator = 0.;
    if (HeroPose) HeroPose->SetVisibility(false);
    if (FemalePose)
    {
        FemalePose->SetPosition(0.f, false);
        FemalePose->TickAnimation(0.f, false);
        FemalePose->RefreshBoneTransforms();
    }
    if (HeroOriginal)
    {
        HeroOriginal->SetVisibility(true, false);
        if (HeroAnimations.Num() > 0) HeroOriginal->PlayAnimation(HeroAnimations[0], true);
        if (bAvatarSelection) { HeroOriginal->SetPlayRate(0); HeroOriginal->SetPosition(0,false); }
    }
    for (int32 I = 0; I < 2; ++I)
    {
        if (!Beys.IsValidIndex(I) || !Beys[I]) continue;
        Beys[I]->SetActorHiddenInGame(false);
        Beys[I]->SetActorScale3D(BeyBaseScale[I]);
        if (BeyArt.IsValidIndex(I) && BeyArt[I]) BeyArt[I]->SetWorldScale3D(BeyArtBaseScale[I]);
    }
}

void APrototypeBattleMode::EnterArena()
{
    if (IsArenaExploring()) { Launch(); return; }
    if (MatchFlow.State == EMatchFlowState::Lobby)
        UGameplayStatics::OpenLevel(this, bAvatarSelection ? TEXT("/Game/Maps/RankedArena_AccentPreview") : TEXT("/Game/Maps/RankedArena_v1"));
}
void APrototypeBattleMode::UpdateArenaExploration()
{
    if (!ArenaWalker) return;
    const bool Exploring = IsArenaExploring();
    ArenaWalker->SetActorHiddenInGame(!Exploring);
    ArenaWalker->SetActorEnableCollision(Exploring);
    if (Exploring != bWasExploring)
    {
        auto* PC = UGameplayStatics::GetPlayerController(this, 0);
        if (PC)
        {
            if (MobileUX::Enabled()) PC->SetVirtualJoystickVisibility(Exploring);
            if (Exploring)
            {
                PC->Possess(ArenaWalker); PC->SetControlRotation(FRotator(-15, -90, 0)); PC->SetViewTarget(ArenaWalker);
            }
            else
            {
                ArenaWalker->GetCharacterMovement()->StopMovementImmediately();
                PC->UnPossess(); if (BattleView) PC->SetViewTarget(BattleView);
            }
        }
        UE_LOG(LogTemp, Display, TEXT("ARENA_EXPLORE enabled=%d"), Exploring);
        bWasExploring = Exploring;
    }
    if (Exploring) MatchFlow.SetMode(ERaceMode::RaceTo8);
}


void APrototypeBattleMode::SetupAIAvatars()
{
    HeroOriginal=FaceCharacter?FaceCharacter->FindComponentByClass<USkeletalMeshComponent>():nullptr;
    if(!ensure(HeroOriginal))return;
    for(int32 I=0;I<2;++I)if(Beys.IsValidIndex(I)&&Beys[I])BeyBaseScale[I]=Beys[I]->GetActorScale3D();
    HeroForward=FaceCharacter->GetActorForwardVector();HeroRight=FaceCharacter->GetActorRightVector();
    const bool bNewAvatars=FParse::Param(FCommandLine::Get(),TEXT("DeepSeekDoubao")) && !bAvatarSelection;
    auto* GPT=LoadObject<USkeletalMesh>(nullptr,bNewAvatars?TEXT("/Game/FeelLab/Characters/AIAvatars/DeepSeek/SK_DeepSeek"):TEXT("/Game/FeelLab/Characters/AIAvatars/GPT/SK_GPT"));
    auto* Grok=LoadObject<USkeletalMesh>(nullptr,bNewAvatars?TEXT("/Game/FeelLab/Characters/AIAvatars/Doubao/SK_Doubao"):TEXT("/Game/FeelLab/Characters/AIAvatars/GROK/SK_GROK"));
    auto* Idle=LoadObject<UAnimSequence>(nullptr,bNewAvatars?TEXT("/Game/FeelLab/Characters/AIAvatars/DeepSeek/A_LaunchScaled"):TEXT("/Game/FeelLab/Characters/AIAvatars/GPT/A_Idle"));
    HeroLaunchAnimation=LoadObject<UAnimSequence>(nullptr,bNewAvatars?TEXT("/Game/FeelLab/Characters/AIAvatars/DeepSeek/A_LaunchScaled"):TEXT("/Game/FeelLab/Characters/AIAvatars/GPT/A_LaunchR"));
    FemaleLaunchAnimation=LoadObject<UAnimSequence>(nullptr,bNewAvatars?TEXT("/Game/FeelLab/Characters/AIAvatars/Doubao/A_LaunchScaled"):TEXT("/Game/FeelLab/Characters/AIAvatars/GROK/A_LaunchL"));
    if(!ensure(GPT&&Grok&&Idle&&HeroLaunchAnimation&&FemaleLaunchAnimation))return;
    HeroAnimations.Empty();HeroAnimations.Add(Idle);
    const double Scale=180./(2*GPT->GetBounds().BoxExtent.Z);
    HeroOriginal->SetSkeletalMesh(GPT);HeroOriginal->EmptyOverrideMaterials();
    HeroOriginal->SetWorldScale3D(FVector(Scale));HeroOriginal->SetWorldRotation(HeroForward.Rotation()+FRotator(0,-90,0));
    HeroOriginal->PlayAnimation(Idle,true);
    if(bNewAvatars){HeroOriginal->SetPlayRate(0);HeroOriginal->SetPosition(0,false);}
    HeroPose=NewObject<USkeletalMeshComponent>(FaceCharacter);HeroPose->SetupAttachment(HeroOriginal);
    HeroPose->SetSkeletalMesh(GPT);HeroPose->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    HeroPose->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    HeroPose->RegisterComponent();HeroPose->PlayAnimation(HeroLaunchAnimation,false);HeroPose->SetPlayRate(0);HeroPose->SetPosition(0,false);HeroPose->SetVisibility(false);
    FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    FVector Opposite=-FaceCharacter->GetActorLocation();Opposite.Z=FaceCharacter->GetActorLocation().Z;
    FemaleActor=GetWorld()->SpawnActor<AActor>(AActor::StaticClass(),Opposite,(-HeroForward).Rotation(),Params);
    if(!ensure(FemaleActor))return;
    auto* Root=NewObject<USceneComponent>(FemaleActor);FemaleActor->SetRootComponent(Root);Root->RegisterComponent();
    FemaleActor->SetActorLocationAndRotation(Opposite,(-HeroForward).Rotation()+FRotator(0,-90,0));FemaleActor->Tags.Add(TEXT("OpponentCharacter"));
    FemalePose=NewObject<USkeletalMeshComponent>(FemaleActor);FemalePose->SetupAttachment(Root);FemalePose->SetSkeletalMesh(Grok);
    FemalePose->SetCollisionEnabled(ECollisionEnabled::NoCollision);FemalePose->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    FemalePose->RegisterComponent();FemalePose->SetWorldScale3D(FVector(180./(2*Grok->GetBounds().BoxExtent.Z)));
    FemalePose->PlayAnimation(FemaleLaunchAnimation,false);FemalePose->SetPlayRate(0);FemalePose->SetPosition(0,false);
    bLaunchHeroReady=true;
    UE_LOG(LogTemp,Display,TEXT("AI_AVATARS_READY GPT=%s GROK=%s release=%.3f"),*GPT->GetName(),*Grok->GetName(),LabLaunch::Release);
}


void APrototypeBattleMode::SelectAvatar(int32 Index)
{
    if(!bAvatarSelection || Index<0 || Index>=6 || !HeroOriginal || !HeroPose || !FemalePose || MatchFlow.State!=EMatchFlowState::Lobby) return;
    const TCHAR* MeshPaths[]={
        TEXT("/Game/FeelLab/Characters/AIAvatars/GPT/SK_GPT"),
        TEXT("/Game/FeelLab/Characters/AIAvatars/GROK/SK_GROK"),
        TEXT("/Game/FeelLab/Characters/AIAvatars/DeepSeek/SK_DeepSeek"),
        TEXT("/Game/FeelLab/Characters/AIAvatars/Doubao/SK_Doubao"),
        TEXT("/Game/FeelLab/Characters/PortraitRefinedV3/Male/SK_MaleLaunch"),
        TEXT("/Game/FeelLab/Characters/PortraitRefinedV3/Female/SK_FemaleLaunch")};
    const TCHAR* AnimationPaths[]={
        TEXT("/Game/FeelLab/Characters/AIAvatars/GPT/A_LaunchR"),
        TEXT("/Game/FeelLab/Characters/AIAvatars/GROK/A_LaunchL"),
        TEXT("/Game/FeelLab/Characters/AIAvatars/DeepSeek/A_LaunchScaled"),
        TEXT("/Game/FeelLab/Characters/AIAvatars/Doubao/A_LaunchScaled"),
        TEXT("/Game/FeelLab/Characters/PortraitRefinedV3/Male/A_Launch"),
        TEXT("/Game/FeelLab/Characters/PortraitRefinedV3/Female/A_Launch")};
    const int32 Opponent = Index == 5 ? 4 : 5;
    auto* Mesh=LoadObject<USkeletalMesh>(nullptr,MeshPaths[Index]);
    auto* Anim=LoadObject<UAnimSequence>(nullptr,AnimationPaths[Index]);
    auto* OppMesh=LoadObject<USkeletalMesh>(nullptr,MeshPaths[Opponent]);
    auto* OppAnim=LoadObject<UAnimSequence>(nullptr,AnimationPaths[Opponent]);
    if(!Mesh || !Anim || !OppMesh || !OppAnim || Anim->GetSkeleton()!=Mesh->GetSkeleton() || OppAnim->GetSkeleton()!=OppMesh->GetSkeleton() || Mesh->GetRefSkeleton().FindBoneIndex(TEXT("LaunchSocket"))<0 || OppMesh->GetRefSkeleton().FindBoneIndex(TEXT("LaunchSocket"))<0)
    { UE_LOG(LogTemp,Error,TEXT("AVATAR_SELECTION_ASSET_INVALID index=%d"),Index); return; }
    SelectedAvatar=Index;
    HeroLaunchAnimation=Anim; FemaleLaunchAnimation=OppAnim;
    HeroAnimations.Empty(); HeroAnimations.Add(Anim);
    HeroOriginal->SetSkeletalMesh(Mesh); HeroOriginal->EmptyOverrideMaterials();
    HeroOriginal->SetWorldScale3D(FVector(180./(2*Mesh->GetBounds().BoxExtent.Z)));
    HeroOriginal->PlayAnimation(Anim,false); HeroOriginal->SetPlayRate(0); HeroOriginal->SetPosition(0,false);
    HeroPose->SetSkeletalMesh(Mesh); HeroPose->EmptyOverrideMaterials(); HeroPose->SetWorldScale3D(HeroOriginal->GetComponentScale());
    HeroPose->PlayAnimation(Anim,false); HeroPose->SetPlayRate(0); HeroPose->SetPosition(0,false);
    FemalePose->SetSkeletalMesh(OppMesh); FemalePose->EmptyOverrideMaterials(); FemalePose->SetWorldScale3D(FVector(180./(2*OppMesh->GetBounds().BoxExtent.Z)));
    FemalePose->PlayAnimation(OppAnim,false); FemalePose->SetPlayRate(0); FemalePose->SetPosition(0,false);
    if(ArenaWalker) ArenaWalker->PreviewAvatar(Mesh,Anim);
    UE_LOG(LogTemp,Display,TEXT("AVATAR_SELECTED index=%d mesh=%s opponent=%s"),Index,*Mesh->GetName(),*OppMesh->GetName());
}
