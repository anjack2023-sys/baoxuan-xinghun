# -*- coding: utf-8 -*-
from pathlib import Path
root = Path(r"C:\BeybladeUE\Source\BeybladePrototype")

# ---- MatchFlow.h: add Collection state ----
mf = (root / "MatchFlow.h").read_text(encoding="utf-8")
if "Collection = 7" not in mf:
    mf = mf.replace(
        "\tBlindPick = 6\n};",
        "\tBlindPick = 6,\n\tCollection = 7\n};",
    )
# Add collection helpers before closing of FMatchFlow if missing
if "EnterCollection" not in mf:
    needle = "\tvoid ResetMatchPool()"
    insert = '''\tint32 CollectionFocus = -1; // -1 grid, >=0 detail index into FCollectionCatalog

\tvoid EnterCollection()
\t{
\t\tif (State != EMatchFlowState::Lobby) return;
\t\tCollectionFocus = -1;
\t\tState = EMatchFlowState::Collection;
\t}

\tvoid ExitCollectionToLobby()
\t{
\t\tif (State != EMatchFlowState::Collection) return;
\t\tCollectionFocus = -1;
\t\tState = EMatchFlowState::Lobby;
\t}

\tvoid OpenCollectionDetail(int32 Index)
\t{
\t\tif (State != EMatchFlowState::Collection) return;
\t\tCollectionFocus = Index;
\t}

\tvoid CloseCollectionDetail()
\t{
\t\tif (State != EMatchFlowState::Collection) return;
\t\tCollectionFocus = -1;
\t}

\tvoid ResetMatchPool()'''
    mf = mf.replace(needle, insert)
(root / "MatchFlow.h").write_text(mf, encoding="utf-8")
print("MatchFlow patched", "Collection" in mf)

# ---- LobbyClickUI.h ----
lc = (root / "LobbyClickUI.h").read_text(encoding="utf-8")
if "OpenCollect" not in lc:
    lc = lc.replace(
        "\tLockBlind = 44\n};",
        "\tLockBlind = 44,\n\tOpenCollect = 50,\n\tCollectBack = 51,\n\tCollectDetailBack = 52,\n\tCollect0 = 60,\n\tCollect1 = 61,\n\tCollect2 = 62,\n\tCollect3 = 63,\n\tCollect4 = 64,\n\tCollect5 = 65,\n\tCollect6 = 66,\n\tCollect7 = 67,\n\tFireSkill = 80\n};",
    )
if "CollectPos" not in lc:
    lc = lc.replace(
        "\tstatic FVector2D BlindBackPos() { return FVector2D(1240.f, ConfirmY); }",
        '''\tstatic FVector2D BlindBackPos() { return FVector2D(1240.f, ConfirmY); }
\tstatic FVector2D CollectPos() { return FVector2D(140.f, 770.f); }
\tstatic FVector2D CollectBackPos() { return FVector2D(1008.f, 960.f); }
\tstatic FVector2D CollectDetailBackPos() { return FVector2D(1008.f, 960.f); }
\tstatic constexpr float CollectSlotW = 180.f;
\tstatic constexpr float CollectSlotH = 220.f;
\tstatic constexpr float CollectSlotGapX = 36.f;
\tstatic constexpr float CollectSlotGapY = 28.f;
\tstatic constexpr float CollectSlotX0 = 280.f;
\tstatic constexpr float CollectSlotY0 = 240.f;
\tstatic FVector2D CollectSlotPos(int32 Index)
\t{
\t\tconst int32 Col = Index % 4;
\t\tconst int32 Row = Index / 4;
\t\treturn FVector2D(CollectSlotX0 + Col * (CollectSlotW + CollectSlotGapX), CollectSlotY0 + Row * (CollectSlotH + CollectSlotGapY));
\t}
\t// Right-thumb active skill button (Fighting only)
\tstatic constexpr float SkillBtnW = 120.f;
\tstatic constexpr float SkillBtnH = 120.f;
\tstatic FVector2D SkillBtnPos() { return FVector2D(1680.f, 780.f); }''',
    )
# Lobby hit: Collect button
if "OpenCollect" not in lc.split("State == EMatchFlowState::Lobby")[1][:800]:
    lc = lc.replace(
        '''\t\tif (State == EMatchFlowState::Lobby)
\t\t{
\t\t\tconst FVector2D Size(BtnW, BtnH);
\t\t\tconst FVector2D StartSize(StartW, BtnH);
\t\t\tif (Contains(Race5Pos(), Size, MouseX, MouseY)) return ELobbyClickAction::Race5;
\t\t\tif (Contains(Race8Pos(), Size, MouseX, MouseY)) return ELobbyClickAction::Race8;
\t\t\tif (Contains(StartPos(), StartSize, MouseX, MouseY)) return ELobbyClickAction::Start;
\t\t\treturn ELobbyClickAction::None;
\t\t}''',
        '''\t\tif (State == EMatchFlowState::Lobby)
\t\t{
\t\t\tconst FVector2D Size(BtnW, BtnH);
\t\t\tconst FVector2D StartSize(StartW, BtnH);
\t\t\tif (Contains(Race5Pos(), Size, MouseX, MouseY)) return ELobbyClickAction::Race5;
\t\t\tif (Contains(Race8Pos(), Size, MouseX, MouseY)) return ELobbyClickAction::Race8;
\t\t\tif (Contains(StartPos(), StartSize, MouseX, MouseY)) return ELobbyClickAction::Start;
\t\t\tif (Contains(CollectPos(), Size, MouseX, MouseY)) return ELobbyClickAction::OpenCollect;
\t\t\treturn ELobbyClickAction::None;
\t\t}
\t\tif (State == EMatchFlowState::Collection)
\t\t{
\t\t\t// Detail mode: only back
\t\t\t// Grid mode: 8 slots + back. Caller distinguishes via CollectionFocus.
\t\t\tfor (int32 I = 0; I < 8; ++I)
\t\t\t{
\t\t\t\tif (Contains(CollectSlotPos(I), FVector2D(CollectSlotW, CollectSlotH), MouseX, MouseY))
\t\t\t\t\treturn static_cast<ELobbyClickAction>(static_cast<uint8>(ELobbyClickAction::Collect0) + I);
\t\t\t}
\t\t\tif (Contains(CollectBackPos(), FVector2D(BackW, BtnH), MouseX, MouseY))
\t\t\t\treturn ELobbyClickAction::CollectBack;
\t\t\treturn ELobbyClickAction::None;
\t\t}
\t\tif (State == EMatchFlowState::Fighting)
\t\t{
\t\t\tif (Contains(SkillBtnPos(), FVector2D(SkillBtnW, SkillBtnH), MouseX, MouseY))
\t\t\t\treturn ELobbyClickAction::FireSkill;
\t\t\treturn ELobbyClickAction::None;
\t\t}''',
    )
(root / "LobbyClickUI.h").write_text(lc, encoding="utf-8")
print("LobbyClickUI patched")
print("done phase1")
