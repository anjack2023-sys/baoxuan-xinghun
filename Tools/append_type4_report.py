# -*- coding: utf-8 -*-
from pathlib import Path
p = Path(r"C:\BeybladeUE\docs\reports\TYPE4-BALANCE-LANDING-2026-10-27.md")
t = p.read_text(encoding="utf-8") if p.exists() else ""
marker = "## Source 落地追加（执行器 2026-10-27）"
if marker in t:
    print("already appended")
else:
    a = (
        "\n\n" + marker + "\n\n"
        "见 `docs/GROK-ART-PROGRESS.md` TYPE4 段。\n\n"
        "Automation `Saved/Automation/GrokArt-Type4/index.json`: **13/13 Success**"
        "（含 FrozenConstants + Grade1DataLanding）。\n\n"
        "源码文件：\n"
        "- `Source/BeybladePrototype/BattleSimulation.h` — EBeyType::Balance=3；TypeLabel BALANCE\n"
        "- `Source/BeybladePrototype/Grade1Balance.h` — Rows[4]；ParseType BALANCE/BAL；内置 1.10/1.10/1.05/0.135；G1_BAL_*\n"
        "- `Source/BeybladePrototype/ArtHUD.cpp` — TypeName 攻击型/防御型/持久型/均衡型（无「耐力」）；五卡中文名；PortraitHengren\n"
        "- `Source/BeybladePrototype/MatchFlow.h` — ChiFeng-ATK / BiLei-DEF / ChangXuan-STA / HengRen-BAL / ChiWen-ATK\n"
        "- `Source/BeybladePrototype/PrototypeBattle.cpp` — ImportedBeys 五槽；ApplyBeyArt slot 对齐（衡刃 SM_Hengren）\n"
        "- `Source/BeybladePrototype/BattleSimulationTest.cpp` — BAL 断言；STA mass 最高；衰减 ATK>BAL>DEF>STA；Feel 冻结不动\n\n"
        "备份：`Saved/Backups/before_type4_balance_20261027_051603/`\n"
        "Feel85 / FeelRef60 未碰。\n"
    )
    p.write_text(t + a, encoding="utf-8")
    print("appended ok", p.stat().st_size)
prog = Path(r"C:\BeybladeUE\docs\GROK-ART-PROGRESS.md")
print("PROGRESS exists", prog.exists(), prog.stat().st_size if prog.exists() else 0)
