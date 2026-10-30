using UnrealBuildTool;
public class BeybladePrototypeEditorTarget : TargetRules
{
    public BeybladePrototypeEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.Latest;
        ExtraModuleNames.Add("BeybladePrototype");
    }
}
