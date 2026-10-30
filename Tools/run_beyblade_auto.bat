@echo off
set UE=C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe
if not exist "%UE%" set UE=C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe
mkdir C:\BeybladeUE\Saved\Automation\GrokArt-Type4 2>nul
"%UE%" "C:\BeybladeUE\beyblade-unreal-prototype.uproject" -ExecCmds="Automation RunTests Beyblade.Battle; Quit" -ReportOutputPath="C:/BeybladeUE/Saved/Automation/GrokArt-Type4" -unattended -NullRHI -nop4 -nosplash -log=GrokArtAutomation.log
echo EXIT=%ERRORLEVEL%
