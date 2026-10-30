#pragma once
#include "CoreMinimal.h"
#include "BattleSimulation.h"

// Match-circle flow + scoring (race-to-5 / race-to-8).
// Does NOT touch Feel85 frozen physics constants.
// PickRegular slice: Lobby -> PickRegular (8 pick 3 or 5 + order) -> Prep -> Fighting.
// P2 BlindPick: secret pick->lock->both locked->simultaneous reveal->Prep.
// ONLINE_RESERVE: server adjudicates lock/reveal/score; local dual-lock only.
// No blind countdown hosting / reconnect / matchmaking this knife.

enum class EMatchFlowState : uint8
{
	Lobby = 0,
	PickRegular = 1,
	Prep = 2,
	Fighting = 3,
	RoundSettle = 4,
	MatchSettle = 5,
	BlindPick = 6,
	Collection = 7
};

enum class ERaceMode : uint8
{
	RaceTo5 = 5,
	RaceTo8 = 8
};

enum class EScoreTag : uint8
{
	None = 0,
	OVR = 1,
	XTR = 2
};

enum class ENextBoutKind : uint8
{
	RegularLineup = 0,
	BlindRemaining = 1,
	BlindFullReset = 2
};

struct FRoundScoreDelta
{
	int32 Delta[2] = {0, 0};
	int32 PointsToWinner = 0; // 3 ringout, 2 other unique, 0 draw
	bool bDraw = false;
	EScoreTag Tag = EScoreTag::None;
};

inline FRoundScoreDelta ComputeRoundScoreDelta(const FString& Reason, int32 Winner, EScoreTag Tag = EScoreTag::None)
{
	FRoundScoreDelta Out;
	if (Winner < 0)
	{
		Out.bDraw = true;
		Out.Delta[0] = 1;
		Out.Delta[1] = 1;
		Out.PointsToWinner = 0;
		Out.Tag = EScoreTag::None;
		return Out;
	}
	const bool bRingout = Reason == TEXT("ringout");
	const int32 Pts = bRingout ? 3 : 2;
	Out.PointsToWinner = Pts;
	Out.Delta[Winner] = Pts;
	Out.Delta[1 - Winner] = 0;
	// XTR/OVR are display tags only; both still +3 on ringout.
	Out.Tag = bRingout ? Tag : EScoreTag::None;
	if (bRingout && Out.Tag == EScoreTag::None) Out.Tag = EScoreTag::OVR;
	return Out;
}

inline const TCHAR* ScoreTagLabel(EScoreTag Tag)
{
	switch (Tag)
	{
	case EScoreTag::XTR: return TEXT("XTR");
	case EScoreTag::OVR: return TEXT("OVR");
	default: return TEXT("none");
	}
}

/** Eight-slot logical pool for regular pick (no unique meshes required). */
struct FPickPoolSlot
{
	const TCHAR* Id = TEXT("?");
	EBeyType Type = EBeyType::Attack;
};

struct FPickRegular
{
	static constexpr int32 PoolSize = 8;
	static constexpr int32 LineupSize = 5;

	// Stable order matches skill IDs, mesh imports and keyboard keys 1..8.
	FPickPoolSlot Pool[PoolSize] = {
		{TEXT("ChiFeng-ATK"), EBeyType::Attack},
		{TEXT("BiLei-DEF"), EBeyType::Defense},
		{TEXT("ChangXuan-STA"), EBeyType::Stamina},
		{TEXT("HengRen-BAL"), EBeyType::Balance},
		{TEXT("ChiWen-ATK"), EBeyType::Attack},
        {TEXT("HuangKai-DEF"), EBeyType::Defense},
        {TEXT("CuiPan-STA"), EBeyType::Stamina},
        {TEXT("ShuangHuan-BAL"), EBeyType::Balance},
	};

	// Indices into Pool; -1 = empty. Order = appearance 1->2->3.
	int32 Lineup[LineupSize] = {-1, -1, -1, -1, -1};
	int32 Count = 0;
	int32 Required = 3;

	void Reset()
	{
		for (int32 I = 0; I < LineupSize; ++I) Lineup[I] = -1;
		Count = 0;
	}

	int32 OrderOf(int32 PoolIndex) const
	{
		for (int32 I = 0; I < Count; ++I)
			if (Lineup[I] == PoolIndex) return I + 1; // 1-based
		return 0;
	}

	bool IsSelected(int32 PoolIndex) const { return OrderOf(PoolIndex) > 0; }

	/** Toggle: if already selected, remove and compact; else append if room. */
	bool Toggle(int32 PoolIndex)
	{
		if (PoolIndex < 0 || PoolIndex >= PoolSize) return false;
		const int32 Ord = OrderOf(PoolIndex);
		if (Ord > 0)
		{
			const int32 At = Ord - 1;
			for (int32 I = At; I < Count - 1; ++I) Lineup[I] = Lineup[I + 1];
			Lineup[Count - 1] = -1;
			--Count;
			return true;
		}
		if (Count >= Required) return false;
		Lineup[Count++] = PoolIndex;
		return true;
	}

	bool CanConfirm() const { return Count == Required; }

	FBeyLoadout LoadoutAtLineup(int32 LineupIndex) const
	{
		if (LineupIndex < 0 || LineupIndex >= Count) return MakeLoadout(EBeyType::Attack);
		return MakeLoadout(Pool[Lineup[LineupIndex]].Type, EBeyGrade::Grade1);
	}
};

struct FMatchFlow
{
	EMatchFlowState State = EMatchFlowState::Lobby;
	ERaceMode Mode = ERaceMode::RaceTo5;
	int32 Score[2] = {0, 0};
	int32 RoundIndex = 0; // completed rounds
	FRoundScoreDelta LastDelta;
	FString LastReason;
	int32 LastWinner = -1; // -1 draw, 0/1 player
	int32 MatchWinner = -1; // set on MatchSettle
	FPickRegular Pick;
	int32 CurrentLineupIndex = 0; // which selected top is fighting (round 0 uses 0)

	bool bPoolUsed[FPickRegular::PoolSize] = {};
	bool bBlindPhase = false;
	int32 BlindChoiceP1 = -1;
	int32 BlindChoiceP2 = -1;
	bool bBlindLockedP1 = false;
	bool bBlindLockedP2 = false;
	bool bBlindRevealed = false;
	int32 FullPoolResetCount = 0;

	int32 Target() const { return static_cast<int32>(Mode); }

	void SetMode(ERaceMode InMode)
	{
		if (State != EMatchFlowState::Lobby) return;
		Mode = InMode;
	}

	void ToggleMode()
	{
		if (State != EMatchFlowState::Lobby) return;
		Mode = (Mode == ERaceMode::RaceTo5) ? ERaceMode::RaceTo8 : ERaceMode::RaceTo5;
	}

	void ClearPoolUsed()
	{
		for (int32 I = 0; I < FPickRegular::PoolSize; ++I) bPoolUsed[I] = false;
	}

	void ResetBlindSession()
	{
		BlindChoiceP1 = BlindChoiceP2 = -1;
		bBlindLockedP1 = bBlindLockedP2 = false;
		bBlindRevealed = false;
	}

	int32 CountUsed() const
	{
		int32 N = 0;
		for (int32 I = 0; I < FPickRegular::PoolSize; ++I) if (bPoolUsed[I]) ++N;
		return N;
	}

	int32 CountUnused() const { return FPickRegular::PoolSize - CountUsed(); }

	bool IsPoolUsed(int32 PoolIndex) const
	{
		return PoolIndex >= 0 && PoolIndex < FPickRegular::PoolSize && bPoolUsed[PoolIndex];
	}

	void MarkCurrentBoutUsed()
	{
		if (bBlindPhase)
		{
			if (BlindChoiceP1 >= 0 && BlindChoiceP1 < FPickRegular::PoolSize) bPoolUsed[BlindChoiceP1] = true;
			if (BlindChoiceP2 >= 0 && BlindChoiceP2 < FPickRegular::PoolSize) bPoolUsed[BlindChoiceP2] = true;
		}
		else if (CurrentLineupIndex >= 0 && CurrentLineupIndex < Pick.Count)
		{
			const int32 PoolIndex = Pick.Lineup[CurrentLineupIndex];
			if (PoolIndex >= 0 && PoolIndex < FPickRegular::PoolSize) bPoolUsed[PoolIndex] = true;
		}
	}

	ENextBoutKind PeekNextBoutKind() const
	{
		if (!bBlindPhase && CurrentLineupIndex + 1 < Pick.Count) return ENextBoutKind::RegularLineup;
        // Both players need distinct choices from the shared pool.
        if (CountUnused() < 2) return ENextBoutKind::BlindFullReset;
		return ENextBoutKind::BlindRemaining;
	}

	int32 CollectionFocus = -1; // -1 grid, >=0 detail index into FCollectionCatalog

	void EnterCollection()
	{
		if (State != EMatchFlowState::Lobby) return;
		CollectionFocus = -1;
		State = EMatchFlowState::Collection;
	}

	void ExitCollectionToLobby()
	{
		if (State != EMatchFlowState::Collection) return;
		CollectionFocus = -1;
		State = EMatchFlowState::Lobby;
	}

	void OpenCollectionDetail(int32 Index)
	{
		if (State != EMatchFlowState::Collection) return;
		CollectionFocus = Index;
	}

	void CloseCollectionDetail()
	{
		if (State != EMatchFlowState::Collection) return;
		CollectionFocus = -1;
	}

	void ResetMatchPool()
	{
		Score[0] = Score[1] = 0;
		RoundIndex = 0;
		LastDelta = FRoundScoreDelta();
		LastReason.Empty();
		LastWinner = -1;
		MatchWinner = -1;
		Pick.Reset();
		CurrentLineupIndex = 0;
		ClearPoolUsed();
		bBlindPhase = false;
		ResetBlindSession();
		FullPoolResetCount = 0;
	}

	// Lobby -> PickRegular (caller shows pick UI).
	bool TryEnterPickFromLobby()
	{
		if (State != EMatchFlowState::Lobby) return false;
		ResetMatchPool();
		Pick.Required = Mode == ERaceMode::RaceTo8 ? 5 : 3;
		State = EMatchFlowState::PickRegular;
		return true;
	}

	/** Historical M1/auto helper: lobby -> Fighting with default 0/1/2 lineup (no pick UI). */
	bool TryStartFromLobby()
	{
		if (State != EMatchFlowState::Lobby) return false;
		ResetMatchPool();
		Pick.Required = Mode == ERaceMode::RaceTo8 ? 5 : 3;
		for (int32 I = 0; I < Pick.Required; ++I) Pick.Toggle(I);
		CurrentLineupIndex = 0;
		State = EMatchFlowState::Fighting;
		return true;
	}

	bool TryTogglePick(int32 PoolIndex)
	{
		if (State != EMatchFlowState::PickRegular) return false;
		return Pick.Toggle(PoolIndex);
	}

	// PickRegular -> Prep when the required lineup is selected with order.
	bool TryConfirmPick()
	{
		if (State != EMatchFlowState::PickRegular) return false;
		if (!Pick.CanConfirm()) return false;
		CurrentLineupIndex = 0;
		bBlindPhase = false;
		State = EMatchFlowState::Prep;
		return true;
	}

	bool TryToggleBlindP1(int32 PoolIndex)
	{
		if (State != EMatchFlowState::BlindPick) return false;
		if (bBlindLockedP1 || bBlindRevealed) return false;
		if (PoolIndex < 0 || PoolIndex >= FPickRegular::PoolSize) return false;
		if (bPoolUsed[PoolIndex]) return false;
		if (bBlindLockedP2 && BlindChoiceP2 == PoolIndex) return false;
		if (BlindChoiceP1 == PoolIndex) { BlindChoiceP1 = -1; return true; }
		BlindChoiceP1 = PoolIndex;
		return true;
	}

	bool TryToggleBlindP2(int32 PoolIndex)
	{
		if (State != EMatchFlowState::BlindPick) return false;
		if (bBlindLockedP2 || bBlindRevealed) return false;
		if (PoolIndex < 0 || PoolIndex >= FPickRegular::PoolSize) return false;
		if (bPoolUsed[PoolIndex]) return false;
		if (bBlindLockedP1 && BlindChoiceP1 == PoolIndex) return false;
		if (BlindChoiceP2 == PoolIndex) { BlindChoiceP2 = -1; return true; }
		BlindChoiceP2 = PoolIndex;
		return true;
	}

	void MaybeRevealBlind()
	{
		// Simultaneous reveal only when BOTH locked (forbid one-sided reveal).
		if (bBlindLockedP1 && bBlindLockedP2 && !bBlindRevealed) bBlindRevealed = true;
	}

	bool TryLockBlindP1()
	{
		if (State != EMatchFlowState::BlindPick) return false;
		if (bBlindLockedP1) return true;
		if (BlindChoiceP1 < 0 || bPoolUsed[BlindChoiceP1]) return false;
		if (bBlindLockedP2 && BlindChoiceP2 == BlindChoiceP1) return false;
		bBlindLockedP1 = true;
		MaybeRevealBlind();
		return true;
	}

	bool TryLockBlindP2()
	{
		if (State != EMatchFlowState::BlindPick) return false;
		if (bBlindLockedP2) return true;
		if (BlindChoiceP2 < 0 || bPoolUsed[BlindChoiceP2]) return false;
		if (bBlindLockedP1 && BlindChoiceP1 == BlindChoiceP2) return false;
		bBlindLockedP2 = true;
		MaybeRevealBlind();
		return true;
	}

	/** Local P2 stub. ONLINE_RESERVE: wait remote lock; server adjudicates; no peek. No countdown hosting. */
	bool TryAutoLockP2Local()
	{
		if (State != EMatchFlowState::BlindPick) return false;
		if (!bBlindLockedP1 || bBlindLockedP2) return false;
		if (BlindChoiceP2 < 0)
		{
			for (int32 I = 0; I < FPickRegular::PoolSize; ++I)
				if (!bPoolUsed[I] && I != BlindChoiceP1) { BlindChoiceP2 = I; break; }
		}
		return TryLockBlindP2();
	}

	bool CanConfirmBlind() const
	{
		return State == EMatchFlowState::BlindPick && bBlindRevealed
			&& BlindChoiceP1 >= 0 && BlindChoiceP2 >= 0;
	}

	bool TryConfirmBlind()
	{
		if (!CanConfirmBlind()) return false;
		bBlindPhase = true;
		State = EMatchFlowState::Prep;
		return true;
	}

	/** SPACE: lock P1 -> local auto-lock P2 -> simultaneous reveal -> Prep. */
	bool TryAdvanceBlindLocal()
	{
		if (State != EMatchFlowState::BlindPick) return false;
		if (!bBlindLockedP1)
		{
			if (BlindChoiceP1 < 0)
			{
				for (int32 I = 0; I < FPickRegular::PoolSize; ++I)
					if (!bPoolUsed[I]) { BlindChoiceP1 = I; break; }
			}
			if (!TryLockBlindP1()) return false;
			TryAutoLockP2Local();
		}
		else if (!bBlindLockedP2)
		{
			TryAutoLockP2Local();
		}
		if (bBlindRevealed) return TryConfirmBlind();
		return bBlindLockedP1;
	}

	// Prep -> Fighting (caller launches simulation / rope).
	bool TryLaunchFromPrep()
	{
		if (State != EMatchFlowState::Prep) return false;
		State = EMatchFlowState::Fighting;
		return true;
	}

    bool OnTutorialEnded(const FString& Reason, int32 Winner)
    {
        if(State!=EMatchFlowState::Fighting) return false;
        LastReason=Reason; LastWinner=Winner; LastDelta=FRoundScoreDelta();
        State=EMatchFlowState::RoundSettle;
        return true;
    }

	// After simulation ends once: apply score, enter RoundSettle or MatchSettle.
	bool OnBattleEnded(const FString& Reason, int32 Winner, EScoreTag Tag = EScoreTag::None)
	{
		if (State != EMatchFlowState::Fighting) return false;
		LastReason = Reason;
		LastWinner = Winner;
		LastDelta = ComputeRoundScoreDelta(Reason, Winner, Tag);
		Score[0] += LastDelta.Delta[0];
		Score[1] += LastDelta.Delta[1];
		++RoundIndex;
		MarkCurrentBoutUsed();

		const int32 T = Target();
		const bool P0Wins = Score[0] >= T && Score[0] > Score[1];
		const bool P1Wins = Score[1] >= T && Score[1] > Score[0];
		if (P0Wins || P1Wins)
		{
			MatchWinner = P0Wins ? 0 : 1;
			State = EMatchFlowState::MatchSettle;
		}
		else
		{
			State = EMatchFlowState::RoundSettle;
		}
		return true;
	}

	// After scored round / match settle / abort / pick back: return to lobby.
	bool ReturnToLobby()
	{
		if (State != EMatchFlowState::RoundSettle && State != EMatchFlowState::MatchSettle
			&& State != EMatchFlowState::Fighting && State != EMatchFlowState::PickRegular
			&& State != EMatchFlowState::Prep && State != EMatchFlowState::BlindPick)
			return false;
		State = EMatchFlowState::Lobby;
		ResetMatchPool();
		return true;
	}

	bool TryRematchFromMatchSettle()
	{
		if (State != EMatchFlowState::MatchSettle) return false;
		return ReturnToLobby();
	}

	/** RoundSettle next: Prep (regular 1->2->3) / BlindPick remaining / full-pool reset BlindPick. */
	bool TryContinueRound()
	{
		if (State != EMatchFlowState::RoundSettle) return false;
		const ENextBoutKind Kind = PeekNextBoutKind();
		if (Kind == ENextBoutKind::RegularLineup)
		{
			++CurrentLineupIndex;
			bBlindPhase = false;
			ResetBlindSession();
			State = EMatchFlowState::Prep;
			return true;
		}
		if (Kind == ENextBoutKind::BlindFullReset)
		{
			ClearPoolUsed();
			++FullPoolResetCount;
		}
		bBlindPhase = true;
		ResetBlindSession();
		State = EMatchFlowState::BlindPick;
		return true;
	}

	const TCHAR* ModeLabel() const
	{
		return Mode == ERaceMode::RaceTo8 ? TEXT("抢8分") : TEXT("抢5分");
	}

	const TCHAR* StateLabel() const
	{
		switch (State)
		{
		case EMatchFlowState::Lobby: return TEXT("大厅");
		case EMatchFlowState::PickRegular: return TEXT("选螺_常规");

		case EMatchFlowState::BlindPick: return TEXT("盲选");		case EMatchFlowState::Prep: return TEXT("准备");
		case EMatchFlowState::Fighting: return TEXT("战斗");
		case EMatchFlowState::RoundSettle: return TEXT("局结算");
		case EMatchFlowState::MatchSettle: return TEXT("比赛结算");
		default: return TEXT("?");
		}
	}

	const TCHAR* NextBoutKindLabel() const
	{
		switch (PeekNextBoutKind())
		{
		case ENextBoutKind::RegularLineup: return TEXT("下一场(预排)");
		case ENextBoutKind::BlindRemaining: return TEXT("盲选");
		case ENextBoutKind::BlindFullReset: return TEXT("整池重置盲选");
		default: return TEXT("?");
		}
	}

	static const TCHAR* ReasonLabelCN(const FString& Reason)
	{
		if (Reason == TEXT("ringout")) return TEXT("出界（击飞）");
		if (Reason == TEXT("spinout")) return TEXT("停转");
		if (Reason == TEXT("timeout")) return TEXT("超时（残余动量）");
		if (Reason == TEXT("burst")) return TEXT("爆裂");
		if (Reason == TEXT("trap")) return TEXT("陷阶");
		if (Reason == TEXT("reset")) return TEXT("重置");
		return TEXT("未知");
	}
};
