using UnrealBuildTool;
public class BeybladePrototype : ModuleRules
{
    public BeybladePrototype(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PrivateDependencyModuleNames.Add("RenderCore");
        PublicDependencyModuleNames.AddRange(new[] {"Core", "CoreUObject", "Engine", "InputCore", "EnhancedInput", "SlateCore", "Slate", "MoviePlayer"});
    }
}
