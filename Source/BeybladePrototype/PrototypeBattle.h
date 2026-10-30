#pragma once
#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/HUD.h"
#include "GameFramework/PlayerController.h"
#include "BattleSimulation.h"
#include "MatchFlow.h"
#include "LobbyClickUI.h"
#include "SkillRuntime.h"
#include "CollectionCatalog.h"
#include "IndustrialFeelSettings.h"
#include "BoutPresentation.h"
#include "BeyTrailHistory.h"
#include "PrototypeBattle.generated.h"

class UInputAction;
class UInputMappingContext;
class UStaticMeshComponent;
class UTexture2D;

UCLASS()
class BEYBLADEPROTOTYPE_API APrototypeBattleController : public APlayerController
{
    GENERATED_BODY()
public:
    virtual void SetupInputComponent() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    virtual void PlayerTick(float DeltaTime) override;
private:
    UPROPERTY() TObjectPtr<UInputAction> LaunchAction;
    UPROPERTY() TObjectPtr<UInputAction> ResetAction;
    UPROPERTY() TObjectPtr<UInputAction> SkillAction;
    UPROPERTY() TObjectPtr<UInputAction> ArenaAction;
    UPROPERTY() TObjectPtr<UInputAction> ModeRace5Action;
    UPROPERTY() TObjectPtr<UInputAction> ModeRace8Action;
    UPROPERTY() TObjectPtr<UInputAction> ToggleModeAction;
    UPROPERTY() TObjectPtr<UInputAction> ClickAction;
    UPROPERTY() TObjectPtr<UInputAction> Pick3Action;
    UPROPERTY() TObjectPtr<UInputAction> Pick4Action;
    UPROPERTY() TObjectPtr<UInputAction> Pick5Action;
    UPROPERTY() TArray<TObjectPtr<UInputAction>> ExtraPickActions;
    UPROPERTY() TObjectPtr<UInputMappingContext> Mapping;
    void Launch();
    void ResetMatch();
    void FireSkill();
    void EnterArena();
    void SelectRace5();
    void SelectRace8();
    void ToggleMode();
    void OnLobbyClick();
    void OnTouchPressed(ETouchIndex::Type Finger,FVector Location);
    void DispatchScreenPoint(const FVector2D& Point);
    double LastTouchTime=-1.;
    void PickSlot0(); void PickSlot1(); void PickSlot2(); void PickSlot3(); void PickSlot4(); void PickSlot5(); void PickSlot6(); void PickSlot7();
};

UCLASS()
class BEYBLADEPROTOTYPE_API APrototypeBattleHUD : public AHUD
{
    GENERATED_BODY()
public:
    virtual void DrawHUD() override;
private:
    UPROPERTY() TMap<FName, TObjectPtr<UTexture2D>> UIArt;
    UPROPERTY() TObjectPtr<class UFont> RuntimeFont;
    UTexture2D* Art(const TCHAR* Name);
    void DrawGameHUD();
    void DrawTuningPanel();
    void DrawMobileControls();
};

UCLASS()
class BEYBLADEPROTOTYPE_API APrototypeBattleMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    enum { RankedBoutSeconds=90, TutorialSeconds=35 };
    APrototypeBattleMode();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    UFUNCTION(BlueprintCallable) void EnterArena();
    bool IsArenaExploring() const { return bRankedArena && MatchFlow.State == EMatchFlowState::Lobby; }
    bool IsRankedArena() const { return bRankedArena; }
    int32 GetSelectedAvatar() const { return SelectedAvatar; }
    bool HasAvatarSelection() const { return bAvatarSelection; }
    void SelectAvatar(int32 Index);
    void ToggleTuning() {bTuningOpen=!bTuningOpen;}
    bool IsTuningOpen() const {return bTuningOpen;}
    int32 GetMoveLevel() const {return FeelSettings.Move;}
    int32 GetRingoutLevel() const {return FeelSettings.Ringout;}
    bool HandleTuningClick(const FVector2D& Mouse);
    void AdjustTuning(int32 MoveDelta,int32 RingoutDelta);
    void Launch();
    void ResetMatch();
    void SelectRaceMode(ERaceMode Mode);
    void ToggleRaceMode();
    void TogglePickSlot(int32 PoolIndex);
    void ConfirmPick();
    void LockBlind();
    void ConfirmBlind();
    void ContinueFromRoundSettle();
    void RematchFromMatchSettle();
    UFUNCTION(BlueprintCallable) void OpenCollection();
    UFUNCTION(BlueprintCallable) void CloseCollection();
    UFUNCTION(BlueprintCallable) void SelectCollectionSlot(int32 Index);
    UFUNCTION(BlueprintCallable) void FireActiveSkill();
    const FActiveSkillShell& GetSkillShell() const { return SkillShell; }
    void ApplyCurrentLoadouts();
    const FLaunchSetup& GetLaunchSetup() const {return LaunchSetup;}
    void AdjustLaunch(int32 Angle,int32 Power);
    bool HandleLaunchClick(const FVector2D& Point);
    bool IsLaunching() const {return bLaunching;}
    double GetLaunchAge() const {return LaunchAge;}
    int32 GetSkillUses() const {return SkillUses;}
    bool IsTutorialPending() const {return bTutorialPending;}
    bool IsTutorialBout() const {return bTutorialBout;}
    double GetLastImpactTime() const {return LastImpactTime;}
    double GetImpactDamage(int32 I) const {return ImpactDamage[FMath::Clamp(I,0,1)];}
	/** Class-3 skeleton: persist/load slot 0 (Meta/Progress/Settings). */
	bool SavePlayerSlot0();
	bool LoadPlayerSlot0();
    FString Status() const;
    const FString& GetBattleError() const { return Error; }
    const FBattleSimulation& GetSimulation() const { return Simulation; }
    const FMatchFlow& GetMatchFlow() const { return MatchFlow; }
    bool IsRingoutPresenting() const;
    bool IsAutomationBypass() const { return AutoMatches > 0; }
    UFUNCTION(BlueprintCallable) void ToggleFaceView();
    UFUNCTION(BlueprintCallable) void AdjustFaceView(float PitchDelta, float HeightDelta);
    UFUNCTION(BlueprintCallable) void LockFaceView();
    bool IsFaceView() const { return bFaceView; }
    bool IsFaceViewLocked() const { return bFaceLocked; }
    float GetFacePitch() const { return FacePitch; }
    float GetFaceHeight() const { return FaceHeight; }
    const TArray<FVector>& GetTrail(int32 Index) const {return TrailHistory.Points[FMath::Clamp(Index,0,1)];}
    FVector GetBeyLocation(int32 Index) const { return Beys.IsValidIndex(Index) && Beys[Index] ? Beys[Index]->GetActorLocation() : FVector::ZeroVector; }
private:
    UPROPERTY() TArray<TObjectPtr<class USoundBase>> ContactSounds;
    UPROPERTY() TObjectPtr<class USoundBase> ScrapeSound;
    UPROPERTY() TObjectPtr<class UIronWallEffectComponent> IronWallFx;
    UPROPERTY() TObjectPtr<class UChifengEffectComponent> ChifengFx;
    UPROPERTY() TObjectPtr<class UChangxuanEffectComponent> ChangxuanFx;
    UPROPERTY() TObjectPtr<class UHengrenEffectComponent> HengrenFx;
    UPROPERTY() TObjectPtr<class UChiwenEffectComponent> ChiwenFx;
    UPROPERTY() TObjectPtr<class UIronWallEffectComponent> GoldFx;
    UPROPERTY() TObjectPtr<class UChangxuanEffectComponent> StoneFx;
    UPROPERTY() TObjectPtr<class UHengrenEffectComponent> FrostFx;
    UPROPERTY() TArray<TObjectPtr<class USoundBase>> LaunchSounds;
    UPROPERTY() TArray<TObjectPtr<class USoundBase>> FeedbackSounds;
    UPROPERTY() TObjectPtr<class UAnimSequence> HeroLaunchAnimation;
    UPROPERTY() TObjectPtr<class UAnimSequence> FemaleLaunchAnimation;
    UPROPERTY() TArray<TObjectPtr<class UAnimSequence>> HeroAnimations;
    UPROPERTY() TObjectPtr<class USkeletalMeshComponent> HeroOriginal;
    UPROPERTY() TObjectPtr<class USkeletalMeshComponent> HeroPose;
    UPROPERTY() TObjectPtr<class USkeletalMeshComponent> FemalePose;
    UPROPERTY() TObjectPtr<AActor> FemaleActor;
    FVector LaunchHands[2] = {FVector::ZeroVector, FVector::ZeroVector};
    FVector BeyBaseScale[2] = {FVector::OneVector, FVector::OneVector};
    FVector BeyArtBaseScale[2] = {FVector::OneVector, FVector::OneVector};
    FVector HeroForward = FVector::ForwardVector;
    FVector HeroRight = FVector::RightVector;
    bool bLaunchHeroReady = false;
    FLaunchSetup LaunchSetup;
    bool bLaunching=false;
    double LaunchAge=0.;
    int32 LaunchBeat=-1,SkillUses=0;
    UPROPERTY() TArray<TObjectPtr<class UStaticMeshComponent>> ArenaScoreDisplays;
    UPROPERTY() TArray<TObjectPtr<class UStaticMesh>> ArenaScoreDigits;
    int32 ArenaDisplayedScores[2] = {-1, -1};
    bool bRankedArena = false;
    bool bWasExploring = false;
    UPROPERTY() TObjectPtr<class AArenaWalker> ArenaWalker;
    void UpdateArenaExploration();
    void SetupLaunchHero();
    void SetupAIAvatars();
    bool bAIAvatars=false;
    bool bAvatarSelection=false;
    bool bTutorialPending=false, bTutorialBout=false;
    int32 SelectedAvatar=0;
    void BeginLaunchPresentation();
    void TickLaunchPresentation(float DeltaSeconds);
    void PoseLaunchHero();
    void EndLaunchPresentation();
    void PlayLaunchSound(int32 Index);

    double LastScrapeTime=-1.,LastImpactTime=-1.,LastImpactStrength=0.;
    double ImpactDamage[2]={0.,0.};
    FBeyTrailHistory TrailHistory;
    double RenderYaw[2]={0.,0.};
    FVector2D VisualTilt[2];
    FIndustrialFeelSettings FeelSettings;
    bool bTuningOpen=false;
    float ContactMasterVolume = 1.f;
    double LastContactAudioTime = -1.;
    UPROPERTY() TObjectPtr<AActor> FaceBackdrop;
    UPROPERTY() TObjectPtr<AActor> FaceCharacter;
    UPROPERTY() TArray<TObjectPtr<class UStaticMesh>> ImportedBeys;
    UPROPERTY() TArray<TObjectPtr<UStaticMeshComponent>> BeyArt;
    FVector FaceAnchor;
    float FacePitch = -18.f, FaceHeight = 0.f;
    bool bFaceView = false, bFaceLocked = false;
    void ApplyBeyArt();
    UPROPERTY() TObjectPtr<class ACameraActor> BattleView;
    FVector PreparationViewLocation;
    FRotator PreparationViewRotation;
    float PreparationFOV = 56.f;
    UPROPERTY() TArray<TObjectPtr<AActor>> Beys;
    UPROPERTY() TObjectPtr<UStaticMeshComponent> Bowl;
    UPROPERTY() TObjectPtr<UStaticMeshComponent> Ground;
    FBattleSimulation Simulation;
    FMatchFlow MatchFlow;
    FActiveSkillShell SkillShell;
    FActiveSkillShell OpponentSkill;
    double Accumulator = 0;
    double FallTime = 0;
    double FallDuration = 0;
    FVector FallStart[2];
    bool Falling[2] = {false, false};
    bool WinnerPresentHold = false;
    FVector2D WinnerPresentPos = FVector2D::ZeroVector;
    int32 Seed = 0, Match = 0, AutoMatches = 0;
    bool Ready = false;
    FString Error, LogPath;
    void ApplyTransforms();
    void FinishMatch();
    bool SampleHeight(const FVector2D& Position, double& Height) const;
    bool SweepBowlObstacle(const FVector2D& Start,const FVector2D& End,FVector2D& Position,FVector2D& Normal) const;
    void CheckSurfaceBoundary();
    double GroundFloorZ() const;
    void StartBattleInternal();
};

