#pragma once
#include "CoreMinimal.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

// Class-2 content strings (from content table / content-strings.csv).
// Embedded defaults mirror the CSV; EnsureLoaded may overlay from disk.

namespace ContentStrings
{
	inline TMap<FString, FString>& Map()
	{
		static TMap<FString, FString> M;
		static bool bInit = false;
		if (!bInit)
		{
			bInit = true;
			M.Add(TEXT("lobby_title"), TEXT("对战准备"));
			M.Add(TEXT("lobby_race5"), TEXT("抢 5 分"));
			M.Add(TEXT("lobby_race8"), TEXT("抢 8 分"));
			M.Add(TEXT("lobby_start"), TEXT("开始"));
			M.Add(TEXT("lobby_hint"), TEXT("点击下方按钮或 1=抢5  2=抢8  TAB切换  |  SPACE/点「开始」"));
			M.Add(TEXT("pick_hint"), TEXT("从 5 只中选出 3 只，并排好出场顺序"));
			M.Add(TEXT("pick_progress"), TEXT("已选 {0}/3"));
			M.Add(TEXT("pick_confirm"), TEXT("确认出场"));
			M.Add(TEXT("pick_back"), TEXT("返回大厅"));
			M.Add(TEXT("pick_keys"), TEXT("键 1-8 切换  SPACE 确认  R 返回"));
			M.Add(TEXT("blind_title"), TEXT("盲选"));
			M.Add(TEXT("blind_hint"), TEXT("秘密选择下一只（对方看不到）"));
			M.Add(TEXT("blind_wait"), TEXT("等待双方锁定…"));
			M.Add(TEXT("blind_reveal"), TEXT("同时揭晓"));
			M.Add(TEXT("blind_lock"), TEXT("锁定"));
			M.Add(TEXT("blind_confirm"), TEXT("进入准备"));
			M.Add(TEXT("blind_note"), TEXT("揭晓前不可窥视；双方锁定后同时揭晓（本期无倒计时托管）"));
			M.Add(TEXT("prep_launch"), TEXT("进入拉绳"));
			M.Add(TEXT("prep_back"), TEXT("返回大厅"));
			M.Add(TEXT("prep_hint"), TEXT("SPACE/点击 = 拉绳一步后开战"));
			M.Add(TEXT("rope_label"), TEXT("拉绳发射"));
			M.Add(TEXT("settle_next"), TEXT("下一局"));
			M.Add(TEXT("settle_to_lobby"), TEXT("返回大厅"));
			M.Add(TEXT("match_rematch"), TEXT("再来一局"));
			M.Add(TEXT("match_to_lobby"), TEXT("返回大厅"));
			M.Add(TEXT("match_hint"), TEXT("再来一局 = 回大厅重选抢5/8 后再选螺"));
			M.Add(TEXT("flow_banner"), TEXT("流程：大厅→选螺→准备(拉绳)→战斗→结算/盲选（Feel85冻结）"));
			M.Add(TEXT("fight_hint"), TEXT("战斗中  |  R 中途回大厅"));
			M.Add(TEXT("round_hint"), TEXT("局结算：SPACE/点「下一局」  |  R 回大厅"));
			M.Add(TEXT("match_hint_keys"), TEXT("比赛结算：再来一局 / 返回大厅  |  SPACE 再来"));
			M.Add(TEXT("blind_hint_keys"), TEXT("盲选：点未用槽 → 锁定 → 双方锁定同时揭晓 → 进入准备  |  R 回大厅"));
			M.Add(TEXT("prep_hint_keys"), TEXT("准备/拉绳：SPACE/点「进入拉绳」  |  R 回大厅"));
			M.Add(TEXT("pick_hint_keys"), TEXT("选螺：点选/1-8 选满 3 只  |  SPACE 确认出场  |  R 返回"));
		}
		return M;
	}

	inline bool& LoadedFlag() { static bool B = false; return B; }
	inline bool& LoadedOk() { static bool B = false; return B; }

	inline bool TryLoadFile(const FString& Path)
	{
		FString Text;
		if (!FFileHelper::LoadFileToString(Text, *Path)) return false;
		TArray<FString> Lines;
		Text.ParseIntoArrayLines(Lines, true);
		int32 Applied = 0;
		for (const FString& Line : Lines)
		{
			if (Line.IsEmpty() || Line.StartsWith(TEXT("#")) || Line.StartsWith(TEXT("str_id,"))) continue;
			FString Id, Rest;
			if (!Line.Split(TEXT(","), &Id, &Rest)) continue;
			FString Zh, Context;
			if (!Rest.Split(TEXT(","), &Zh, &Context, ESearchCase::IgnoreCase, ESearchDir::FromEnd)) Zh = Rest;
			Id = Id.TrimStartAndEnd();
			Zh = Zh.TrimStartAndEnd();
			if (Id.IsEmpty() || Zh.IsEmpty()) continue;
			Map().FindOrAdd(Id) = Zh;
			++Applied;
		}
		return Applied > 0;
	}

	inline void EnsureLoaded()
	{
		if (LoadedFlag()) return;
		LoadedFlag() = true;
		(void)Map();
		const FString Candidates[] = {
			FPaths::ProjectContentDir() / TEXT("Beyblade/Data/content-strings.csv"),
			FPaths::ProjectDir() / TEXT("docs/content/content-strings.csv"),
			FPaths::ProjectDir() / TEXT("Content/Beyblade/Data/content-strings.csv"),
		};
		bool Ok = false;
		for (const FString& P : Candidates)
		{
			if (TryLoadFile(P)) { Ok = true; break; }
		}
		LoadedOk() = Ok;
		UE_LOG(LogTemp, Display, TEXT("CONTENT_STRINGS loaded_from_csv=%d count=%d"), Ok ? 1 : 0, Map().Num());
	}

	inline FString Get(const TCHAR* Id)
	{
		EnsureLoaded();
		if (const FString* Found = Map().Find(Id)) return *Found;
		return FString(Id);
	}

	inline FString Format(const TCHAR* Id, int32 A)
	{
		return Get(Id).Replace(TEXT("{0}"), *FString::FromInt(A));
	}

	inline bool WasLoadedFromCsv() { EnsureLoaded(); return LoadedOk(); }
}

