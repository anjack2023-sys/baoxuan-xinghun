#include "ArenaWalker.h"
#include "LobbyClickUI.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/StaticMesh.h"
#include "Misc/AutomationTest.h"

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArenaExperienceTest, "Beyblade.Arena.EntryAndAssets", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FArenaExperienceTest::RunTest(const FString&)
{
    const FVector2D Entry = FLobbyClickUI::ArenaPos() + FVector2D(140, 48);
    TestEqual(TEXT("hall button enters arena"), static_cast<int32>(FLobbyClickUI::HitTest(Entry.X, Entry.Y, EMatchFlowState::Lobby)), static_cast<int32>(ELobbyClickAction::EnterArena));
    TestEqual(TEXT("entry does not interrupt battle"), static_cast<int32>(FLobbyClickUI::HitTest(Entry.X, Entry.Y, EMatchFlowState::Fighting)), static_cast<int32>(ELobbyClickAction::None));
    for(int32 I=0;I<6;++I)
    {
        const FVector2D P=FLobbyClickUI::AvatarPos(I)+FVector2D(FLobbyClickUI::AvatarW/2,FLobbyClickUI::BtnH/2);
        TestTrue(TEXT("avatar button contains its center"),FLobbyClickUI::Contains(FLobbyClickUI::AvatarPos(I),FVector2D(FLobbyClickUI::AvatarW,FLobbyClickUI::BtnH),P.X,P.Y));
        for(int32 J=0;J<6;++J) if(I!=J) TestFalse(TEXT("avatar buttons do not overlap"),FLobbyClickUI::Contains(FLobbyClickUI::AvatarPos(J),FVector2D(FLobbyClickUI::AvatarW,FLobbyClickUI::BtnH),P.X,P.Y));
    }
    const auto* Walker = GetDefault<AArenaWalker>();
    TestEqual(TEXT("walk speed"), Walker->GetCharacterMovement()->MaxWalkSpeed, 240.f);
    TestEqual(TEXT("walking capsule radius"), Walker->GetCapsuleComponent()->GetUnscaledCapsuleRadius(), 34.f);
    auto* Environment = LoadObject<UStaticMesh>(nullptr, TEXT("/Game/Beyblade/Arena/StarCrown_v1/SM_ApprovedArena.SM_ApprovedArena"));
    if (TestNotNull(TEXT("ranked stadium exists"), Environment))
    {
        TestTrue(TEXT("meter to centimeter import scale"), FMath::Abs(Environment->GetBounds().BoxExtent.X - 1450.) < 1.);
        TestEqual(TEXT("all authored material slots preserved"), Environment->GetStaticMaterials().Num(), 23);
        for (int32 I = 0; I < Environment->GetStaticMaterials().Num(); ++I)
            TestNotNull(TEXT("stadium material assigned"), Environment->GetMaterial(I));
    }
    auto* Table = LoadObject<UStaticMesh>(nullptr, TEXT("/Game/Beyblade/Arena/StarCrown_v1/SM_StarCrown_Arena80.SM_StarCrown_Arena80"));
    if (TestNotNull(TEXT("approved compact battle table exists"), Table))
        TestTrue(TEXT("table carries distinct finish and safety materials"), Table->GetStaticMaterials().Num() >= 6);
    return true;
}
#endif
