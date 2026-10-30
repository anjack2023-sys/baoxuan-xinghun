# -*- coding: utf-8 -*-
from pathlib import Path
root = Path(r"C:\BeybladeUE\Source\BeybladePrototype")

# SkillRuntime: baseline attack restore
sk = (root / "SkillRuntime.h").read_text(encoding="utf-8")
if "BaselineAttack" not in sk:
    sk = sk.replace(
        "\tdouble RingoutRateAdd = 0.0;",
        "\tdouble RingoutRateAdd = 0.0;\n\tdouble BaselineAttack = 1.0;\n\tbool bPendingRestore = false;",
    )
    sk = sk.replace(
        "\t\tRingoutRateAdd = 0.0;\n\t\tLastSeenHits = 0;",
        "\t\tRingoutRateAdd = 0.0;\n\t\tBaselineAttack = 1.0;\n\t\tbPendingRestore = false;\n\t\tLastSeenHits = 0;",
    )
    sk = sk.replace(
        """\tdef void TickFx(double Dt)
\t{
\t\tif (!bFxActive) return;
\t\tFxRemainSec -= Dt;
\t\tif (FxRemainSec <= 0.0)
\t\t{
\t\t\tbFxActive = false;
\t\t\tFxRemainSec = 0.0;
\t\t\tAttackMulActive = 1.0;
\t\t\tRingoutRateAdd = 0.0;
\t\t}
\t}""".replace("def ", ""),
        """\tvoid TickFx(double Dt)
\t{
\t\tif (!bFxActive) return;
\t\tFxRemainSec -= Dt;
\t\tif (FxRemainSec <= 0.0)
\t\t{
\t\t\tbFxActive = false;
\t\t\tFxRemainSec = 0.0;
\t\t\tAttackMulActive = 1.0;
\t\t\tRingoutRateAdd = 0.0;
\t\t\tbPendingRestore = true;
\t\t}
\t}""",
    )
    # The above replace may fail due to formatting - do simpler
(root / "SkillRuntime.h").write_text(sk, encoding="utf-8")

sk = (root / "SkillRuntime.h").read_text(encoding="utf-8")
if "bPendingRestore = true" not in sk:
    sk = sk.replace(
        """\t\tif (FxRemainSec <= 0.0)
\t\t{
\t\t\tbFxActive = false;
\t\t\tFxRemainSec = 0.0;
\t\t\tAttackMulActive = 1.0;
\t\t\tRingoutRateAdd = 0.0;
\t\t}""",
        """\t\tif (FxRemainSec <= 0.0)
\t\t{
\t\t\tbFxActive = false;
\t\t\tFxRemainSec = 0.0;
\t\t\tAttackMulActive = 1.0;
\t\t\tRingoutRateAdd = 0.0;
\t\t\tbPendingRestore = true;
\t\t}""",
    )
(root / "SkillRuntime.h").write_text(sk, encoding="utf-8")
print("SkillRuntime baseline:", "bPendingRestore" in (root/"SkillRuntime.h").read_text(encoding="utf-8"))

# Fix FireActiveSkill + Tick in cpp
cpp = (root / "PrototypeBattle.cpp").read_text(encoding="utf-8")

# Replace FireActiveSkill body
old_fire = None
start = cpp.find("void APrototypeBattleMode::FireActiveSkill()")
if start >= 0:
    end = cpp.find("\nvoid ", start + 10)
    if end < 0: end = cpp.find("\nvoid APrototypeBattleMode::ApplyBeyArt", start)
    new_fire = '''void APrototypeBattleMode::FireActiveSkill()
{
    if (MatchFlow.State != EMatchFlowState::Fighting) return;
    SkillShell.BaselineAttack = Simulation.Attack[0];
    if (!SkillShell.TryFire())
    {
        UE_LOG(LogTemp, Display, TEXT("SKILL_FIRE_BLOCKED hits=%d need=%d"), SkillShell.HitsDealt, SkillShell.Need());
        return;
    }
    // Data-layer stub: temporary Attack mul. Does NOT touch SPIN_KICK / RESTITUTION / Feel constants.
    Simulation.Attack[0] = SkillShell.BaselineAttack * SkillShell.AttackMulActive;
    UE_LOG(LogTemp, Display, TEXT("SKILL_FIRE name=JiTu tier=%d next_need=%d atk_mul=%.2f ringout_add=%.2f"),
        SkillShell.Tier, SkillShell.Need(), SkillShell.AttackMulActive, SkillShell.RingoutRateAdd);
}

'''
    if end > start:
        cpp = cpp[:start] + new_fire + cpp[end:]

# Replace crude Tick hook
hook_start = cpp.find("if (MatchFlow.State == EMatchFlowState::Fighting && AutoMatches <= 0)")
if hook_start >= 0:
    # find the closing of this if block - naive: find matching
    # Replace whole if block we inserted
    old_hook = '''    if (MatchFlow.State == EMatchFlowState::Fighting && AutoMatches <= 0)
    {
        SkillShell.ObserveHits(Simulation.Hits);
        SkillShell.TickFx(DeltaSeconds);
        // When FX ends, restore Attack from current loadout (P1).
        if (!SkillShell.bFxActive && SkillShell.AttackMulActive <= 1.0 + 1.e-6)
        {
            // Attack may have been multiplied; re-apply lineup loadout for P1 only if FX just ended.
        }
    }
'''
    new_hook = '''    if (MatchFlow.State == EMatchFlowState::Fighting && AutoMatches <= 0)
    {
        SkillShell.ObserveHits(Simulation.Hits);
        SkillShell.TickFx(DeltaSeconds);
        if (SkillShell.bPendingRestore)
        {
            Simulation.Attack[0] = SkillShell.BaselineAttack;
            SkillShell.bPendingRestore = false;
            UE_LOG(LogTemp, Display, TEXT("SKILL_FX_END restore_atk=%.3f"), Simulation.Attack[0]);
        }
    }
'''
    if old_hook in cpp:
        cpp = cpp.replace(old_hook, new_hook)
    else:
        # try fuzzy - already partially there
        pass

(root / "PrototypeBattle.cpp").write_text(cpp, encoding="utf-8")
print("Fire/Tick updated", "SKILL_FX_END" in cpp or "bPendingRestore" in (root/"PrototypeBattle.cpp").read_text(encoding="utf-8"))
