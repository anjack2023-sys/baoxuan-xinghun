#pragma once
#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "PlayerSaveGame.generated.h"

/**
 * Class-3 player/runtime data skeleton (slot 0).
 * Spec: docs/数据分离三类-规格-2026-10-26.md
 * Does NOT store Feel85 / balance tunables — those stay in docs/balance + freeze.
 */
UCLASS()
class BEYBLADEPROTOTYPE_API UBeybladePlayerSaveGame : public USaveGame
{
	GENERATED_BODY()
public:
	// ---- Save_Meta ----
	UPROPERTY(VisibleAnywhere, Category = "Save_Meta")
	int32 SaveVersion = 1;

	UPROPERTY(VisibleAnywhere, Category = "Save_Meta")
	int32 SlotId = 0;

	/** Empty by default; filled on successful SaveSlot0. */
	UPROPERTY(VisibleAnywhere, Category = "Save_Meta")
	FString Timestamp;

	// ---- Save_Progress (empty defaults) ----
	UPROPERTY(VisibleAnywhere, Category = "Save_Progress")
	TArray<FString> UnlockedBeys;

	UPROPERTY(VisibleAnywhere, Category = "Save_Progress")
	int32 MatchWins = 0;

	/** "RaceTo5" / "RaceTo8" / empty. */
	UPROPERTY(VisibleAnywhere, Category = "Save_Progress")
	FString LastMode;

	// ---- Settings placeholders ----
	UPROPERTY(VisibleAnywhere, Category = "Settings")
	float MasterVolume = 1.0f;

	UPROPERTY(VisibleAnywhere, Category = "Settings")
	bool bMute = false;

	UPROPERTY(VisibleAnywhere, Category = "Settings")
	FString Language = TEXT("zh");

	void ApplyEmptyDefaults()
	{
		SaveVersion = 1;
		SlotId = 0;
		Timestamp.Empty();
		UnlockedBeys.Reset();
		MatchWins = 0;
		LastMode.Empty();
		MasterVolume = 1.0f;
		bMute = false;
		Language = TEXT("zh");
	}
};
