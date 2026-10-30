using UnrealBuildTool;
public class BeybladePrototypeTarget : TargetRules
{
    public BeybladePrototypeTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.Latest;
        ExtraModuleNames.Add("BeybladePrototype");
    }
}
