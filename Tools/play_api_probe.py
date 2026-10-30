import json, os, unreal
out = {"methods": {}}
for name in dir(unreal.EditorLevelLibrary):
    if "play" in name.lower() or "pie" in name.lower() or "simulate" in name.lower():
        out["methods"]["EditorLevelLibrary."+name] = True
try:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    for name in dir(les):
        if "play" in name.lower() or "pie" in name.lower() or "request" in name.lower():
            out["methods"]["LevelEditorSubsystem."+name] = True
except Exception as e:
    out["les_err"] = str(e)
for name in dir(unreal):
    if "Play" in name and ("Editor" in name or "Level" in name or "Session" in name):
        out["methods"]["unreal."+name] = True
# also try common
candidates = []
for cls_name in ["EditorLevelLibrary", "LevelEditorSubsystem", "EditorActorSubsystem"]:
    pass
path = os.path.join(unreal.Paths.project_dir(), "Tools", "play_api_probe.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2)
unreal.log("PLAY_API_PROBE " + path)