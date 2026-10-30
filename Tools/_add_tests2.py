# -*- coding: utf-8 -*-
from pathlib import Path
root = Path(r"C:\BeybladeUE\Source\BeybladePrototype")

# Fix Grade1 test expectation 0.130
tpath = root / "BattleSimulationTest.cpp"
t = tpath.read_text(encoding="utf-8")
t = t.replace(
    "TestTrue(TEXT(\"table BAL k\"), FMath::IsNearlyEqual(Balance.SpinDecayPerSec, 0.135));",
    "TestTrue(TEXT(\"table BAL k\"), FMath::IsNearlyEqual(Balance.SpinDecayPerSec, 0.130));",
)

# Includes
if '#include "SkillRuntime.h"' not in t:
    if '#include "MatchFlow.h"' in t:
        t = t.replace('#include "MatchFlow.h"', '#include "MatchFlow.h"\n#include "SkillRuntime.h"\n#include "CollectionCatalog.h"\n#include "LobbyClickUI.h"')
    elif '#include "LobbyClickUI.h"' in t:
        t = t.replace('#include "LobbyClickUI.h"', '#include "LobbyClickUI.h"\n#include "SkillRuntime.h"\n#include "CollectionCatalog.h"')
    else:
        # after first include block
        t = '#include "SkillRuntime.h"\n#include "CollectionCatalog.h"\n#include "LobbyClickUI.h"\n#include "MatchFlow.h"\n' + t

if "FActiveSkillShellTest" not in t:
    t += r'''

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FActiveSkillShellTest, "Beyblade.Match.ActiveSkillShell", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FActiveSkillShellTest::RunTest(const FString&)
{
	// Chifeng path: Attack+20% duration, escalate 5/10
	FActiveSkillShell Sk;
	Sk.ConfigureForPoolSlot(0, EBeyType::Attack);
	TestEqual(TEXT("chifeng kind"), (int32)Sk.Kind, (int32)EActiveSkillKind::ChifengBurst);
	TestEqual(TEXT("initial progress"), (int32)Sk.State(), (int32)ESkillButtonState::Progress);
	TestEqual(TEXT("need starts 5"), Sk.Need(), 5);
	TestFalse(TEXT("no auto fire"), Sk.TryFire());
	Sk.ObserveHits(5);
	TestEqual(TEXT("ready at 5"), (int32)Sk.State(), (int32)ESkillButtonState::Ready);
	TestTrue(TEXT("player can fire"), Sk.TryFire());
	TestEqual(TEXT("progress cleared"), Sk.HitsDealt, 0);
	TestEqual(TEXT("next need 10"), Sk.Need(), 10);
	TestTrue(TEXT("atk mul 1.2"), FMath::IsNearlyEqual(Sk.AttackMulActive, 1.20));
	TestTrue(TEXT("ringout add 0.1"), FMath::IsNearlyEqual(Sk.RingoutRateAdd, 0.10));
	Sk.TickFx(3.5);
	TestEqual(TEXT("back to progress"), (int32)Sk.State(), (int32)ESkillButtonState::Progress);
	TestEqual(TEXT("still need 10"), Sk.Need(), 10);
	TestFalse(TEXT("cannot fire early"), Sk.TryFire());

	// Chiwen path: next-hit Extra 1.35 (not Attack duration)
	FActiveSkillShell Cw;
	Cw.ConfigureForPoolSlot(4, EBeyType::Attack);
	TestEqual(TEXT("chiwen kind"), (int32)Cw.Kind, (int32)EActiveSkillKind::ChiwenNextExtra);
	Cw.ObserveHits(5);
	TestTrue(TEXT("chiwen fire"), Cw.TryFire());
	TestTrue(TEXT("chiwen extra 1.35"), FMath::IsNearlyEqual(Cw.ExtraKickMulPending, 1.35));
	TestTrue(TEXT("chiwen no atk mul"), FMath::IsNearlyEqual(Cw.AttackMulActive, 1.0));
	Cw.NotifyExtraConsumed();
	TestEqual(TEXT("chiwen after consume"), (int32)Cw.State(), (int32)ESkillButtonState::Progress);
	TestEqual(TEXT("chiwen next need 10"), Cw.Need(), 10);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCollectionPanelTest, "Beyblade.Match.CollectionPanel", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCollectionPanelTest::RunTest(const FString&)
{
	TestEqual(TEXT("eight entries"), FCollectionCatalog::Count, 8);
	TestEqual(TEXT("slot0 chifeng"), FString(FCollectionCatalog::Get(0).Id), FString(TEXT("chifeng")));
	TestEqual(TEXT("slot3 chiwen"), FString(FCollectionCatalog::Get(3).Id), FString(TEXT("chiwen")));
	TestEqual(TEXT("slot4 huangkai"), FString(FCollectionCatalog::Get(4).Id), FString(TEXT("huangkai")));
	TestEqual(TEXT("slot5 cuipan"), FString(FCollectionCatalog::Get(5).Id), FString(TEXT("cuipan")));
	TestEqual(TEXT("slot7 shuanghuan"), FString(FCollectionCatalog::Get(7).Id), FString(TEXT("shuanghuan")));
	TestEqual(TEXT("chiwen zh"), FString(FCollectionCatalog::Get(3).NameZh), FString(TEXT("炽纹")));
	TestEqual(TEXT("huangkai zh"), FString(FCollectionCatalog::Get(4).NameZh), FString(TEXT("煌铠")));
	TestEqual(TEXT("cuipan zh"), FString(FCollectionCatalog::Get(5).NameZh), FString(TEXT("翠磐")));
	TestEqual(TEXT("shuanghuan zh"), FString(FCollectionCatalog::Get(7).NameZh), FString(TEXT("霜环")));

	FMatchFlow Flow;
	TestTrue(TEXT("lobby start"), Flow.State == EMatchFlowState::Lobby);
	Flow.EnterCollection();
	TestEqual(TEXT("collection state"), (int32)Flow.State, (int32)EMatchFlowState::Collection);
	Flow.OpenCollectionDetail(3);
	TestEqual(TEXT("detail focus"), Flow.CollectionFocus, 3);
	Flow.CloseCollectionDetail();
	TestEqual(TEXT("grid again"), Flow.CollectionFocus, -1);
	Flow.ExitCollectionToLobby();
	TestEqual(TEXT("back lobby"), (int32)Flow.State, (int32)EMatchFlowState::Lobby);

	const FVector2D Collect = FLobbyClickUI::CollectPos();
	TestEqual(TEXT("lobby collect hit"), (int32)FLobbyClickUI::HitTest(Collect.X + 5.f, Collect.Y + 5.f, EMatchFlowState::Lobby), (int32)ELobbyClickAction::OpenCollect);
	const FVector2D Slot0 = FLobbyClickUI::CollectSlotPos(0);
	TestEqual(TEXT("collect slot0 hit"), (int32)FLobbyClickUI::HitTest(Slot0.X + 5.f, Slot0.Y + 5.f, EMatchFlowState::Collection), (int32)ELobbyClickAction::Collect0);
	const FVector2D Skill = FLobbyClickUI::SkillBtnPos();
	TestEqual(TEXT("fighting skill hit"), (int32)FLobbyClickUI::HitTest(Skill.X + 5.f, Skill.Y + 5.f, EMatchFlowState::Fighting), (int32)ELobbyClickAction::FireSkill);
	TestEqual(TEXT("lobby no skill"), (int32)FLobbyClickUI::HitTest(Skill.X + 5.f, Skill.Y + 5.f, EMatchFlowState::Lobby), (int32)ELobbyClickAction::None);
	return true;
}
'''
    print("tests appended")
else:
    print("tests already present")

tpath.write_text(t, encoding="utf-8")
print("BAL k assert", "0.130" in tpath.read_text(encoding="utf-8"))
print("ActiveSkill", "FActiveSkillShellTest" in tpath.read_text(encoding="utf-8"))
