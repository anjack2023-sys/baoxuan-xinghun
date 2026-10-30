from pathlib import Path
bs=Path(r"C:\BeybladeUE\Source\BeybladePrototype\BattleSimulation.h").read_text(encoding="utf-8")
print("bWallBump in Reset", "bWallBumpThisFrame = false" in bs)
print("bWallBump set in rim", bs.count("bWallBumpThisFrame = true"))
print("Tick clear", "bWallBumpThisFrame = false;\n\t\t++Frames" in bs or "bWallBumpThisFrame = false;" in bs)
# Fix Reset if missing
if "PendingExtraKickMul[0] = PendingExtraKickMul[1] = 1.0;" in bs and "bWallBumpThisFrame = false;" not in bs[bs.find("void Reset()"):bs.find("void Reset()")+800]:
    bs=bs.replace(
        "PendingExtraKickMul[0] = PendingExtraKickMul[1] = 1.0;",
        "PendingExtraKickMul[0] = PendingExtraKickMul[1] = 1.0;\n\t\tbWallBumpThisFrame = false;",
        1,
    )
    Path(r"C:\BeybladeUE\Source\BeybladePrototype\BattleSimulation.h").write_text(bs,encoding="utf-8")
    print("Reset wall clear added")
