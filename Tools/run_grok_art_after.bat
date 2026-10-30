@echo off
set UE=C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe
"%UE%" "C:\BeybladeUE\beyblade-unreal-prototype.uproject" -ExecCmds="py C:/BeybladeUE/Tools/polish_industrial_anime_v2.py" -unattended -nosplash -nosound -windowed -ResX=1600 -ResY=900 -log=GrokArtAfter.log
echo EXIT=%ERRORLEVEL%
