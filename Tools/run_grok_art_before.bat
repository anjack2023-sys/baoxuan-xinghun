@echo off
set UE=C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe
"%UE%" "C:\BeybladeUE\beyblade-unreal-prototype.uproject" -ExecCmds="py C:/BeybladeUE/Tools/capture_industrial_before.py" -unattended -nosplash -nosound -windowed -ResX=1600 -ResY=900 -log=GrokArtBefore.log
echo EXIT=%ERRORLEVEL%
