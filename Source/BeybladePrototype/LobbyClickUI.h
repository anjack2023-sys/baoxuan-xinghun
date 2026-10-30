#pragma once
#include "CoreMinimal.h"
#include "MatchFlow.h"

// Shared 1920x1080 art coordinates for drawing and mouse hit testing.
// Same SelectRace / Launch / Pick path as keys. Does not touch Feel85.

enum class ELobbyClickAction : uint8
{
	None = 0,
	Race5 = 1,
	Race8 = 2,
	Start = 3,
	// PickRegular actions (pool 0..7, confirm, back)
	Pick0 = 10,
	Pick1 = 11,
	Pick2 = 12,
	Pick3 = 13,
	Pick4 = 14,
    Pick5 = 15,
    Pick6 = 16,
    Pick7 = 17,
	ConfirmPick = 20,
	BackLobby = 21,
	// Prep
	PrepLaunch = 30,
	// RoundSettle / MatchSettle / BlindPick
	NextRound = 40,
	Rematch = 41,
	ToLobby = 42,
	ConfirmBlind = 43,
	LockBlind = 44,
	OpenCollect = 50,
	CollectBack = 51,
	CollectDetailBack = 52,
	Collect0 = 60,
	Collect1 = 61,
	Collect2 = 62,
	Collect3 = 63,
	Collect4 = 64,
	Collect5 = 65,
	Collect6 = 66,
	Collect7 = 67,
	FireSkill = 80,
    EnterArena = 81,
    Avatar0 = 90, Avatar1, Avatar2, Avatar3, Avatar4, Avatar5
};

struct FLobbyClickUI
{
	static constexpr float BtnY = 500.f;
	static constexpr float BtnH = 96.f;
	static constexpr float BtnW = 280.f;
	static constexpr float Gap = 40.f;
	static constexpr float StartW = 320.f;

	// PickRegular layout
    static constexpr float SlotY = 245.f;
    static constexpr float SlotW = 160.f;
    static constexpr float SlotH = 200.f;
	static constexpr float SlotGap = 70.f;
    static constexpr float SlotX0 = 160.f;
    static constexpr float ConfirmY = 920.f;
	static constexpr float ConfirmW = 320.f;
	static constexpr float BackW = 320.f;
	static constexpr float NextW = 320.f;

	static FVector2D Race5Pos() { return FVector2D(140.f, BtnY); }
	static FVector2D Race8Pos() { return FVector2D(140.f + BtnW + Gap, BtnY); }
	static FVector2D StartPos() { return FVector2D(140.f, 650.f); }

	static float ScaleFor(const FVector2D& Viewport)
	{
		return FMath::Max(0.001f, FMath::Min(static_cast<float>(Viewport.X / 1920.f), static_cast<float>(Viewport.Y / 1080.f)));
	}
	static FVector2D ViewOrigin(const FVector2D& Viewport)
	{
		return (Viewport - FVector2D(1920.f, 1080.f) * ScaleFor(Viewport)) * 0.5f;
	}
	static FVector2D ToViewport(const FVector2D& Pos, const FVector2D& Viewport)
	{
		return ViewOrigin(Viewport) + Pos * ScaleFor(Viewport);
	}
	static FVector2D FromViewport(const FVector2D& Pos, const FVector2D& Viewport)
	{
		return (Pos - ViewOrigin(Viewport)) / ScaleFor(Viewport);
	}

	static FVector2D SlotPos(int32 Index)
	{
		const int32 Column = Index < 5 ? Index : Index - 5 + 1;
		return FVector2D(SlotX0 + Column * (SlotW + SlotGap), SlotY + (Index < 5 ? 0.f : 310.f));
	}
	static FVector2D ConfirmPos() { return FVector2D(632.f, ConfirmY); }
	static FVector2D BackPos() { return FVector2D(1008.f, ConfirmY); }
	static FVector2D PrepLaunchPos() { return ConfirmPos(); }
	static FVector2D NextRoundPos() { return FVector2D(624.f, 800.f); }
	static FVector2D RematchPos() { return NextRoundPos(); }
	static FVector2D ToLobbyPos() { return FVector2D(1000.f, 800.f); }
	static FVector2D LockBlindPos() { return FVector2D(360.f, ConfirmY); }
	static FVector2D ConfirmBlindPos() { return FVector2D(800.f, ConfirmY); }
	static FVector2D BlindBackPos() { return FVector2D(1240.f, ConfirmY); }
	static FVector2D ArenaPos() { return FVector2D(460.f, 770.f); }
	static FVector2D CollectPos() { return FVector2D(140.f, 770.f); }
	static FVector2D CollectBackPos() { return FVector2D(1008.f, 960.f); }
	static FVector2D CollectDetailBackPos() { return FVector2D(1008.f, 960.f); }
	static constexpr float CollectSlotW = 280.f;
	static constexpr float CollectSlotH = 300.f;
	static constexpr float CollectSlotGapX = 36.f;
	static constexpr float CollectSlotGapY = 28.f;
	static constexpr float CollectSlotX0 = 346.f;
	static constexpr float CollectSlotY0 = 230.f;
	static FVector2D CollectSlotPos(int32 Index)
	{
		const int32 Col = Index % 4;
		const int32 Row = Index / 4;
		return FVector2D(CollectSlotX0 + Col * (CollectSlotW + CollectSlotGapX), CollectSlotY0 + Row * (CollectSlotH + CollectSlotGapY));
	}
	// Right-thumb active skill button (Fighting only)
	static constexpr float SkillBtnW = 280.f;
	static constexpr float SkillBtnH = 120.f;
	static FVector2D SkillBtnPos() { return FVector2D(1580.f, 780.f); }

    static FVector2D AvatarPos(int32 Index) { return FVector2D(1120.f + (Index % 2) * 300.f, 260.f + (Index / 2) * 110.f); }
    static constexpr float AvatarW = 260.f;

	static bool Contains(const FVector2D& Pos, const FVector2D& Size, float X, float Y)
	{
		return X >= Pos.X && Y >= Pos.Y && X < Pos.X + Size.X && Y < Pos.Y + Size.Y;
	}

	/** Mouse in reference coordinates; convert viewport pixels with FromViewport first. */
	static ELobbyClickAction HitTest(float MouseX, float MouseY, EMatchFlowState State)
	{
		if (State == EMatchFlowState::Lobby)
		{
			const FVector2D Size(BtnW, BtnH);
			const FVector2D StartSize(StartW, BtnH);
			if (Contains(Race5Pos(), Size, MouseX, MouseY)) return ELobbyClickAction::Race5;
			if (Contains(Race8Pos(), Size, MouseX, MouseY)) return ELobbyClickAction::Race8;
			if (Contains(StartPos(), StartSize, MouseX, MouseY)) return ELobbyClickAction::Start;
			if (Contains(ArenaPos(), Size, MouseX, MouseY)) return ELobbyClickAction::EnterArena;
			if (Contains(CollectPos(), Size, MouseX, MouseY)) return ELobbyClickAction::OpenCollect;
			return ELobbyClickAction::None;
		}
		if (State == EMatchFlowState::Collection)
		{
			// Detail mode: only back
			// Grid mode: 8 slots + back. Caller distinguishes via CollectionFocus.
			for (int32 I = 0; I < 8; ++I)
			{
				if (Contains(CollectSlotPos(I), FVector2D(CollectSlotW, CollectSlotH), MouseX, MouseY))
					return static_cast<ELobbyClickAction>(static_cast<uint8>(ELobbyClickAction::Collect0) + I);
			}
			if (Contains(CollectBackPos(), FVector2D(BackW, BtnH), MouseX, MouseY))
				return ELobbyClickAction::CollectBack;
			return ELobbyClickAction::None;
		}
		if (State == EMatchFlowState::Fighting)
		{
			if (Contains(SkillBtnPos(), FVector2D(SkillBtnW, SkillBtnH), MouseX, MouseY))
				return ELobbyClickAction::FireSkill;
			return ELobbyClickAction::None;
		}
		if (State == EMatchFlowState::PickRegular)
		{
			const FVector2D SlotSize(SlotW, SlotH);
			for (int32 I = 0; I < FPickRegular::PoolSize; ++I)
			{
				if (Contains(SlotPos(I), SlotSize, MouseX, MouseY))
					return static_cast<ELobbyClickAction>(static_cast<uint8>(ELobbyClickAction::Pick0) + I);
			}
			if (Contains(ConfirmPos(), FVector2D(ConfirmW, BtnH), MouseX, MouseY))
				return ELobbyClickAction::ConfirmPick;
			if (Contains(BackPos(), FVector2D(BackW, BtnH), MouseX, MouseY))
				return ELobbyClickAction::BackLobby;
			return ELobbyClickAction::None;
		}
		if (State == EMatchFlowState::BlindPick)
		{
			const FVector2D SlotSize(SlotW, SlotH);
			for (int32 I = 0; I < FPickRegular::PoolSize; ++I)
			{
				if (Contains(SlotPos(I), SlotSize, MouseX, MouseY))
					return static_cast<ELobbyClickAction>(static_cast<uint8>(ELobbyClickAction::Pick0) + I);
			}
			if (Contains(LockBlindPos(), FVector2D(ConfirmW, BtnH), MouseX, MouseY))
				return ELobbyClickAction::LockBlind;
			if (Contains(ConfirmBlindPos(), FVector2D(ConfirmW, BtnH), MouseX, MouseY))
				return ELobbyClickAction::ConfirmBlind;
			if (Contains(BlindBackPos(), FVector2D(BackW, BtnH), MouseX, MouseY))
				return ELobbyClickAction::BackLobby;
			return ELobbyClickAction::None;
		}
		if (State == EMatchFlowState::Prep)
		{
			if (Contains(PrepLaunchPos(), FVector2D(ConfirmW, BtnH), MouseX, MouseY))
				return ELobbyClickAction::PrepLaunch;
			if (Contains(BackPos(), FVector2D(BackW, BtnH), MouseX, MouseY))
				return ELobbyClickAction::BackLobby;
			return ELobbyClickAction::None;
		}
		if (State == EMatchFlowState::RoundSettle)
		{
			if (Contains(NextRoundPos(), FVector2D(NextW, BtnH), MouseX, MouseY))
				return ELobbyClickAction::NextRound;
			if (Contains(ToLobbyPos(), FVector2D(BackW, BtnH), MouseX, MouseY))
				return ELobbyClickAction::ToLobby;
			return ELobbyClickAction::None;
		}
		if (State == EMatchFlowState::MatchSettle)
		{
			if (Contains(RematchPos(), FVector2D(NextW, BtnH), MouseX, MouseY))
				return ELobbyClickAction::Rematch;
			if (Contains(ToLobbyPos(), FVector2D(BackW, BtnH), MouseX, MouseY))
				return ELobbyClickAction::ToLobby;
			return ELobbyClickAction::None;
		}
		return ELobbyClickAction::None;
	}
};
