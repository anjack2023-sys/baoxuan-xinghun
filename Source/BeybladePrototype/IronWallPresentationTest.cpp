#include "IronWallPresentation.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"
#include "Misc/AutomationTest.h"
#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FIronWallPresentationTest, "Beyblade.Skills.IronWallPresentation", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FIronWallPresentationTest::RunTest(const FString&)
{
    TestEqual(TEXT("deploy begins transparent"), IronWallPresentation::Opacity(0., -1.), 0.);
    TestEqual(TEXT("persistent shield stays visible without a baked video duration"), IronWallPresentation::Opacity(30., -1.), 1.);
    TestEqual(TEXT("expiry fades halfway"), IronWallPresentation::Opacity(4., IronWallPresentation::FadeSeconds / 2.), .5);
    TestEqual(TEXT("no lingering shield"), IronWallPresentation::Opacity(4., 1.), 0.);
    TestEqual(TEXT("no future impact"), IronWallPresentation::HitOpacity(-.01), 0.);
    TestEqual(TEXT("impact starts bright"), IronWallPresentation::HitOpacity(0.), 1.);
    TestEqual(TEXT("impact ends"), IronWallPresentation::HitOpacity(1.), 0.);
    for (const TCHAR* Name : {TEXT("SM_IronWallField"), TEXT("SM_IronWallLines"), TEXT("SM_IronWallGround"), TEXT("SM_IronWallRipple")})
    {
        auto* Mesh = LoadObject<UStaticMesh>(nullptr, *FString::Printf(TEXT("/Game/Beyblade/FX/IronWall/%s.%s"), Name, Name));
        if (TestNotNull(TEXT("shield mesh cooked source exists"), Mesh)) TestTrue(TEXT("centimetre scale is valid"), Mesh->GetBounds().BoxExtent.X > 90. && Mesh->GetBounds().BoxExtent.X < 160.);
    }
    for (const TCHAR* Name : {TEXT("M_IronWallField"), TEXT("M_IronWallLines")})
        TestNotNull(TEXT("shield material exists"), LoadObject<UMaterialInterface>(nullptr, *FString::Printf(TEXT("/Game/Beyblade/FX/IronWall/%s.%s"), Name, Name)));
    return true;
}
#endif
