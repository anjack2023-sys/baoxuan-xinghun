import json
import os
import unreal

sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
report = {"actors": [], "api": {}}
for actor in sub.get_all_level_actors():
    item = {"label": actor.get_actor_label(), "class": actor.get_class().get_name(),
            "location": str(actor.get_actor_location()), "scale": str(actor.get_actor_scale3d())}
    mesh = actor.get_component_by_class(unreal.StaticMeshComponent)
    if mesh and mesh.static_mesh:
        item.update(mesh=mesh.static_mesh.get_path_name(), bounds=str(mesh.static_mesh.get_bounds()),
                    local_bounds=str(mesh.get_local_bounds()), relative=str(mesh.get_editor_property("relative_location")))
    light = actor.get_component_by_class(unreal.LightComponent)
    if light:
        item["intensity"] = light.get_editor_property("intensity")
    cam = actor.get_component_by_class(unreal.CameraComponent)
    if cam:
        item["camera_pp"] = str(cam.get_editor_property("post_process_settings"))
    report["actors"].append(item)
for cls, names in [(unreal.Actor, ["add_component_by_class", "attach_to_actor"]),
                   (unreal.EditorLevelLibrary, ["editor_play_in_viewport"]),
                   (unreal.EditorLevelUtils, ["create_new_streaming_level"]),
                   (unreal.TextRenderComponent, ["set_horizontal_alignment"]),
                   (unreal.AutomationLibrary, ["take_high_res_screenshot"])]:
    for name in names:
        report["api"][cls.__name__ + "." + name] = str(getattr(cls, name, None).__doc__)
report["exposure_properties"] = [x for x in dir(unreal.PostProcessSettings) if "exposure" in x]
report["exposure_enum"] = [x for x in dir(unreal.AutoExposureMethod) if x.startswith("AEM")]
path = os.path.join(unreal.Paths.project_dir(), "Tools", "formal_inspection.json")
with open(path, "w", encoding="utf-8") as output:
    json.dump(report, output, indent=2)
unreal.log("FORMAL_INSPECTION_DONE " + path)
