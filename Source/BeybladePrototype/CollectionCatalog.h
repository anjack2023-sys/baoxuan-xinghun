#pragma once
#include "CoreMinimal.h"
#include "BattleSimulation.h"

/** Eight-bey collection catalog (≠ five-card fight pool). Feel untouched. */
struct FCollectionEntry
{
	const TCHAR* Id = TEXT("");
	const TCHAR* NameZh = TEXT("");
	EBeyType Type = EBeyType::Attack;
	int32 Grade = 1;
	const TCHAR* DescZh = TEXT("");
	const TCHAR* Portrait = TEXT(""); // T_* leaf under /Game/Beyblade/UI/P3/
	const TCHAR* MeshLeaf = TEXT(""); // SM_* leaf under Tripo_v1
};

struct FCollectionCatalog
{
	static constexpr int32 Count = 8;

	static const FCollectionEntry& Get(int32 Index)
	{
		static const FCollectionEntry Rows[Count] = {
			{TEXT("chifeng"), TEXT("赤锋"), EBeyType::Attack, 1, TEXT("定妆攻击型：锐角+赤核，破甲突击。"), TEXT("PortraitChifeng"), TEXT("Chifeng")},
			{TEXT("bilei"), TEXT("壁垒"), EBeyType::Defense, 1, TEXT("定妆防御型：厚环+蓝核，稳守硬抗。"), TEXT("PortraitBilei"), TEXT("Bilei")},
			{TEXT("changxuan"), TEXT("长旋"), EBeyType::Stamina, 1, TEXT("定妆持久型：长翼+青核，续航磨转。"), TEXT("PortraitChangxuan"), TEXT("Changxuan")},
			{TEXT("chiwen"), TEXT("炽纹"), EBeyType::Attack, 1, TEXT("第二攻击：炽焰纹路，追击爆发。"), TEXT("PortraitChiwen"), TEXT("Chiwen")},
			{TEXT("huangkai"), TEXT("煌铠"), EBeyType::Defense, 1, TEXT("第二防御：金铠护环，边线固守。"), TEXT("PortraitHuangkai"), TEXT("Huangkai")},
			{TEXT("cuipan"), TEXT("翠磐"), EBeyType::Stamina, 1, TEXT("第二持久：石质厚盘，耐磨久停。"), TEXT("PortraitCuipan"), TEXT("Cuipan")},
			{TEXT("hengblade"), TEXT("衡刃"), EBeyType::Balance, 1, TEXT("定妆均衡型：黑刃+白核，攻防兼顾。"), TEXT("PortraitHengren"), TEXT("Hengren")},
			{TEXT("shuanghuan"), TEXT("霜环"), EBeyType::Balance, 1, TEXT("第二均衡：双环冷锋，节奏回冲。"), TEXT("PortraitShuanghuan"), TEXT("Shuanghuan")},
		};
		return Rows[FMath::Clamp(Index, 0, Count - 1)];
	}
};
