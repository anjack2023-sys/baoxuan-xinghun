from pathlib import Path
cpp_path=Path(r"C:\BeybladeUE\Source\BeybladePrototype\PrototypeBattle.cpp")
cpp=cpp_path.read_text(encoding="utf-8")
old='''void APrototypeBattleMode::StartBattleInternal()
{
    ApplyCurrentLoadouts();
    Simulation.Reset();
    Simulation.Launch(); ++Match; Accumulator = 0;'''
new='''void APrototypeBattleMode::StartBattleInternal()
{
    ApplyCurrentLoadouts();
    SkillShell.ResetForBout();
    Simulation.Reset();
    Simulation.Launch(); ++Match; Accumulator = 0;'''
if old not in cpp:
    raise SystemExit("StartBattleInternal block not found exact")
cpp=cpp.replace(old,new,1)
cpp_path.write_text(cpp, encoding="utf-8")
print("StartBattleInternal reset ok", cpp.count("SkillShell.ResetForBout"))
