#pragma once
#include "CoreMinimal.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

// Grade1 Attack/Defense/Mass/k from balance table (class-1 tunables).
// Source of truth files (same schema):
//   Content/Beyblade/Data/grade1-loadouts.csv
//   docs/balance/grade1-loadouts.csv
//   docs/balance/tunables-template.csv keys G1_* / G2_SpinDecayMul / G3_SpinDecayMul
// Embedded rows = same numbers (offline / automation fallback). Feel85 FROZEN constants are NOT here.

// Requires EBeyType / EBeyGrade / FBeyLoadout already declared (include from BattleSimulation.h after those defs).

namespace Grade1Balance
{
	struct FRow
	{
		double Attack = 1.0;
		double Defense = 1.0;
		double Mass = 1.0;
		double SpinDecayPerSec = 0.0;
	};

	inline FRow& MutableRow(EBeyType Type)
	{
		static FRow Rows[4] = {
			{1.35, 0.85, 0.90, 0.163}, // Attack — mirrors CSV
			{0.85, 1.35, 1.15, 0.122}, // Defense
			{0.95, 1.05, 1.30, 0.103}, // Stamina
			{1.10, 1.10, 1.05, 0.130}, // Balance
		};
		int32 Idx = 0;
		if (Type == EBeyType::Defense) Idx = 1;
		else if (Type == EBeyType::Stamina) Idx = 2;
		else if (Type == EBeyType::Balance) Idx = 3;
		return Rows[Idx];
	}

	inline double& Grade2Mul() { static double M = 0.75; return M; }
	inline double& Grade3Mul() { static double M = 0.55; return M; }
	inline bool& LoadedFlag() { static bool B = false; return B; }
	inline bool& LoadedOk() { static bool B = false; return B; }

	inline EBeyType ParseType(const FString& S)
	{
		if (S.Equals(TEXT("DEFENSE"), ESearchCase::IgnoreCase) || S.Equals(TEXT("DEF"), ESearchCase::IgnoreCase)) return EBeyType::Defense;
		if (S.Equals(TEXT("STAMINA"), ESearchCase::IgnoreCase) || S.Equals(TEXT("STA"), ESearchCase::IgnoreCase)) return EBeyType::Stamina;
		if (S.Equals(TEXT("BALANCE"), ESearchCase::IgnoreCase) || S.Equals(TEXT("BAL"), ESearchCase::IgnoreCase)) return EBeyType::Balance;
		return EBeyType::Attack;
	}

	inline bool ApplyCsvLine(const FString& Line)
	{
		if (Line.IsEmpty() || Line.StartsWith(TEXT("#")) || Line.StartsWith(TEXT("type,"))) return false;
		TArray<FString> Cols;
		Line.ParseIntoArray(Cols, TEXT(","), true);
		if (Cols.Num() < 6) return false;
		const EBeyType Type = ParseType(Cols[0].TrimStartAndEnd());
		const int32 Grade = FCString::Atoi(*Cols[1].TrimStartAndEnd());
		if (Grade != 1) return false; // only Grade1 full rows in this file
		FRow& R = MutableRow(Type);
		R.Attack = FCString::Atod(*Cols[2].TrimStartAndEnd());
		R.Defense = FCString::Atod(*Cols[3].TrimStartAndEnd());
		R.Mass = FCString::Atod(*Cols[4].TrimStartAndEnd());
		R.SpinDecayPerSec = FCString::Atod(*Cols[5].TrimStartAndEnd());
		return true;
	}

	inline bool TryLoadFile(const FString& Path)
	{
		FString Text;
		if (!FFileHelper::LoadFileToString(Text, *Path)) return false;
		TArray<FString> Lines;
		Text.ParseIntoArrayLines(Lines, true);
		int32 Applied = 0;
		for (const FString& Line : Lines)
		{
			if (ApplyCsvLine(Line)) ++Applied;
		}
		return Applied >= 4;
	}

	inline void ApplyTunableKey(const FString& Key, double Value)
	{
		if (Key == TEXT("G1_ATK_Attack")) MutableRow(EBeyType::Attack).Attack = Value;
		else if (Key == TEXT("G1_ATK_Defense")) MutableRow(EBeyType::Attack).Defense = Value;
		else if (Key == TEXT("G1_ATK_Mass")) MutableRow(EBeyType::Attack).Mass = Value;
		else if (Key == TEXT("G1_ATK_SpinDecay")) MutableRow(EBeyType::Attack).SpinDecayPerSec = Value;
		else if (Key == TEXT("G1_DEF_Attack")) MutableRow(EBeyType::Defense).Attack = Value;
		else if (Key == TEXT("G1_DEF_Defense")) MutableRow(EBeyType::Defense).Defense = Value;
		else if (Key == TEXT("G1_DEF_Mass")) MutableRow(EBeyType::Defense).Mass = Value;
		else if (Key == TEXT("G1_DEF_SpinDecay")) MutableRow(EBeyType::Defense).SpinDecayPerSec = Value;
		else if (Key == TEXT("G1_STA_Attack")) MutableRow(EBeyType::Stamina).Attack = Value;
		else if (Key == TEXT("G1_STA_Defense")) MutableRow(EBeyType::Stamina).Defense = Value;
		else if (Key == TEXT("G1_STA_Mass")) MutableRow(EBeyType::Stamina).Mass = Value;
		else if (Key == TEXT("G1_STA_SpinDecay")) MutableRow(EBeyType::Stamina).SpinDecayPerSec = Value;
		else if (Key == TEXT("G1_BAL_Attack")) MutableRow(EBeyType::Balance).Attack = Value;
		else if (Key == TEXT("G1_BAL_Defense")) MutableRow(EBeyType::Balance).Defense = Value;
		else if (Key == TEXT("G1_BAL_Mass")) MutableRow(EBeyType::Balance).Mass = Value;
		else if (Key == TEXT("G1_BAL_SpinDecay")) MutableRow(EBeyType::Balance).SpinDecayPerSec = Value;
		else if (Key == TEXT("G2_SpinDecayMul")) Grade2Mul() = Value;
		else if (Key == TEXT("G3_SpinDecayMul")) Grade3Mul() = Value;
		// frozen Feel85 keys intentionally ignored
	}

	inline bool TryLoadTunables(const FString& Path)
	{
		FString Text;
		if (!FFileHelper::LoadFileToString(Text, *Path)) return false;
		TArray<FString> Lines;
		Text.ParseIntoArrayLines(Lines, true);
		int32 Applied = 0;
		for (const FString& Line : Lines)
		{
			if (Line.IsEmpty() || Line.StartsWith(TEXT("#")) || Line.StartsWith(TEXT("key,"))) continue;
			TArray<FString> Cols;
			Line.ParseIntoArray(Cols, TEXT(","), true);
			if (Cols.Num() < 4) continue;
			const FString Key = Cols[0].TrimStartAndEnd();
			const FString Frozen = Cols[3].TrimStartAndEnd();
			if (Frozen.Equals(TEXT("true"), ESearchCase::IgnoreCase)) continue; // never take Feel85 from tunables
			if (!Key.StartsWith(TEXT("G1_")) && !Key.StartsWith(TEXT("G2_")) && !Key.StartsWith(TEXT("G3_"))) continue;
			ApplyTunableKey(Key, FCString::Atod(*Cols[1].TrimStartAndEnd()));
			++Applied;
		}
		return Applied > 0;
	}

	inline void EnsureLoaded()
	{
		if (LoadedFlag()) return;
		LoadedFlag() = true;
		const FString Candidates[] = {
			FPaths::ProjectContentDir() / TEXT("Beyblade/Data/grade1-loadouts.csv"),
			FPaths::ProjectDir() / TEXT("docs/balance/grade1-loadouts.csv"),
			FPaths::ProjectDir() / TEXT("Content/Beyblade/Data/grade1-loadouts.csv"),
		};
		bool Ok = false;
		for (const FString& P : Candidates)
		{
			if (TryLoadFile(P)) { Ok = true; break; }
		}
		// Overlay non-frozen G1_* from tunables if present (same values expected).
		const FString Tunables[] = {
			FPaths::ProjectDir() / TEXT("docs/balance/tunables-template.csv"),
			FPaths::ProjectContentDir() / TEXT("Beyblade/Data/tunables-template.csv"),
		};
		for (const FString& P : Tunables)
		{
			TryLoadTunables(P);
		}
		LoadedOk() = Ok;
		UE_LOG(LogTemp, Display, TEXT("GRADE1_DATA loaded_from_csv=%d atk=(%.3f,%.3f,%.3f,k=%.3f) def=(%.3f,%.3f,%.3f,k=%.3f) sta=(%.3f,%.3f,%.3f,k=%.3f) bal=(%.3f,%.3f,%.3f,k=%.3f)"),
			Ok ? 1 : 0,
			MutableRow(EBeyType::Attack).Attack, MutableRow(EBeyType::Attack).Defense, MutableRow(EBeyType::Attack).Mass, MutableRow(EBeyType::Attack).SpinDecayPerSec,
			MutableRow(EBeyType::Defense).Attack, MutableRow(EBeyType::Defense).Defense, MutableRow(EBeyType::Defense).Mass, MutableRow(EBeyType::Defense).SpinDecayPerSec,
			MutableRow(EBeyType::Stamina).Attack, MutableRow(EBeyType::Stamina).Defense, MutableRow(EBeyType::Stamina).Mass, MutableRow(EBeyType::Stamina).SpinDecayPerSec,
			MutableRow(EBeyType::Balance).Attack, MutableRow(EBeyType::Balance).Defense, MutableRow(EBeyType::Balance).Mass, MutableRow(EBeyType::Balance).SpinDecayPerSec);
	}

	inline bool WasLoadedFromCsv() { EnsureLoaded(); return LoadedOk(); }

	inline FRow GetRow(EBeyType Type)
	{
		EnsureLoaded();
		return MutableRow(Type);
	}

	inline FBeyLoadout MakeLoadout(EBeyType Type, EBeyGrade Grade = EBeyGrade::Grade1)
	{
		EnsureLoaded();
		FBeyLoadout L;
		L.Type = Type;
		L.Grade = Grade;
		const FRow R = MutableRow(Type);
		L.Attack = R.Attack;
		L.Defense = R.Defense;
		L.Mass = R.Mass;
		L.SpinDecayPerSec = R.SpinDecayPerSec;
		if (Grade == EBeyGrade::Grade2) L.SpinDecayPerSec *= Grade2Mul();
		else if (Grade == EBeyGrade::Grade3) L.SpinDecayPerSec *= Grade3Mul();
		return L;
	}

	/** Test helper: force re-read next EnsureLoaded (does not clear embedded defaults mid-test unless Reload). */
	inline void ResetLoadStateForTests()
	{
		LoadedFlag() = false;
		LoadedOk() = false;
		MutableRow(EBeyType::Attack) = {1.35, 0.85, 0.90, 0.163};
		MutableRow(EBeyType::Defense) = {0.85, 1.35, 1.15, 0.122};
		MutableRow(EBeyType::Stamina) = {0.95, 1.05, 1.30, 0.103};
		MutableRow(EBeyType::Balance) = {1.10, 1.10, 1.05, 0.130};
		Grade2Mul() = 0.75;
		Grade3Mul() = 0.55;
	}
}
