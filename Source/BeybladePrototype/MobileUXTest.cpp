#include "MobileUX.h"
#include "LobbyClickUI.h"
#include "Misc/AutomationTest.h"
#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMobileUXTest,"Beyblade.Mobile.TouchLayout",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMobileUXTest::RunTest(const FString&)
{
    for(const FVector2D View:{FVector2D(1280,720),FVector2D(2400,1080),FVector2D(1920,1200)})
    {
        const auto StartPixel=FLobbyClickUI::ToViewport(MobileUX::StartButton()+FVector2D(130,48),View);
        TestTrue(TEXT("start button on screen"),StartPixel.X>0 && StartPixel.X<View.X && StartPixel.Y>0 && StartPixel.Y<View.Y);
        TestTrue(TEXT("start touch target matches drawing"),MobileUX::HitStart(FLobbyClickUI::FromViewport(StartPixel,View)));
        for(int32 I=0;I<3;++I)
        {
            const auto P=MobileUX::Button(I)+FVector2D(75,36);
            const auto Pixel=FLobbyClickUI::ToViewport(P,View);
            TestTrue(TEXT("touch target on screen"),Pixel.X>0 && Pixel.X<View.X && Pixel.Y>0 && Pixel.Y<View.Y);
            TestEqual(TEXT("touch drawing and hit coordinates agree"),MobileUX::Hit(FLobbyClickUI::FromViewport(Pixel,View)),I);
        }
    }
    TestFalse(TEXT("unrelated touch does not start"),MobileUX::HitStart(FVector2D(100,100)));
    TestEqual(TEXT("unrelated touches ignored"),MobileUX::Hit(FVector2D(100,100)),-1);
    return true;
}
#endif
