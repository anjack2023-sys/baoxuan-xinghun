#pragma once
#include "CoreMinimal.h"
#include "PlayerSaveGame.h"
#include "MatchFlow.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/DateTime.h"

/**
 * Minimal Save/Load for slot 0. No balance/Feel85 numbers live here.
 * Named constants avoid magic slot indices in call sites.
 */
namespace BeybladePlayerSave
{
	inline const TCHAR* SlotName() { return TEXT("BeybladeSlot0"); }
	inline constexpr int32 UserIndex() { return 0; }
	inline constexpr int32 CurrentSaveVersion() { return 1; }

	inline UBeybladePlayerSaveGame* CreateDefaults()
	{
		UBeybladePlayerSaveGame* Save = Cast<UBeybladePlayerSaveGame>(
			UGameplayStatics::CreateSaveGameObject(UBeybladePlayerSaveGame::StaticClass()));
		if (Save)
		{
			Save->ApplyEmptyDefaults();
			Save->SaveVersion = CurrentSaveVersion();
			Save->SlotId = 0;
		}
		return Save;
	}

	inline bool SaveSlot0(UBeybladePlayerSaveGame* Save)
	{
		if (!Save) return false;
		Save->SlotId = 0;
		Save->SaveVersion = CurrentSaveVersion();
		Save->Timestamp = FDateTime::Now().ToString(TEXT("%Y-%m-%dT%H:%M:%S"));
		return UGameplayStatics::SaveGameToSlot(Save, SlotName(), UserIndex());
	}

	inline UBeybladePlayerSaveGame* LoadSlot0()
	{
		if (!UGameplayStatics::DoesSaveGameExist(SlotName(), UserIndex()))
			return nullptr;
		return Cast<UBeybladePlayerSaveGame>(
			UGameplayStatics::LoadGameFromSlot(SlotName(), UserIndex()));
	}

	inline bool DoesSlot0Exist()
	{
		return UGameplayStatics::DoesSaveGameExist(SlotName(), UserIndex());
	}

	inline bool DeleteSlot0()
	{
		if (!DoesSlot0Exist()) return true;
		return UGameplayStatics::DeleteGameInSlot(SlotName(), UserIndex());
	}

	/** Load if present; otherwise create defaults, persist once, return object. */
	inline UBeybladePlayerSaveGame* LoadOrCreateSlot0()
	{
		if (UBeybladePlayerSaveGame* Existing = LoadSlot0())
			return Existing;
		UBeybladePlayerSaveGame* Fresh = CreateDefaults();
		if (Fresh) SaveSlot0(Fresh);
		return Fresh;
	}

	inline const TCHAR* ModeToPersist(ERaceMode Mode)
	{
		return Mode == ERaceMode::RaceTo8 ? TEXT("RaceTo8") : TEXT("RaceTo5");
	}

	inline bool TryParseMode(const FString& Text, ERaceMode& Out)
	{
		if (Text.Equals(TEXT("RaceTo8"), ESearchCase::IgnoreCase) || Text == TEXT("8"))
		{
			Out = ERaceMode::RaceTo8;
			return true;
		}
		if (Text.Equals(TEXT("RaceTo5"), ESearchCase::IgnoreCase) || Text == TEXT("5") || Text.IsEmpty())
		{
			Out = ERaceMode::RaceTo5;
			return true;
		}
		return false;
	}
}

