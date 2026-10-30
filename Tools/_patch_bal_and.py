# -*- coding: utf-8 -*-
from pathlib import Path
import re
root = Path(r"C:\BeybladeUE\Source\BeybladePrototype")

# Patch SkillRuntime WindowHitSec to require bey AND wall
sk = (root / "SkillRuntime.h").read_text(encoding="utf-8")
sk = sk.replace(
    "\tbool bWindowGotHit = false;",
    "\tbool bWindowGotBey = false;\n\tbool bWindowGotWall = false;",
)
sk = sk.replace(
    "\t\tbWindowGotHit = false;",
    "\t\tbWindowGotBey = bWindowGotWall = false;",
)
# State check
sk = sk.replace(
'''\t\tcase ESkillCondition::WindowHitSec:
\t\t\tif (bWindowGotHit && WindowSec <= Need() + 1.e-6) return ESkillButtonState::Ready;
\t\t\tbreak;''',
'''\t\tcase ESkillCondition::WindowHitSec:
\t\t\tif (bWindowGotBey && bWindowGotWall && WindowSec <= Need() + 1.e-6) return ESkillButtonState::Ready;
\t\t\tbreak;''',
)
# Observe window branch
sk = sk.replace(
'''\t\tcase ESkillCondition::WindowHitSec:
\t\t\tWindowSec += Dt;
\t\t\tif (bContact) bWindowGotHit = true;
\t\t\tif (!bWindowGotHit && WindowSec > Need())
\t\t\t{
\t\t\t\t// Missed window — restart
\t\t\t\tWindowSec = 0.0;
\t\t\t\tbWindowGotHit = false;
\t\t\t}
\t\t\tbreak;''',
'''\t\tcase ESkillCondition::WindowHitSec:
\t\t\t// CSV window_hit_bey_and_wall: need bey AND wall each >=1 within N seconds.
\t\t\tWindowSec += Dt;
\t\t\tif (Delta > 0) bWindowGotBey = true;
\t\t\tif (bWall) bWindowGotWall = true;
\t\t\tif (!(bWindowGotBey && bWindowGotWall) && WindowSec > Need())
\t\t\t{
\t\t\t\tWindowSec = 0.0;
\t\t\t\tbWindowGotBey = bWindowGotWall = false;
\t\t\t}
\t\t\tbreak;''',
)
# TryFire clear
sk = sk.replace(
    "\t\tbWindowGotHit = false;\n\t\tTier = FMath::Min",
    "\t\tbWindowGotBey = bWindowGotWall = false;\n\t\tTier = FMath::Min",
)
# ProgressLabel
sk = sk.replace(
'''\t\tcase ESkillCondition::WindowHitSec:
\t\t\tif (bWindowGotHit) return FString::Printf(TEXT("已撞 %.0f/%ds"), WindowSec, N);
\t\t\treturn FString::Printf(TEXT("需撞 %.0f/%ds"), WindowSec, N);''',
'''\t\tcase ESkillCondition::WindowHitSec:
\t\t\treturn FString::Printf(TEXT("螺%d墙%d %.0f/%ds"), bWindowGotBey ? 1 : 0, bWindowGotWall ? 1 : 0, WindowSec, N);''',
)
# Comment update
sk = sk.replace(
    " * BAL: window_hit — land bey-or-wall hit within N seconds 5/10/15/20",
    " * BAL: window_hit_bey_and_wall — bey AND wall each >=1 within N seconds 5/10/15/20",
)
(root / "SkillRuntime.h").write_text(sk, encoding="utf-8")
print("SkillRuntime and-wall", "bWindowGotBey" in sk and "bWindowGotWall" in sk)
print("old bWindowGotHit left?", "bWindowGotHit" in sk)

# Fix test for BAL and
tpath = root / "BattleSimulationTest.cpp"
t = tpath.read_text(encoding="utf-8")
old_bal = '''\t// BAL window hit within N seconds
\tFActiveSkillShell Bal;
\tBal.ConfigureForPoolSlot(3, EBeyType::Balance);
\tTestEqual(TEXT("bal window cond"), (int32)Bal.Condition, (int32)ESkillCondition::WindowHitSec);
\tBal.Observe(1.0, 0, false);
\tTestFalse(TEXT("bal no hit yet"), Bal.CanFire());
\tBal.Observe(0.0, 1, true); // wall or bey hit inside window
\tTestEqual(TEXT("bal ready after hit"), (int32)Bal.State(), (int32)ESkillButtonState::Ready);
\tTestTrue(TEXT("bal fire"), Bal.TryFire());
\tTestEqual(TEXT("bal next need 10s"), Bal.Need(), 10);'''
new_bal = '''\t// BAL window: bey AND wall each >=1 within N seconds (not OR)
\tFActiveSkillShell Bal;
\tBal.ConfigureForPoolSlot(3, EBeyType::Balance);
\tTestEqual(TEXT("bal window cond"), (int32)Bal.Condition, (int32)ESkillCondition::WindowHitSec);
\tBal.Observe(1.0, 0, false);
\tTestFalse(TEXT("bal no hit yet"), Bal.CanFire());
\tBal.Observe(0.0, 1, false); // bey only
\tTestFalse(TEXT("bal bey alone not enough"), Bal.CanFire());
\tBal.Observe(0.0, 1, true); // wall too (same hit count)
\tTestEqual(TEXT("bal ready bey+wall"), (int32)Bal.State(), (int32)ESkillButtonState::Ready);
\tTestTrue(TEXT("bal fire"), Bal.TryFire());
\tTestEqual(TEXT("bal next need 10s"), Bal.Need(), 10);'''
if old_bal in t:
    t = t.replace(old_bal, new_bal)
    print("BAL test updated")
else:
    print("WARN bal test block not exact")
    # try looser
    if "bal ready after hit" in t:
        t = t.replace("Bal.Observe(0.0, 1, true); // wall or bey hit inside window",
                      "Bal.Observe(0.0, 1, false); // bey only\n\tTestFalse(TEXT(\"bal bey alone not enough\"), Bal.CanFire());\n\tBal.Observe(0.0, 1, true); // +wall")
        t = t.replace("bal ready after hit", "bal ready bey+wall")
        print("BAL test fuzzy updated")
tpath.write_text(t, encoding="utf-8")
print("done")
