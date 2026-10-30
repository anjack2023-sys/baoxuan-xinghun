#include "FeelLabTypePresets.h"
#include "MobileUX.h"
#include "PrototypeBattle.h"
#include "CanvasItem.h"
#include "GlobalRenderResources.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "Engine/Texture2D.h"
#include "Fonts/SlateFontInfo.h"
#include "Misc/Paths.h"

namespace
{
const FLinearColor Cream(.957f, .925f, .851f, 1.f);
const FLinearColor Gold(.847f, .710f, .420f, 1.f);
const FLinearColor Navy(.063f, .122f, .220f, 1.f);

const TCHAR* TypeName(EBeyType Type)
{
    switch (Type)
    {
    case EBeyType::Defense: return TEXT("防御型");
    case EBeyType::Stamina: return TEXT("持久型");
    case EBeyType::Balance: return TEXT("均衡型");
    default: return TEXT("攻击型");
    }
}

FLinearColor TypeColor(EBeyType Type)
{
    switch (Type)
    {
    case EBeyType::Defense: return FLinearColor(.26f, .66f, .95f);
    case EBeyType::Stamina: return FLinearColor(.31f, .79f, .52f);
    case EBeyType::Balance: return FLinearColor(.85f, .72f, .28f);
    default: return FLinearColor(.96f, .35f, .24f);
    }
}
const TCHAR* BeyName(int32 Index)
{
    const TCHAR* Names[] = {TEXT("赤锋"), TEXT("壁垒"), TEXT("长旋"), TEXT("衡刃"), TEXT("炽纹"), TEXT("煌铠"), TEXT("翠磐"), TEXT("霜环")};
    return Names[FMath::Clamp(Index, 0, FPickRegular::PoolSize-1)];
}
}

UTexture2D* APrototypeBattleHUD::Art(const TCHAR* Name)
{
    const FName Key(Name);
    if (const auto* Found = UIArt.Find(Key)) return Found->Get();
    const FString Path = FString::Printf(TEXT("/Game/Beyblade/UI/P3/T_%s.T_%s"), Name, Name);
    UTexture2D* Texture = LoadObject<UTexture2D>(nullptr, *Path);
    UIArt.Add(Key, Texture);
    if (!Texture) UE_LOG(LogTemp, Warning, TEXT("P3_UI_MISSING %s"), *Path);
    return Texture;
}

void APrototypeBattleHUD::DrawGameHUD()
{
    const auto* Mode = GetWorld()->GetAuthGameMode<APrototypeBattleMode>();
    if (!Canvas || !Mode) return;
    if (Mode->IsAutomationBypass())
    {
        DrawRect(FLinearColor(.015f, .02f, .03f, .88f), 16, 16, FMath::Min(760.f, Canvas->ClipX - 32.f), 128);
        DrawText(Mode->Status(), Cream, 30, 35, GEngine->GetMediumFont());
        DrawText(TEXT("SPACE: launch / rematch   R: ready  |  AUTO"), Cream, 30, 80, GEngine->GetSmallFont());
        return;
    }

    const FMatchFlow& Flow = Mode->GetMatchFlow();
    const TCHAR* Portraits[] = {TEXT("PortraitChifeng"), TEXT("PortraitBilei"), TEXT("PortraitChangxuan"), TEXT("PortraitHengren"), TEXT("PortraitChiwen"), TEXT("PortraitHuangkai"), TEXT("PortraitCuipan"), TEXT("PortraitShuanghuan")};
    const FBattleSimulation& Sim = Mode->GetSimulation();
    const FVector2D Viewport(Canvas->ClipX, Canvas->ClipY);
    const float Scale = FLobbyClickUI::ScaleFor(Viewport);
    const FVector2D Origin = FLobbyClickUI::ViewOrigin(Viewport);
    auto Rect = [&](FVector2D Pos, FVector2D Size, FLinearColor Color)
    {
        const FVector2D P = Origin + Pos * Scale;
        DrawRect(Color, P.X, P.Y, Size.X * Scale, Size.Y * Scale);
    };
    auto Image = [&](const TCHAR* Name, FVector2D Pos, FVector2D Size, FLinearColor Tint = FLinearColor::White)
    {
        UTexture2D* Texture = Art(Name);
        if (!Texture) return;
        if (FString(Name).StartsWith(TEXT("Portrait")))
        {
            const float Fit = FMath::Min(Size.X / Texture->GetSizeX(), Size.Y / Texture->GetSizeY());
            const FVector2D Fitted(Texture->GetSizeX() * Fit, Texture->GetSizeY() * Fit);
            Pos += (Size - Fitted) * .5f;
            Size = Fitted;
        }
        const FVector2D P = Origin + Pos * Scale;
        DrawTexture(Texture, P.X, P.Y, Size.X * Scale, Size.Y * Scale, 0, 0, 1, 1, Tint, BLEND_Translucent);
    };
    auto Text = [&](const FString& Label, FVector2D Pos, float Size, FLinearColor Color, bool Center = false)
    {
        if (!RuntimeFont)
        {
            RuntimeFont = NewObject<UFont>(this);
            RuntimeFont->FontCacheType = EFontCacheType::Runtime;
        }
        static const FSlateFontInfo BaseFont(MakeShared<FCompositeFont>(FName(TEXT("Regular")),
            FPaths::EngineContentDir() / TEXT("Slate/Fonts/DroidSansFallback.ttf"), EFontHinting::Default, EFontLoadingPolicy::LazyLoad), 32);
        FSlateFontInfo Font = BaseFont;
        Font.Size = FMath::Max(1, FMath::RoundToInt(Size * Scale * (MobileUX::Enabled()? .95f : .75f)));
        FCanvasTextItem Item(Origin + Pos * Scale, FText::FromString(Label), Font, Color);
        Item.Font = RuntimeFont;
        Item.bCentreX = Center;
        if (Color.R > .5f) Item.EnableShadow(FLinearColor(0, 0, 0, .7f));
        Canvas->DrawItem(Item);
    };
    FVector2D Mouse(-1, -1);
    if (auto* PC = GetOwningPlayerController())
    {
        float X = 0, Y = 0;
        if (PC->GetMousePosition(X, Y)) Mouse = FLobbyClickUI::FromViewport(FVector2D(X, Y), Viewport);
    }
    auto Button = [&](const TCHAR* Texture, FVector2D Pos, float W, const FString& Label = FString(), bool Enabled = true, bool Selected = false)
    {
        const bool Hovered = Enabled && FLobbyClickUI::Contains(Pos, FVector2D(W, FLobbyClickUI::BtnH), Mouse.X, Mouse.Y);
        const float Brightness = Enabled ? (Hovered || Selected ? 1.f : .86f) : .42f;
        if (Texture[0] && !(FString(Texture)==TEXT("LobbyButton") && !Label.IsEmpty())) Image(Texture, Pos, FVector2D(W, FLobbyClickUI::BtnH), FLinearColor(Brightness, Brightness, Brightness, Enabled ? 1.f : .65f));
        else
        {
            const FLinearColor Background = !Enabled ? FLinearColor(.025f,.045f,.075f,.88f)
                : Selected ? FLinearColor(.12f,.22f,.34f,.98f)
                : Hovered ? FLinearColor(.08f,.15f,.24f,.97f) : FLinearColor(.04f,.08f,.15f,.95f);
            Rect(Pos,FVector2D(W,FLobbyClickUI::BtnH),Background);
            Rect(Pos,FVector2D(W,Selected || Hovered ? 4 : 2),Enabled ? Gold : FLinearColor(.30f,.30f,.30f));
            if (Selected) Rect(Pos+FVector2D(0,4),FVector2D(4,FLobbyClickUI::BtnH-4),Gold);
        }
        if (!Label.IsEmpty()) Text(Label, Pos + FVector2D(W * .5f, 26), 32, Enabled ? Cream : FLinearColor(.55f, .55f, .55f), true);
        if (Selected || Hovered) Rect(Pos + FVector2D(38, 101), FVector2D(W - 76, 3), Gold);
    };

    auto AvatarPanel = [&]()
    {
        if (!Mode->HasAvatarSelection() || Flow.State != EMatchFlowState::Lobby) return;
        Rect(FVector2D(1080, 165), FVector2D(640, 460), FLinearColor(.015f,.03f,.06f,.86f));
        Rect(FVector2D(1080, 165), FVector2D(640, 3), Gold);
        Text(TEXT("选择出战角色"), FVector2D(1120, 185), 42, Cream);
        const TCHAR* Names[]={TEXT("白龙娘"),TEXT("黑曜血姬"),TEXT("蓝色大肥鱼"),TEXT("豆姐"),TEXT("男主"),TEXT("女主")};
        for(int32 I=0;I<6;++I)
            Button(TEXT(""),FLobbyClickUI::AvatarPos(I),FLobbyClickUI::AvatarW,Names[I],true,Mode->GetSelectedAvatar()==I);
    };
    if (!Mode->GetBattleError().IsEmpty())
    {
        Rect(FVector2D(100, 380), FVector2D(1720, 220), FLinearColor(.025f, .035f, .055f, .96f));
        Text(TEXT("场地载入失败"), FVector2D(140, 410), 42, FLinearColor(1, .35f, .25f));
        Text(Mode->GetBattleError(), FVector2D(140, 490), 24, Cream);
        return;
    }

    if (Mode->IsArenaExploring())
    {
        AvatarPanel();
        if (MobileUX::Enabled()) Button(TEXT(""),MobileUX::StartButton(),260,TEXT("开始对战"),true,false);
        Rect(FVector2D(70, 55), FVector2D(750, 170), FLinearColor(.015f, .03f, .06f, .82f));
        Rect(FVector2D(70, 55), FVector2D(4, 170), Gold);
        Text(TEXT("星魂竞技场"), FVector2D(105, 72), 46, Cream);
        Text(TEXT("抢8分 · 本地体验"), FVector2D(105, 142), 27, Gold);
        Rect(FVector2D(400, 970), FVector2D(1120, 65), FLinearColor(.015f, .03f, .06f, .8f));
        Text(MobileUX::Enabled() ? TEXT("选择角色，然后点击开始对战") : Mode->HasAvatarSelection() ? TEXT("选择角色 · WASD 行走 · Shift 跑动 · 右键转视角 · E / 空格 对战") : TEXT("WASD 行走 · Shift 跑动 · C 切换AI角色 · 按住鼠标右键转视角 · E / 空格 开始对战 · R 返回训练馆"), FVector2D(960, 990), 25, Cream, true);
        return;
    }
    const bool Menu = Flow.State == EMatchFlowState::Lobby || Flow.State == EMatchFlowState::PickRegular || Flow.State == EMatchFlowState::BlindPick;
    if (Flow.State == EMatchFlowState::Lobby)
    {
        Rect(FVector2D(90, 140), FVector2D(710, 850), FLinearColor(.015f, .03f, .06f, .80f));
        Rect(FVector2D(90, 140), FVector2D(4, 850), Gold);
    }
    else if (Menu)
    {
        Image(TEXT("Lobby"), FVector2D(0, 0), FVector2D(1920, 1080));
        Rect(FVector2D(0, 0), FVector2D(1920, 1080), FLinearColor(.008f, .015f, .035f, .32f));
        Rect(FVector2D(100, 210), FVector2D(1200, 640), FLinearColor(.015f, .03f, .07f, .64f));
        Rect(FVector2D(100, 210), FVector2D(1200, 2), Gold);
    }

    if (Flow.State == EMatchFlowState::Lobby)
    {
        Text(TEXT("爆旋星魂"), FVector2D(140, 165), 88, Cream);
        Text(TEXT("BEYBLADE  /  TRAINING HALL"), FVector2D(145, 280), 27, Gold);
        Rect(FVector2D(145, 343), FVector2D(96, 5), Gold);
        Text(TEXT("训练馆大厅 · 选择赛制开始对战"), FVector2D(145, 390), 32, Cream);
        Button(TEXT("Race5"), FLobbyClickUI::Race5Pos(), FLobbyClickUI::BtnW, FString(), true, Flow.Mode == ERaceMode::RaceTo5);
        Button(TEXT("Race8"), FLobbyClickUI::Race8Pos(), FLobbyClickUI::BtnW, FString(), true, Flow.Mode == ERaceMode::RaceTo8);
        Button(TEXT("Start"), FLobbyClickUI::StartPos(), FLobbyClickUI::StartW);
        Button(TEXT(""), FLobbyClickUI::CollectPos(), FLobbyClickUI::BtnW, TEXT("收集"));
        Button(TEXT(""), FLobbyClickUI::ArenaPos(), FLobbyClickUI::BtnW, TEXT("竞技场 [E]"));
        Text(MobileUX::Enabled()?TEXT("点击开始，选择出场阵容"):TEXT("空格开始  ·  F11 手感设置"), FVector2D(145, 920), 23, Cream);
        AvatarPanel();
        Text(TEXT("中央训练盘 · 教学区域规划中"), FVector2D(1340, 940), 24, Gold, true);
        return;
    }

    
    if (Flow.State == EMatchFlowState::Collection)
    {
        Image(TEXT("Lobby"), FVector2D(0, 0), FVector2D(1920, 1080));
        Rect(FVector2D(0, 0), FVector2D(1920, 1080), FLinearColor(.008f, .015f, .035f, .58f));
        Rect(FVector2D(120, 40), FVector2D(1680, 980), FLinearColor(.015f, .03f, .07f, .86f));
        Rect(FVector2D(120, 40), FVector2D(1680, 4), Gold);
        if (Flow.CollectionFocus < 0)
        {
            Text(TEXT("陀螺收集"), FVector2D(960, 70), 52, Cream, true);
            Text(TEXT("图鉴八格 · 点击查看详情"), FVector2D(960, 140), 26, Gold, true);
            for (int32 I = 0; I < FCollectionCatalog::Count; ++I)
            {
                const FCollectionEntry& E = FCollectionCatalog::Get(I);
                const FVector2D P = FLobbyClickUI::CollectSlotPos(I);
                const bool Hovered = FLobbyClickUI::Contains(P, FVector2D(FLobbyClickUI::CollectSlotW, FLobbyClickUI::CollectSlotH), Mouse.X, Mouse.Y);
                Rect(P, FVector2D(FLobbyClickUI::CollectSlotW, FLobbyClickUI::CollectSlotH), FLinearColor(.03f, .06f, .12f, .95f));
                Rect(P, FVector2D(FLobbyClickUI::CollectSlotW, Hovered ? 4 : 2), Gold);
                if (UTexture2D* Port = Art(E.Portrait))
                    Image(E.Portrait, P + FVector2D(16, 12), FVector2D(248, 220));
                else
                    Text(TEXT("立绘占位"), P + FVector2D(140, 100), 20, Cream, true);
                Text(E.NameZh, P + FVector2D(140, 242), 22, Cream, true);
                Text(TypeName(E.Type), P + FVector2D(140, 272), 18, TypeColor(E.Type), true);
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
                Image(E.Portrait, FVector2D(480, 200), FVector2D(420, 600));
            else
                Text(TEXT("立绘占位"), FVector2D(690, 400), 32, Gold, true);
            Text(E.NameZh, FVector2D(1100, 240), 48, Cream);
            Text(TypeName(E.Type), FVector2D(1100, 310), 28, TypeColor(E.Type));
            Text(TEXT("品级  Grade1"), FVector2D(1100, 360), 26, Gold);
            Text(E.DescZh, FVector2D(1100, 430), 24, Cream);
            const auto Passive=SkillBalance::Get(E.Id,TEXT("passive"));
            const auto Active=SkillBalance::Get(E.Id,TEXT("active"));
            const auto Info=SkillBalance::PassiveInfo(E.Id);
            Text(TEXT("天赋 · ")+Passive.Name,FVector2D(970,480),23,Gold);
            Text(SkillBalance::EffectLabel(Passive),FVector2D(970,516),18,Cream);
            Text(FString(TEXT("被动 · "))+Info.Name,FVector2D(970,557),23,Gold);
            Text(Info.Line1,FVector2D(970,593),18,Cream);
            Text(Info.Line2,FVector2D(970,623),18,Cream);
            Text(TEXT("主动 · ")+Active.Name,FVector2D(970,665),24,Gold);
            Text(SkillBalance::EffectLabel(Active),FVector2D(970,701),20,Cream);
            Text(TEXT("图鉴展示 · 出战范围沿用现有八卡池"),FVector2D(970,758),20,FLinearColor(.7f,.75f,.8f));
            Button(TEXT("LobbyButton"), FLobbyClickUI::CollectDetailBackPos(), FLobbyClickUI::BackW, TEXT("返回"));
        }
        return;
    }

if (Flow.State == EMatchFlowState::PickRegular || Flow.State == EMatchFlowState::BlindPick)
    {
        const bool Blind = Flow.State == EMatchFlowState::BlindPick;
        int32 Preview = Blind && Flow.bBlindRevealed ? FMath::Max(0, Flow.BlindChoiceP1)
            : !Blind && Flow.Pick.Count > 0 ? Flow.Pick.Lineup[Flow.Pick.Count - 1] : 0;
        Text(Blind ? TEXT("盲选出场") : TEXT("选择出场阵容"), FVector2D(700, 48), 58, Cream, true);
        Text(Blind ? (Flow.bBlindRevealed ? TEXT("双方已锁定 · 同时揭晓") : TEXT("选择未使用的陀螺 · 锁定后同时揭晓"))
                   : (Flow.Pick.Required == 5 ? TEXT("八选五 · 点击顺序就是出场顺序") : TEXT("八选三 · 点击顺序就是出场顺序")), FVector2D(700, 128), 30, Gold, true);
        Text(FString::Printf(TEXT("%s    |    %d : %d"), Flow.ModeLabel(), Flow.Score[0], Flow.Score[1]), FVector2D(700, 175), 24, Cream, true);
        for (int32 I = 0; I < FPickRegular::PoolSize; ++I)
        {
            const FVector2D P = FLobbyClickUI::SlotPos(I);
            const bool Used = Blind && Flow.IsPoolUsed(I);
            const int32 Order = Blind ? 0 : Flow.Pick.OrderOf(I);
            // Never read or render the opponent's choice before simultaneous reveal.
            const bool P1 = Blind && Flow.BlindChoiceP1 == I;
            const bool P2 = Blind && Flow.bBlindRevealed && Flow.BlindChoiceP2 == I;
            const bool Selected = Order > 0 || P1 || P2;
            if (FLobbyClickUI::Contains(P, FVector2D(160, 200), Mouse.X, Mouse.Y)) Preview = I;
            Rect(P + FVector2D(10, 10), FVector2D(140, 180), FLinearColor(.025f, .05f, .10f, .9f));
            if (Blind && !Used && !Flow.bBlindRevealed)
                Image(TEXT("Blind"), P, FVector2D(160, 200), FLinearColor(1, 1, 1, Selected ? 1.f : .72f));
            else
            {
                Image(Used ? TEXT("SlotUsed") : Selected ? TEXT("SlotSelected") : TEXT("SlotEmpty"), P, FVector2D(160, 200));
                if (!Used)
                {
                    Rect(P + FVector2D(18, 26), FVector2D(124, 118), Navy);
                    if (Portraits[I]) Image(Portraits[I], P + FVector2D(6, 4), FVector2D(148, 148));
                    else Text(TEXT("立绘待补"), P + FVector2D(80, 78), 21, Cream, true);
                    Rect(P + FVector2D(15, 154), FVector2D(130, 30), Navy);
                    Text(Selected ? TEXT("已选") : TEXT("待选"), P + FVector2D(80, 154), 24, Selected ? Gold : Cream, true);
                }
            }
            if (Order > 0 && Order <= 3) Image(*FString::Printf(TEXT("Order%d"), Order), P + FVector2D(2, 2), FVector2D(48, 48));
            else if (Order > 3) Text(FString::FromInt(Order), P + FVector2D(24, 4), 30, Gold, true);
            if (Blind && (P1 || P2) && !Used)
                Text(P1 ? TEXT("P1") : TEXT("P2"), P + FVector2D(80, -32), 24, Gold, true);
            Text(BeyName(I), P + FVector2D(80, 216), 21,
                 Used ? FLinearColor(.45f, .48f, .55f) : Cream, true);
            Text(TypeName(Flow.Pick.Pool[I].Type), P + FVector2D(80, 248), 19, Used ? FLinearColor(.45f, .48f, .55f) : Cream, true);
            Rect(P + FVector2D(40, 278), FVector2D(80, 3), Used ? FLinearColor(.3f, .3f, .3f) : TypeColor(Flow.Pick.Pool[I].Type));
            if (!Used && FLobbyClickUI::Contains(P, FVector2D(160, 200), Mouse.X, Mouse.Y))
                Rect(P + FVector2D(25, -8), FVector2D(110, 3), Gold);
        }
        if (!Blind || Flow.bBlindRevealed)
        {
            Rect(FVector2D(1420, 245), FVector2D(400, 590), FLinearColor(.02f, .04f, .09f, .88f));
            Rect(FVector2D(1420, 245), FVector2D(400, 3), Gold);
            Text(BeyName(Preview), FVector2D(1620, 275), 30, Cream, true);
            if (Portraits[Preview]) Image(Portraits[Preview], FVector2D(1440, 345), FVector2D(360, 360));
            else Text(TEXT("立绘待补"), FVector2D(1690, 500), 30, Gold, true);
            const auto& Stats=FeelLabTypes::GetBey(Preview);
            Text(FString::Printf(TEXT("攻击 ×%.2f   减伤 %d%%"),Stats.AttackValue(),Stats.Defense),FVector2D(1620,728),20,Gold,true);
            Text(FString::Printf(TEXT("耐久 %d   自然旋转 %.0f秒"),Stats.Life,Stats.NaturalSeconds),FVector2D(1620,765),20,Cream,true);
            Text(FLaunchSetup::Style(Flow.Pick.Pool[Preview].Type), FVector2D(1620, 804), 16, Cream, true);
        }
        if (!Blind)
        {
            FString Lineup = FString::Printf(TEXT("已选 %d / %d"), Flow.Pick.Count, Flow.Pick.Required);
            for (int32 I = 0; I < Flow.Pick.Count; ++I)
                Lineup += FString::Printf(TEXT("    %d. %s"), I + 1, BeyName(Flow.Pick.Lineup[I]));
            Rect(FVector2D(260, 860), FVector2D(880, 45), FLinearColor(.015f, .03f, .07f, .85f));
            Text(Lineup, FVector2D(700, 867), Flow.Pick.Required == 5 ? 20 : 25, Cream, true);
            Button(TEXT("Confirm"), FLobbyClickUI::ConfirmPos(), FLobbyClickUI::ConfirmW, FString(), Flow.Pick.CanConfirm());
            Button(TEXT("LobbyButton"), FLobbyClickUI::BackPos(), FLobbyClickUI::BackW);
        }
        else
        {
            Text(FString::Printf(TEXT("可用 %d / 8    ·    %s"), Flow.CountUnused(), Flow.bBlindRevealed ? TEXT("已揭晓，可进入准备") : TEXT("揭晓前不显示对方选择")), FVector2D(700, 867), 27, Cream, true);
            Button(TEXT("Button"), FLobbyClickUI::LockBlindPos(), FLobbyClickUI::ConfirmW, TEXT("锁定选择"), !Flow.bBlindLockedP1 && Flow.BlindChoiceP1 >= 0);
            Button(TEXT("Button"), FLobbyClickUI::ConfirmBlindPos(), FLobbyClickUI::ConfirmW, TEXT("进入准备"), Flow.CanConfirmBlind());
            Button(TEXT("LobbyButton"), FLobbyClickUI::BlindBackPos(), FLobbyClickUI::BackW);
        }
        Text(MobileUX::Enabled()?(Flow.Pick.Required == 5 ? TEXT("点击选择五只陀螺，再点击确认出场") : TEXT("点击选择三只陀螺，再点击确认出场")):TEXT("1—8 选择  ·  空格确认  ·  R 返回大厅"), FVector2D(960, 1030), 22, Cream, true);
        return;
    }

    Rect(FVector2D(120, 28), FVector2D(1680, 108), FLinearColor(.035f, .07f, .13f, .9f));
    Rect(FVector2D(120, 134), FVector2D(1680, 3), Gold);
    Text(FString::Printf(TEXT("P1   %d"), Flow.Score[0]), FVector2D(180, 56), 38, FLinearColor(1, .43f, .32f));
    Text(FString::Printf(TEXT("%d   P2"), Flow.Score[1]), FVector2D(1600, 56), 38, FLinearColor(.36f, .73f, 1));
    Text(Flow.ModeLabel(), FVector2D(960, 48), 28, Gold, true);
    const int32 Remaining = Flow.State==EMatchFlowState::Prep ? (Mode->IsTutorialPending()?APrototypeBattleMode::TutorialSeconds:Mode->IsRankedArena()?APrototypeBattleMode::RankedBoutSeconds:120) : FMath::Max(0, FMath::CeilToInt((Sim.FrameLimit - Sim.Frames) * FBattleSimulation::Step));
    Text(FString::Printf(TEXT("%02d : %02d"), Remaining / 60, Remaining % 60), FVector2D(960, 88), 26, Cream, true);
    Text(MobileUX::Enabled()?FString(TEXT("点击右上角切换对战视角")) : Mode->IsFaceView() ? FString::Printf(TEXT("人物视角  角度 %.0f°  高度 %+.0f cm  ·  %s  ·  V 返回"), Mode->GetFacePitch(), Mode->GetFaceHeight(),
        Mode->IsFaceViewLocked() ? TEXT("已锁定 · F10 解锁") : TEXT("↑↓ 调角度 / PgUp PgDn 调高度 / F10 保存"))
        : FString(TEXT("俯视视角 · V 切换人物视角")), FVector2D(960, 160), 22, Cream, true);
    if(Mode->IsLaunching())
    {
        const double Age=Mode->GetLaunchAge();
        const FString Prompt=Age<1.6?FString(TEXT("陀螺发射"))
            :Age<FLaunchSetup::ReleaseTime?FString::FromInt(FMath::Clamp(1+FMath::FloorToInt((Age-1.6)/(1.3/3.)),1,3))
            :FString(TEXT("发射！"));
        Text(Prompt,FVector2D(960,820),95,Gold,true);
        Text(Age<FLaunchSetup::ReleaseTime?TEXT("准备 · 瞄准"):TEXT("落盘后开始计时"),FVector2D(960,930),26,Cream,true);
        return;
    }

    if (!Mode->IsLaunching() && (Flow.State == EMatchFlowState::Prep || Flow.State == EMatchFlowState::Fighting))
        for (int32 I = 0; I < 2; ++I)
        {
            const FVector Screen = Canvas->Project(Mode->GetBeyLocation(I) + FVector(0, 0, 45));
            if (Screen.Z > 0)
            {
                const FVector2D Label=FLobbyClickUI::FromViewport(FVector2D(Screen.X, Screen.Y), Viewport);
                Rect(Label-FVector2D(25,3),FVector2D(50,30),FLinearColor(.01f,.02f,.04f,.85f));
                Text(FString::Printf(TEXT("P%d"), I + 1), Label, 30,
                    I == 0 ? FLinearColor(1, .43f, .32f) : FLinearColor(.36f, .73f, 1), true);
            }
        }

    if (Flow.State == EMatchFlowState::Prep)
    {
        Rect(FVector2D(480, 715), FVector2D(960, 140), FLinearColor(.035f, .07f, .13f, .9f));
        Text(Mode->IsTutorialPending()?TEXT("首次教学局 · 不计分"):TEXT("准备出场"), FVector2D(960, 735), 40, Cream, true);
        const int32 P1 = Flow.bBlindPhase ? Flow.BlindChoiceP1 : Flow.Pick.Lineup[Flow.CurrentLineupIndex];
        const int32 P2 = Flow.bBlindPhase ? Flow.BlindChoiceP2 : 1;
        Rect(FVector2D(1420, 245), FVector2D(400, 590), FLinearColor(.02f, .04f, .09f, .88f));
        Rect(FVector2D(1420, 245), FVector2D(400, 3), Gold);
        Text(TEXT("P1 本局出场"), FVector2D(1620, 275), 30, Cream, true);
        if (Portraits[P1]) Image(Portraits[P1], FVector2D(1440, 345), FVector2D(360, 360));
        else Text(TEXT("立绘待补"), FVector2D(1690, 500), 30, Gold, true);
        Text(FLaunchSetup::Style(Flow.Pick.Pool[P1].Type), FVector2D(1620, 755), 17, Cream, true);
        Rect(FVector2D(70,745),FVector2D(480,285),FLinearColor(.02f,.04f,.09f,.94f));
        Text(TEXT("发射设定"),FVector2D(310,758),30,Gold,true);
        const auto& Setup=Mode->GetLaunchSetup();
        Text(FString::Printf(TEXT("角度  %+.0f°"),double(Setup.Angle)),FVector2D(305,825),29,Cream,true);
        Text(FString::Printf(TEXT("力度  %d%%"),Setup.Power),FVector2D(305,920),29,Cream,true);
        for(int32 I=0;I<4;++I)
        {
            const FVector2D B=FLaunchSetup::Button(I);
            Rect(B,FVector2D(80,70),FLinearColor(.1f,.18f,.28f,.95f));
            Text(I%2?TEXT("+"):TEXT("-"),B+FVector2D(40,17),36,Gold,true);
        }
        Text(TEXT("力度影响初速度，不增加基础寿命"),FVector2D(310,997),19,Cream,true);
        if(Mode->IsRankedArena()) Text(TEXT("金边区域：停留会减速"),FVector2D(960,865),20,Gold,true);
        if(!Mode->IsLaunching())
        {
            const FVector2D Start=FVector2D(-1.2,-.55)*Sim.ArenaScale;
            const FVector2D Dir=(FVector2D(.55,.2)-FVector2D(-1.2,-.55)).GetSafeNormal().GetRotated(Setup.Angle);
            const FVector2D End=Start+Dir*(.45*Setup.Power/100.);
            const FVector A=Project(FVector(Start.X*100,Start.Y*100,FBattleSimulation::BowlHeight(Start.Size()/Sim.ArenaScale)*100+20));
            const FVector B=Project(FVector(End.X*100,End.Y*100,FBattleSimulation::BowlHeight(End.Size()/Sim.ArenaScale)*100+20));
            if(A.Z>0 && B.Z>0){DrawLine(A.X,A.Y,B.X,B.Y,Gold,3);DrawLine(B.X,B.Y,B.X-8,B.Y+9,Gold,3);}
        }
        Text(FString::Printf(TEXT("P1  %s     VS     P2  %s"), BeyName(P1), BeyName(P2)), FVector2D(960, 800), 29, Gold, true);
        Button(TEXT("Start"), FLobbyClickUI::PrepLaunchPos(), FLobbyClickUI::ConfirmW);
        Button(TEXT("LobbyButton"), FLobbyClickUI::BackPos(), FLobbyClickUI::BackW);
        Text(MobileUX::Enabled()?TEXT("点击开始发射"):TEXT("A/D 调角度 · W/S 调力度 · 空格开始发射"), FVector2D(960, 1030), 22, Cream, true);
    }
    else if (Flow.State == EMatchFlowState::Fighting)
    {
        // Screen-space effects follow the simulation and never affect its collision rules.
        if (Mode->IsRankedArena())
        {
            for(int32 Z=0;Z<6;++Z)
            {
                const double Angle=PI/2.+Z*PI/3.;
                const FVector2D N(FMath::Cos(Angle),FMath::Sin(Angle)),T(-N.Y,N.X),Center=N*StarCrownRim::TrapRingRadius;
                bool Occupied=false;
                for(int32 I=0;I<2;++I)
                {
                    const FVector2D D=Sim.Position[I]-Center;
                    const FVector2D Closest=T*FMath::Clamp(FVector2D::DotProduct(D,T),-StarCrownRim::TrapHalfSegment,StarCrownRim::TrapHalfSegment);
                    Occupied|=(D-Closest).SizeSquared()<=FMath::Square(StarCrownRim::TrapRadius+FBattleSimulation::Radius);
                }
                FVector Previous; bool HavePrevious=false;
                for(int32 J=0;J<=32;++J)
                {
                    const int32 Side=J<=16?1:-1; const double A=(J<=16?-PI/2.:PI/2.)+(J<=16?J:J-16)*PI/16.;
                    const FVector2D P=Center+T*(Side*StarCrownRim::TrapHalfSegment+StarCrownRim::TrapRadius*FMath::Cos(A))+N*(StarCrownRim::TrapRadius*FMath::Sin(A));
                    const FVector Screen=Project(FVector(P.X*100,P.Y*100,FBattleSimulation::BowlHeight(P.Size()/Sim.ArenaScale)*100+1.5));
                    if(HavePrevious && Screen.Z>0 && Previous.Z>0) DrawLine(Previous.X,Previous.Y,Screen.X,Screen.Y,Occupied?FLinearColor(1.f,.68f,.1f):FLinearColor(.55f,.32f,.06f),Occupied?3.f*Scale:1.5f*Scale);
                    Previous=Screen;HavePrevious=true;
                }
                if(Occupied)
                {
                    const FVector C=Project(FVector(Center.X*100,Center.Y*100,FBattleSimulation::BowlHeight(Center.Size()/Sim.ArenaScale)*100+5));
                    if(C.Z>0) for(int32 J=0;J<4;++J)
                    {
                        const double A=GetWorld()->GetTimeSeconds()*4.+J*PI/2.;
                        DrawLine(C.X+FMath::Cos(A)*12*Scale,C.Y+FMath::Sin(A)*8*Scale,
                                 C.X+FMath::Cos(A)*20*Scale,C.Y+FMath::Sin(A)*15*Scale,FLinearColor(1.f,.72f,.18f),2.f*Scale);
                    }
                }
            }
        }
        for(int32 I=0;I<2;++I)
        {
            const FVector Head=Mode->GetBeyLocation(I)+FVector(0,0,15);
            const float Life=FMath::Clamp(float(Sim.Spin[I]/FBattleSimulation::SpinStart),0.f,1.f);
            const FVector A=Project(Head);
            const TArray<FVector>& History=Mode->GetTrail(I);
            const double MaxLength=100.*(0.35+1.55*Life);
            TArray<FCanvasUVTri> TrailTriangles;
            double Distance=0.;
            FVector Newer=Head;
            for(int32 J=History.Num()-1;J>=0 && Distance<MaxLength;--J)
            {
                FVector Older=History[J];
                const double Segment=(Newer-Older).Size2D();
                if(Segment<.2) continue;
                if(Distance+Segment>MaxLength) Older=FMath::Lerp(Newer,Older,(MaxLength-Distance)/Segment);
                const double NextDistance=FMath::Min(MaxLength,Distance+Segment);
                const FVector P=Project(Newer),Q=Project(Older);
                if(P.Z>0 && Q.Z>0)
                {
                    const FVector2D Direction=FVector2D(Q.X-P.X,Q.Y-P.Y).GetSafeNormal();
                    const FVector2D Normal(-Direction.Y,Direction.X);
                    const float Near=float(Distance/MaxLength),Far=float(NextDistance/MaxLength);
                    const FLinearColor Base=I==0?FLinearColor(1.f,.12f,.04f):FLinearColor(.04f,.52f,1.f);
                    for(int32 Strand=-2;Strand<=2;++Strand)
                    {
                        const float Drift=Strand*6.f*Scale;
                        const float Time=GetWorld()->GetTimeSeconds();
                        const float W0=(3.f+4.f*Near)*Scale,W1=(3.f+4.f*Far)*Scale;
                        const float Wave0=FMath::Sin(Time*3.f+Near*12.f+Strand*2.f)*3.f*Scale*Near;
                        const float Wave1=FMath::Sin(Time*3.f+Far*12.f+Strand*2.f)*3.f*Scale*Far;
                        const FVector2D C0=FVector2D(P.X,P.Y)+Normal*(Drift*Near+Wave0);
                        const FVector2D C1=FVector2D(Q.X,Q.Y)+Normal*(Drift*Far+Wave1);
                        const float Opacity0=.25f*Life*(1.f-Near)*(1.f-Near);
                        const float Opacity1=.25f*Life*(1.f-Far)*(1.f-Far);
                        FLinearColor Edge=Base,Inner0=Base,Inner1=Base;Edge.A=0.f;Inner0.A=Opacity0;Inner1.A=Opacity1;
                        auto Triangle=[&](FVector2D X,FVector2D Y,FVector2D Z,FLinearColor CX,FLinearColor CY,FLinearColor CZ)
                        {
                            FCanvasUVTri Tri;Tri.V0_Pos=X;Tri.V1_Pos=Y;Tri.V2_Pos=Z;
                            Tri.V0_Color=CX;Tri.V1_Color=CY;Tri.V2_Color=CZ;TrailTriangles.Add(Tri);
                        };
                        Triangle(C0-Normal*W0,C0,C1-Normal*W1,Edge,Inner0,Edge);
                        Triangle(C0,C1,C1-Normal*W1,Inner0,Inner1,Edge);
                        Triangle(C0,C0+Normal*W0,C1,Inner0,Edge,Inner1);
                        Triangle(C0+Normal*W0,C1+Normal*W1,C1,Edge,Edge,Inner1);
                    }
                }
                Distance=NextDistance;Newer=Older;
            }
            if (!TrailTriangles.IsEmpty())
            {
                FCanvasTriangleItem TrailItem(TrailTriangles, GWhiteTexture);
                TrailItem.BlendMode = SE_BLEND_Translucent;
                Canvas->DrawItem(TrailItem);
            }
            const double Age=GetWorld()->GetRealTimeSeconds()-Mode->GetLastImpactTime();
            if(A.Z>0 && Age>=0. && Age<.7 && Mode->GetImpactDamage(I)>.001)
            {
                const FVector2D At=FLobbyClickUI::FromViewport(FVector2D(A.X,A.Y),Viewport)+FVector2D(0,-55-35*Age);
                Text(FString::Printf(TEXT("-%.1f"),Mode->GetImpactDamage(I)),At,24,FLinearColor(1.f,.8f,.32f,float(1.-Age/.7)),true);
            }
        }
        const float Ratio1 = FMath::Clamp(static_cast<float>(Sim.Spin[0] / FBattleSimulation::SpinStart), 0.f, 1.f);
        const float Ratio2 = FMath::Clamp(static_cast<float>(Sim.Spin[1] / FBattleSimulation::SpinStart), 0.f, 1.f);
        Rect(FVector2D(180,112),FVector2D(360,5),FLinearColor(.015f,.025f,.045f,.9f));
        Rect(FVector2D(1380,112),FVector2D(360,5),FLinearColor(.015f,.025f,.045f,.9f));
        Rect(FVector2D(180, 112), FVector2D(360 * Ratio1, 5), FLinearColor(1, .43f, .32f));
        Rect(FVector2D(1380 + 360 * (1 - Ratio2), 112), FVector2D(360 * Ratio2, 5), FLinearColor(.36f, .73f, 1));
        if (Sim.Spin[0] <= .20 * FBattleSimulation::SpinStart)
            {
            Rect(FVector2D(160,165),FVector2D(310,42),FLinearColor(.28f,.015f,.02f,.92f));
            Text(TEXT("转速过低 · 小心停转"),FVector2D(175,173),24,FLinearColor(1.f,.35f,.2f));
        }
        const float Hp1=Sim.Durability[0]/Sim.MaxDurability[0], Hp2=Sim.Durability[1]/Sim.MaxDurability[1];
        Rect(FVector2D(180,122),FVector2D(360,5),FLinearColor(.015f,.025f,.045f,.9f));
        Rect(FVector2D(1380,122),FVector2D(360,5),FLinearColor(.015f,.025f,.045f,.9f));
        Rect(FVector2D(180,122),FVector2D(360*Hp1,5),FLinearColor(.3f,1,.5f));
        Rect(FVector2D(1380+360*(1-Hp2),122),FVector2D(360*Hp2,5),FLinearColor(.3f,1,.5f));
        Text(FString::Printf(TEXT("耐久 %.0f / %.0f"),Sim.Durability[0],Sim.MaxDurability[0]),FVector2D(180,138),18,Cream);
        Text(FString::Printf(TEXT("耐久 %.0f / %.0f"),Sim.Durability[1],Sim.MaxDurability[1]),FVector2D(1560,138),18,Cream);
        if(Mode->IsTutorialBout())
        {
            Rect(FVector2D(35,625),FVector2D(555,220),FLinearColor(.015f,.035f,.07f,.94f));
            Text(TEXT("教学局 · 不计入比分"),FVector2D(55,635),24,Gold);
            Text(TEXT("金边区域：停留会减速"),FVector2D(55,675),20,Cream);
            Text(MobileUX::Enabled() ? TEXT("技能充满高亮后点击释放") : TEXT("技能充满高亮后按 Q 释放"),FVector2D(55,710),20,Cream);
            Text(TEXT("转速决定停转；耐久耗尽会爆裂"),FVector2D(55,745),20,Cream);
            Text(TEXT("超时比较剩余动量，较高者获胜"),FVector2D(55,780),20,Cream);
        }
        // Active skill shell (v2): always visible; gray=progress, bright=ready; never auto-fire.
        {
            const FActiveSkillShell& Sk = Mode->GetSkillShell();
            const FVector2D SP = FLobbyClickUI::SkillBtnPos();
            const ESkillButtonState St = Sk.State();
            const bool Ready = St == ESkillButtonState::Ready;
            const bool Fx = St == ESkillButtonState::ActiveFx;
            // Use the same readiness as firing; no independent timer can leave the flame lit.
            if (Ready)
            {
                const float Time = GetWorld()->GetTimeSeconds();
                for (int32 I = 0; I < 18; ++I)
                {
                    const float X = 8.f + I * 15.5f;
                    const float Height = 24.f + 25.f * (.5f + .5f * FMath::Sin(Time * 8.f + I * 2.3f));
                    const float Sway = 7.f * FMath::Sin(Time * 5.f + I);
                    for (int32 Layer = 0; Layer < 3; ++Layer)
                    {
                        const float Width = 15.f - Layer * 4.f;
                        const FVector2D Base = SP + FVector2D(X, 12.f);
                        const FVector2D A = Origin + (Base + FVector2D(-Width, 0)) * Scale;
                        const FVector2D B = Origin + (Base + FVector2D(Width, 0)) * Scale;
                        const FVector2D C = Origin + (Base + FVector2D(Sway, -Height * (1.f - Layer * .24f))) * Scale;
                        FCanvasUVTri Flame;
                        Flame.V0_Pos = A; Flame.V1_Pos = B; Flame.V2_Pos = C;
                        Flame.V0_Color = Flame.V1_Color = Flame.V2_Color = Layer == 0 ? FLinearColor(1.f, .12f, .015f, .48f)
                            : Layer == 1 ? FLinearColor(1.f, .48f, .025f, .8f) : FLinearColor(1.f, .88f, .35f, .95f);
                        Canvas->K2_DrawTriangle(nullptr, {Flame});
                    }
                    const float Rise = FMath::Fmod(Time * 42.f + I * 13.f, 80.f);
                    Rect(SP + FVector2D(X + Sway, -Rise), FVector2D(2, 4), FLinearColor(1.f, .65f, .12f, (1.f - Rise / 80.f) * .75f));
                }
            }
            const float Bright = Ready ? 1.f : (Fx ? .75f : .42f);
            Rect(SP, FVector2D(FLobbyClickUI::SkillBtnW, FLobbyClickUI::SkillBtnH),
                 FLinearColor(.04f * Bright, .08f * Bright, .15f * Bright, .95f));
            Rect(SP, FVector2D(FLobbyClickUI::SkillBtnW, 4), Ready ? Gold : (Fx ? FLinearColor(.4f, .8f, 1.f) : FLinearColor(.35f, .35f, .4f)));
            const TCHAR* IconIds[]={TEXT("chifeng"),TEXT("chiwen"),TEXT("bilei"),TEXT("huangkai"),TEXT("changxuan"),TEXT("cuipan"),TEXT("hengblade"),TEXT("shuanghuan")};
            int32 IconIndex=0; for(int32 I=0;I<8;++I) if(Sk.BeyId==IconIds[I]) IconIndex=I;
            if (UTexture2D* Atlas=Art(TEXT("SkillAtlas")))
            {
                const FVector2D IP=Origin+(SP+FVector2D(8,25))*Scale;
                DrawTexture(Atlas,IP.X,IP.Y,72*Scale,72*Scale,(IconIndex%4)*.25f,IconIndex<4?.1875f:.5546875f,.25f,.25f,
                    FLinearColor(Bright,Bright,Bright,1),BLEND_Translucent);
            }
            const double Progress=Ready?1.:(Sk.Condition==ESkillCondition::WindowHitSec ?
                .5*(int(Sk.bWindowGotBey)+int(Sk.bWindowGotWall)) : FMath::Clamp(Sk.ProgressValue()/Sk.Need(),0.,1.));
            const FVector2D RingCenter=Origin+(SP+FVector2D(44,61))*Scale;
            for(int32 Segment=0;Segment<32;++Segment)
            {
                const double A=-PI/2.+Segment*2.*PI/32.,B=-PI/2.+(Segment+1)*2.*PI/32.;
                const FVector2D P=RingCenter+FVector2D(FMath::Cos(A),FMath::Sin(A))*43.f*Scale;
                const FVector2D Q=RingCenter+FVector2D(FMath::Cos(B),FMath::Sin(B))*43.f*Scale;
                DrawLine(P.X,P.Y,Q.X,Q.Y,(Segment+1<=Progress*32.)?Gold:FLinearColor(.25f,.3f,.38f),3.f*Scale);
            }
            Text(Sk.LabelZh(), SP + FVector2D(180, 25), 25, Ready || Fx ? Cream : FLinearColor(.55f, .55f, .6f), true);
            if (Fx)
                Text((Sk.ActiveData.Duration==0. ? FString(TEXT("下一次碰撞")) : FString::Printf(TEXT("剩余 %.1fs"), Sk.FxRemainSec)), SP + FVector2D(180, 70), 20, Gold, true);
            else
                Text(Ready ? FString(TEXT("已就绪")) : Sk.ProgressLabel(), SP + FVector2D(180, 70), 20, Ready ? Gold : Cream, true);
            if (Ready && Sk.BeyId == TEXT("bilei"))
                Rect(SP + FVector2D(0, FLobbyClickUI::SkillBtnH - 4), FVector2D(FLobbyClickUI::SkillBtnW, 4),
                    FLinearColor(.15f, .55f, 1.f, .65f + .3f * FMath::Sin(GetWorld()->GetTimeSeconds() * 7.f)));
            if (Ready) Text(MobileUX::Enabled() ? TEXT("点击释放") : TEXT("Q 释放技能"), SP + FVector2D(140, -80), 22, Gold, true);
        }
        Text(MobileUX::Enabled() ? TEXT("点击技能按钮释放") : TEXT("Q 释放技能  ·  R 回大厅"), FVector2D(960, 1030), 22, Cream, true);
    }
    else if (Flow.State == EMatchFlowState::RoundSettle || Flow.State == EMatchFlowState::MatchSettle)
    {
        Rect(FVector2D(0, 150), FVector2D(1920, 930), FLinearColor(.01f, .02f, .04f, .55f));
        const bool Match = Flow.State == EMatchFlowState::MatchSettle;
        Image(Match ? TEXT("MatchPanel") : TEXT("RoundPanel"), Match ? FVector2D(560, 250) : FVector2D(600, 280), Match ? FVector2D(800, 480) : FVector2D(720, 420));
        if (Match)
        {
            Text(FString::Printf(TEXT("P%d  赢得比赛"), Flow.MatchWinner + 1), FVector2D(960, 430), 52, Navy, true);
            Text(FString::Printf(TEXT("%d  :  %d"), Flow.Score[0], Flow.Score[1]), FVector2D(960, 530), 70, Navy, true);
            Text(Flow.ModeLabel(), FVector2D(960, 630), 25, Navy, true);
        }
        else
        {
            const TCHAR* ReasonArt = Flow.LastWinner < 0 ? TEXT("Draw") : Flow.LastReason == TEXT("ringout") ? TEXT("Ringout")
                : Flow.LastReason == TEXT("spinout") ? TEXT("Spinout") : Flow.LastReason == TEXT("timeout") ? TEXT("Timeout") : nullptr;
            if (ReasonArt) Image(ReasonArt, FVector2D(704, 440), FVector2D(512, 77));
            else Text(FMatchFlow::ReasonLabelCN(Flow.LastReason), FVector2D(960, 450), 40, Navy, true);
            Text(FString::Printf(TEXT("P1  +%d          P2  +%d"), Flow.LastDelta.Delta[0], Flow.LastDelta.Delta[1]), FVector2D(960, 540), 34, Navy, true);
            Text(FString::Printf(TEXT("%d  :  %d"), Flow.Score[0], Flow.Score[1]), FVector2D(960, 600), 54, Navy, true);
            if (Flow.LastReason == TEXT("ringout") && Flow.LastDelta.Tag == EScoreTag::XTR)
                Image(TEXT("XTR"), FVector2D(1230, 455), FVector2D(160, 48));

        }
        Rect(FVector2D(220,675),FVector2D(1480,110),FLinearColor(.025f,.05f,.09f,.97f));
        Text((Match?FString(TEXT("末局复盘 · ")):FString())+ExplainBout(Sim),FVector2D(960,684),25,Cream,true);
        Text(FString::Printf(TEXT("用时 %.1fs · 碰螺 %d次 · 最强闭合速度 %.1f m/s · 碰墙 P1 %d / P2 %d"),Sim.Frames*FBattleSimulation::Step,Sim.Hits,Sim.PeakClosing,Sim.PlayerWallHits[0],Sim.PlayerWallHits[1]),FVector2D(960,715),20,Gold,true);
        Text(FString::Printf(TEXT("P1 发射 %d%% / %+.0f° · 主动技能 %d次 · 末局剩余转速 P1 %.1f%% / P2 %.1f%%"),Mode->GetLaunchSetup().Power,double(Mode->GetLaunchSetup().Angle),Mode->GetSkillUses(),Sim.Spin[0]*100,Sim.Spin[1]*100),FVector2D(960,753),22,Cream,true);
        if(Mode->IsTutorialBout())
            Text(TEXT("教学完成 · 不计入比分 · 继续开始正式对战"),FVector2D(960,785),19,Gold,true);
        else if(Sim.Winner==1 && Sim.Reason==TEXT("timeout"))
            Text(FString::Printf(TEXT("你的剩余动量少 %.2f；下局可尝试更早使用技能"),FMath::Max(0.,Sim.TimeoutMomentum[1]-Sim.TimeoutMomentum[0])),FVector2D(960,785),19,Gold,true);
        Button(Match ? TEXT("Rematch") : TEXT("Button"), FLobbyClickUI::NextRoundPos(), FLobbyClickUI::NextW, Match ? FString() : FString(TEXT("下一局")));
        Button(TEXT("LobbyButton"), FLobbyClickUI::ToLobbyPos(), FLobbyClickUI::BackW);
        Text(Match ? TEXT("再来一局将返回大厅重新组队") : (MobileUX::Enabled()?TEXT("点击继续下一局或回大厅"):TEXT("空格继续下一局  ·  R 返回大厅")), FVector2D(960, 955), 23, Cream, true);
    }

}

void APrototypeBattleHUD::DrawHUD()
{
    Super::DrawHUD();DrawGameHUD();DrawTuningPanel();DrawMobileControls();
}
void APrototypeBattleHUD::DrawTuningPanel()
{
    const auto* Mode=GetWorld()->GetAuthGameMode<APrototypeBattleMode>();
    if (!Canvas || !Mode || Mode->IsAutomationBypass()) return;
    const FVector2D View(Canvas->ClipX,Canvas->ClipY),Origin=FLobbyClickUI::ViewOrigin(View);
    const float Scale=FLobbyClickUI::ScaleFor(View);
    if (!RuntimeFont) {RuntimeFont=NewObject<UFont>(this);RuntimeFont->FontCacheType=EFontCacheType::Runtime;}
    auto Rect=[&](float X,float Y,float W,float H) {const auto P=Origin+FVector2D(X,Y)*Scale;DrawRect(FLinearColor(.025f,.05f,.10f,.96f),P.X,P.Y,W*Scale,H*Scale);};
    auto Text=[&](const FString& Label,float X,float Y,int32 Size=25) {
        FSlateFontInfo Font(MakeShared<FCompositeFont>(FName(TEXT("Regular")),FPaths::EngineContentDir()/TEXT("Slate/Fonts/DroidSansFallback.ttf"),EFontHinting::Default,EFontLoadingPolicy::LazyLoad),FMath::Max(1,FMath::RoundToInt(Size*Scale*.75f)));
        FCanvasTextItem Item(Origin+FVector2D(X,Y)*Scale,FText::FromString(Label),Font,Cream);Item.Font=RuntimeFont;Canvas->DrawItem(Item);
    };
    Rect(30,190,230,52);Text(Mode->IsTuningOpen()?TEXT("收起调试 [F11]"):TEXT("手感设置 [F11]"),46,202);
    if (!Mode->IsTuningOpen()) return;
    Rect(30,250,470,235);Text(TEXT("手感调试 · 实时生效"),46,264);
    Text(FString::Printf(TEXT("移动倍率  %d%%"),Mode->GetMoveLevel()),46,310);
    Text(FString::Printf(TEXT("击飞强度  %d"),Mode->GetRingoutLevel()),46,375);
    for(float Y:{300.f,365.f}) {Rect(310,Y,65,50);Rect(405,Y,65,50);Text(TEXT("−"),332,Y+8);Text(TEXT("+"),427,Y+8);}
    Text(TEXT("每次±5 · 自动保存 · 移动10–200%"),46,435,20);
    Text(TEXT("击飞0–100：强度，不代表出界概率"),46,460,19);
}

void APrototypeBattleHUD::DrawMobileControls()
{
    if(!Canvas || !MobileUX::Enabled() || !RuntimeFont)return;
    const FVector2D View(Canvas->ClipX,Canvas->ClipY);
    const float Scale=FLobbyClickUI::ScaleFor(View);
    const TCHAR* Labels[]={TEXT("切换视角"),TEXT("回大厅"),TEXT("退出")};
    for(int32 I=0;I<3;++I)
    {
        const auto P=FLobbyClickUI::ToViewport(MobileUX::Button(I),View);
        DrawRect(FLinearColor(.035f,.07f,.13f,.95f),P.X,P.Y,150*Scale,72*Scale);
        FSlateFontInfo Font(MakeShared<FCompositeFont>(FName(TEXT("Regular")),FPaths::EngineContentDir()/TEXT("Slate/Fonts/DroidSansFallback.ttf"),EFontHinting::Default,EFontLoadingPolicy::LazyLoad),FMath::Max(1,FMath::RoundToInt(26*Scale)));
        FCanvasTextItem Item(P+FVector2D(12,20)*Scale,FText::FromString(Labels[I]),Font,Cream);Item.Font=RuntimeFont;Canvas->DrawItem(Item);
    }
}

