#pragma once
#include "CoreMinimal.h"
#include "Misc/ConfigCacheIni.h"
struct FIndustrialFeelSettings
{
    int32 Move=120,Ringout=60;
    void Clamp() {Move=FMath::Clamp(Move,10,200);Ringout=FMath::Clamp(Ringout,0,100);}
    void Load(const FString& File)
    {
        FConfigFile C;C.Read(File);C.GetInt(TEXT("Feel"),TEXT("Move"),Move);C.GetInt(TEXT("Feel"),TEXT("Ringout"),Ringout);Clamp();
    }
    bool Save(const FString& File) const
    {
        FIndustrialFeelSettings V=*this;V.Clamp();FConfigFile C;C.bCanSaveAllSections=true;
        C.SetInt64(TEXT("Feel"),TEXT("Move"),V.Move);C.SetInt64(TEXT("Feel"),TEXT("Ringout"),V.Ringout);return C.Write(File);
    }
};
