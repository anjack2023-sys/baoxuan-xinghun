$ErrorActionPreference = 'Stop'
$projectFile = 'C:\BeybladeUE\beyblade-unreal-prototype.uproject'
$editorExe = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
if (Get-Process UnrealEditor -ErrorAction SilentlyContinue) { throw 'Close Unreal Editor before seed batches to save memory.' }
foreach ($battleSeed in 4242, 42, 2026) {
    foreach ($renderFPS in 60, 120) {
        $batchLog = "C:\BeybladeUE\Saved\Battle-auto-$battleSeed-$renderFPS.log"
        & $editorExe $projectFile /Game/Maps/Main -game -nullrhi -unattended -nosplash -benchmark "-fps=$renderFPS" "-ProtoSeed=$battleSeed" -ProtoAuto=24 "-abslog=$batchLog" *> 'C:\BeybladeUE\Saved\Battle-auto-console.txt'
        if (-not (Select-String -LiteralPath $batchLog -Pattern 'BATTLE_AUTO_COMPLETE matches=24' -Quiet)) {
            throw "Incomplete batch: $batchLog (inspect BATTLE_INIT_FAILED / BATTLE_SURFACE_FAILED)"
        }
        Write-Output "COMPLETE seed=$battleSeed render_fps=$renderFPS; CSV path appears after BATTLE_READY in $batchLog"
    }
}
