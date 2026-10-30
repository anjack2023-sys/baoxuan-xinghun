# -*- coding: utf-8 -*-
from pathlib import Path
p = Path(r"C:\BeybladeUE\Source\BeybladePrototype\ArtHUD.cpp")
src = p.read_text(encoding="utf-8")

# Fix BeyName + Portraits for ChiWen
src = src.replace(
    'const TCHAR* Names[] = {TEXT("赤锋"), TEXT("壁垒"), TEXT("长旋"), TEXT("衡刃"), TEXT("炽纹")};',
    'const TCHAR* Names[] = {TEXT("赤锋"), TEXT("壁垒"), TEXT("长旋"), TEXT("衡刃"), TEXT("炽纹")};',
)
# Maybe garbled - use regex on ASCII-safe pattern
import re
src2 = re.sub(
    r'const TCHAR\* Names\[\] = \{[^;]+;',
    'const TCHAR* Names[] = {TEXT("赤锋"), TEXT("壁垒"), TEXT("长旋"), TEXT("衡刃"), TEXT("炽纹")};',
    src,
    count=1,
)
src = src2

src = src.replace(
    'const TCHAR* Portraits[] = {TEXT("PortraitChifeng"), TEXT("PortraitBilei"), TEXT("PortraitChangxuan"), TEXT("PortraitHengren"), TEXT("PortraitChifeng")};',
    'const TCHAR* Portraits[] = {TEXT("PortraitChifeng"), TEXT("PortraitBilei"), TEXT("PortraitChangxuan"), TEXT("PortraitHengren"), TEXT("PortraitChiwen")};',
)

# Lobby: add Collect button before return
lobby_old = '''        Button(TEXT("Start"), FLobbyClickUI::StartPos(), FLobbyClickUI::StartW);
        Text(TEXT("点击按钮或按空格开始  ·  1 / 2 切换赛制"), FVector2D(145, 815), 23, Cream);
        return;
    }'''
# May be garbled Chinese - find by Button Start and nearby return
if "CollectPos" not in src:
    # Find lobby Start button block
    m = re.search(r'Button\(TEXT\("Start"\), FLobbyClickUI::StartPos\(\), FLobbyClickUI::StartW\);\s*\n\s*Text\([^;]+;\s*\n\s*return;', src)
    if not m:
        # try without Text line
        m = re.search(r'Button\(TEXT\("Start"\), FLobbyClickUI::StartPos\(\), FLobbyClickUI::StartW\);', src)
        if m:
            insert = '''Button(TEXT("Start"), FLobbyClickUI::StartPos(), FLobbyClickUI::StartW);
        Button(TEXT("LobbyButton"), FLobbyClickUI::CollectPos(), FLobbyClickUI::BtnW, TEXT("收集"));
'''
            src = src[:m.start()] + insert + src[m.end()+1:]  # careful
            # Actually replace just the Start line with Start+Collect
            src = src.replace(
                'Button(TEXT("Start"), FLobbyClickUI::StartPos(), FLobbyClickUI::StartW);',
                'Button(TEXT("Start"), FLobbyClickUI::StartPos(), FLobbyClickUI::StartW);\n        Button(TEXT("LobbyButton"), FLobbyClickUI::CollectPos(), FLobbyClickUI::BtnW, TEXT("收集"));',
                1,
            )
    else:
        src = src[:m.start()] + '''Button(TEXT("Start"), FLobbyClickUI::StartPos(), FLobbyClickUI::StartW);
        Button(TEXT("LobbyButton"), FLobbyClickUI::CollectPos(), FLobbyClickUI::BtnW, TEXT("收集"));
        Text(TEXT("点击按钮或按空格开始"), FVector2D(145, 815), 23, Cream);
        return;''' + src[m.end():]

# Insert Collection UI block before PickRegular block
if "EMatchFlowState::Collection" not in src:
    collect_ui = r'''
    if (Flow.State == EMatchFlowState::Collection)
    {
        DrawRect(Navy, 0, 0, Canvas->ClipX, Canvas->ClipY);
        Rect(FVector2D(120, 40), FVector2D(1680, 980), FLinearColor(.02f, .04f, .09f, .94f));
        Rect(FVector2D(120, 40), FVector2D(1680, 4), Gold);
        if (Flow.CollectionFocus < 0)
        {
            Text(TEXT("陀螺收集"), FVector2D(960, 70), 52, Cream, true);
            Text(TEXT("图鉴八格 · 全解锁 · 非出战卡池"), FVector2D(960, 140), 26, Gold, true);
            for (int32 I = 0; I < FCollectionCatalog::Count; ++I)
            {
                const FCollectionEntry& E = FCollectionCatalog::Get(I);
                const FVector2D P = FLobbyClickUI::CollectSlotPos(I);
                const bool Hovered = FLobbyClickUI::Contains(P, FVector2D(FLobbyClickUI::CollectSlotW, FLobbyClickUI::CollectSlotH), Mouse.X, Mouse.Y);
                Rect(P, FVector2D(FLobbyClickUI::CollectSlotW, FLobbyClickUI::CollectSlotH), FLinearColor(.03f, .06f, .12f, .95f));
                if (Hovered) Rect(P, FVector2D(FLobbyClickUI::CollectSlotW, 4), Gold);
                if (UTexture2D* Port = Art(E.Portrait))
                    Image(E.Portrait, P + FVector2D(16, 12), FVector2D(148, 148));
                else
                    Text(TEXT("立绘占位"), P + FVector2D(90, 70), 20, Cream, true);
                Text(E.NameZh, P + FVector2D(90, 168), 22, Cream, true);
                Text(TypeName(E.Type), P + FVector2D(90, 196), 18, TypeColor(E.Type), true);
            }
            Button(TEXT("LobbyButton"), FLobbyClickUI::CollectBackPos(), FLobbyClickUI::BackW, TEXT("返回"));
        }
        else
        {
            const FCollectionEntry& E = FCollectionCatalog::Get(Flow.CollectionFocus);
            Text(TEXT("收集详情"), FVector2D(960, 70), 48, Cream, true);
            Rect(FVector2D(420, 160), FVector2D(1080, 700), FLinearColor(.025f, .05f, .10f, .96f));
            Rect(FVector2D(420, 160), FVector2D(1080, 4), Gold);
            if (UTexture2D* Port = Art(E.Portrait))
                Image(E.Portrait, FVector2D(480, 220), FVector2D(420, 420));
            else
                Text(TEXT("立绘占位"), FVector2D(690, 400), 32, Gold, true);
            Text(E.NameZh, FVector2D(1100, 240), 48, Cream);
            Text(TypeName(E.Type), FVector2D(1100, 310), 28, TypeColor(E.Type));
            Text(TEXT("品级  Grade1"), FVector2D(1100, 360), 26, Gold);
            Text(E.DescZh, FVector2D(1100, 430), 24, Cream);
            Text(TEXT("收集图鉴 ≠ 五卡出战池"), FVector2D(1100, 560), 22, FLinearColor(.7f, .75f, .8f));
            Button(TEXT("LobbyButton"), FLobbyClickUI::CollectDetailBackPos(), FLobbyClickUI::BackW, TEXT("返回"));
        }
        return;
    }

'''
    marker = "if (Flow.State == EMatchFlowState::PickRegular || Flow.State == EMatchFlowState::BlindPick)"
    if marker not in src:
        raise SystemExit("pick marker missing")
    src = src.replace(marker, collect_ui + marker, 1)

# Fighting skill button
if "SkillBtnPos" not in src:
    fight_old = '''    else if (Flow.State == EMatchFlowState::Fighting)
    {
        const float Ratio1 = FMath::Clamp(static_cast<float>(Sim.Spin[0] / FBattleSimulation::SpinStart), 0.f, 1.f);
        const float Ratio2 = FMath::Clamp(static_cast<float>(Sim.Spin[1] / FBattleSimulation::SpinStart), 0.f, 1.f);
        Rect(FVector2D(180, 112), FVector2D(360 * Ratio1, 5), FLinearColor(1, .43f, .32f));
        Rect(FVector2D(1380 + 360 * (1 - Ratio2), 112), FVector2D(360 * Ratio2, 5), FLinearColor(.36f, .73f, 1));
        Text(TEXT("R 键回大厅"), FVector2D(960, 1030), 22, Cream, true);
    }'''
    # Chinese may be garbled - match by structure
    m = re.search(
        r'else if \(Flow\.State == EMatchFlowState::Fighting\)\s*\{.*?Text\([^;]+;\s*\}',
        src,
        flags=re.S,
    )
    if not m:
        raise SystemExit("fighting block missing")
    fight_new = '''else if (Flow.State == EMatchFlowState::Fighting)
    {
        const float Ratio1 = FMath::Clamp(static_cast<float>(Sim.Spin[0] / FBattleSimulation::SpinStart), 0.f, 1.f);
        const float Ratio2 = FMath::Clamp(static_cast<float>(Sim.Spin[1] / FBattleSimulation::SpinStart), 0.f, 1.f);
        Rect(FVector2D(180, 112), FVector2D(360 * Ratio1, 5), FLinearColor(1, .43f, .32f));
        Rect(FVector2D(1380 + 360 * (1 - Ratio2), 112), FVector2D(360 * Ratio2, 5), FLinearColor(.36f, .73f, 1));
        // Active skill shell (v2): always visible; gray=progress, bright=ready; never auto-fire.
        {
            const FActiveSkillShell& Sk = Mode->GetSkillShell();
            const FVector2D SP = FLobbyClickUI::SkillBtnPos();
            const ESkillButtonState St = Sk.State();
            const bool Ready = St == ESkillButtonState::Ready;
            const bool Fx = St == ESkillButtonState::ActiveFx;
            const float Bright = Ready ? 1.f : (Fx ? .75f : .42f);
            Rect(SP, FVector2D(FLobbyClickUI::SkillBtnW, FLobbyClickUI::SkillBtnH),
                 FLinearColor(.08f * Bright, .12f * Bright, .18f * Bright, .92f));
            Rect(SP, FVector2D(FLobbyClickUI::SkillBtnW, 4), Ready ? Gold : (Fx ? FLinearColor(.4f, .8f, 1.f) : FLinearColor(.35f, .35f, .4f)));
            Text(Sk.LabelZh(), SP + FVector2D(60, 28), 28, Ready || Fx ? Cream : FLinearColor(.55f, .55f, .6f), true);
            if (Fx)
                Text(FString::Printf(TEXT("%.1fs"), Sk.FxRemainSec), SP + FVector2D(60, 70), 20, Gold, true);
            else
                Text(FString::Printf(TEXT("%d/%d"), Sk.HitsDealt, Sk.Need()), SP + FVector2D(60, 70), 22, Ready ? Gold : Cream, true);
            if (Ready) Text(TEXT("可释放"), SP + FVector2D(60, -28), 18, Gold, true);
        }
        Text(TEXT("R 回大厅"), FVector2D(960, 1030), 22, Cream, true);
    }'''
    src = src[:m.start()] + fight_new + src[m.end():]

p.write_text(src, encoding="utf-8")
print("ArtHUD patched")
print("Collection:", "EMatchFlowState::Collection" in src)
print("SkillBtn:", "SkillBtnPos" in src)
print("Collect lobby:", "CollectPos" in src)
