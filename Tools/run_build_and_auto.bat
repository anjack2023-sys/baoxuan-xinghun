@echo off
cd /d C:\BeybladeUE
call Build-Editor.bat
if errorlevel 1 exit /b %ERRORLEVEL%
set UE=C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe
"%UE%" "C:\BeybladeUE\beyblade-unreal-prototype.uproject" -ExecCmds="Automation RunTests Beyblade.Battle; Quit" -unattended -NullRHI -nop4 -nosplash -log=GrokArtAutomation.log
echo EXIT=%ERRORLEVEL%
