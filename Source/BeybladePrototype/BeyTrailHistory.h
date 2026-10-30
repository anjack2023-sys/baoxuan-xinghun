#pragma once
#include "CoreMinimal.h"

struct FBeyTrailHistory
{
    TArray<FVector> Points[2];
    void Reset() {Points[0].Reset();Points[1].Reset();}
    void Record(int32 Frame,const FVector& A,const FVector& B)
    {
        if(Frame%2!=0) return;
        Points[0].Add(A);Points[1].Add(B);
        for(auto& Trail:Points) if(Trail.Num()>30) Trail.RemoveAt(0,Trail.Num()-30,EAllowShrinking::No);
    }
};
