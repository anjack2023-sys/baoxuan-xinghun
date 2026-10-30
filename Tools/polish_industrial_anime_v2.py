# -*- coding: utf-8 -*-
"""Anime navy/cream/gold venue polish on StadiumIndustrialPolish_v1.
Softens glare; keeps collision, tags, scales, FaceCamera.ini untouched.
Does NOT touch FeelRef60 / BattleSimulation physics constants.
"""
import hashlib, json, time, traceback
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT = ROOT / "screenshots/grok-art-20261027/after"
OUT.mkdir(parents=True, exist_ok=True)
ASSETS = "/Game/ArtPreview/IndustrialPolish_v1"
MAP = "/Game/Maps/StadiumIndustrialPolish_v1"
LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
MEL = unreal.MaterialEditingLibrary
MAIN_HASH = hashlib.sha256((ROOT / "Content/Maps/Main.umap").read_bytes()).hexdigest()


def import_hengren_portrait():
    src = Path(r"C:\\Users\\Administrator\\Desktop\\bey-art-refs\\heroes-8\\batch1-lock\\BEY_hengblade_BALANCE_preview.png")
    dest = "/Game/Beyblade/UI/P3"
    name = "T_PortraitHengren"
    path = dest + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return path
    if not src.is_file():
        return None
    task = unreal.AssetImportTask()
    task.filename = str(src)
    task.destination_path = dest
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = False
    TOOLS.import_asset_tasks([task])
    tex = unreal.load_asset(path)
    if not isinstance(tex, unreal.Texture2D):
        return None
    tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tex.set_editor_property("srgb", True)
    tex.set_editor_property("never_stream", True)
    unreal.EditorAssetLibrary.save_loaded_asset(tex)
    return path


REQUIRED_TAGS = ("BattleP1", "BattleP2", "BattleBowl", "BattleGround", "BattleCamera", "FaceBackdrop", "FaceCameraCharacter")

def material(name, color, roughness=0.82, metal=0.08, specular=0.18):
    path = ASSETS + "/" + name
    mat = unreal.load_asset(path) or TOOLS.create_asset(name, ASSETS, unreal.Material, unreal.MaterialFactoryNew())
    assert mat, name
    MEL.delete_all_material_expressions(mat)
    base = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector)
    base.constant = unreal.LinearColor(*color, 1)
    MEL.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    for prop, value in [
        (unreal.MaterialProperty.MP_ROUGHNESS, roughness),
        (unreal.MaterialProperty.MP_METALLIC, metal),
        (unreal.MaterialProperty.MP_SPECULAR, specular),
    ]:
        node = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant)
        node.r = value
        MEL.connect_material_property(node, "", prop)
    MEL.recompile_material(mat)
    assert unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat

def set_rect(label, intensity=None, color=None):
    actor = next((a for a in ACTORS.get_all_level_actors() if a.get_actor_label() == label), None)
    if not actor:
        return False
    comp = actor.get_component_by_class(unreal.RectLightComponent)
    if not comp:
        return False
    if intensity is not None:
        comp.set_intensity(intensity)
    if color is not None:
        comp.set_light_color(unreal.LinearColor(*color, 1))
    return True

def ensure_pp():
    pp = next((a for a in ACTORS.get_all_level_actors() if a.get_actor_label() == "GrokArtExposure"), None)
    if pp is None:
        pp = ACTORS.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector())
        pp.set_actor_label("GrokArtExposure")
    settings = unreal.PostProcessSettings()
    for key, value in {
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_MANUAL,
        "override_auto_exposure_apply_physical_camera_exposure": True,
        "auto_exposure_apply_physical_camera_exposure": False,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": -3.2,
        "override_bloom_intensity": True,
        "bloom_intensity": 0.05,
        "override_motion_blur_amount": True,
        "motion_blur_amount": 0.0,
    }.items():
        settings.set_editor_property(key, value)
    pp.set_editor_property("unbound", True)
    pp.set_editor_property("priority", 80)
    pp.set_editor_property("settings", settings)
    return True

def rebuild_backdrop_emissive(strength=6.5):
    """Lower unlit emissive so backdrop does not wash out bowl collisions."""
    backdrop = unreal.load_asset(ASSETS + "/M_ArenaBackdrop")
    tex = unreal.load_asset(ASSETS + "/T_EnvArena")
    assert backdrop and tex
    MEL.delete_all_material_expressions(backdrop)
    backdrop.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    backdrop.set_editor_property("two_sided", True)
    sample = MEL.create_material_expression(backdrop, unreal.MaterialExpressionTextureSample)
    sample.texture = tex
    uv = MEL.create_material_expression(backdrop, unreal.MaterialExpressionTextureCoordinate)
    flip = MEL.create_material_expression(backdrop, unreal.MaterialExpressionMultiply)
    flip_scale = MEL.create_material_expression(backdrop, unreal.MaterialExpressionConstant2Vector)
    flip_scale.r = 1.0
    flip_scale.g = -1.0
    offset = MEL.create_material_expression(backdrop, unreal.MaterialExpressionAdd)
    flip_bias = MEL.create_material_expression(backdrop, unreal.MaterialExpressionConstant2Vector)
    flip_bias.r = 0.0
    flip_bias.g = 1.0
    MEL.connect_material_expressions(uv, "", flip, "A")
    MEL.connect_material_expressions(flip_scale, "", flip, "B")
    MEL.connect_material_expressions(flip, "", offset, "A")
    MEL.connect_material_expressions(flip_bias, "", offset, "B")
    assert MEL.connect_material_expressions(offset, "", sample, "UVs")
    multiply = MEL.create_material_expression(backdrop, unreal.MaterialExpressionMultiply)
    strength_n = MEL.create_material_expression(backdrop, unreal.MaterialExpressionConstant)
    strength_n.r = float(strength)
    MEL.connect_material_expressions(strength_n, "", multiply, "B")
    MEL.connect_material_expressions(sample, "RGB", multiply, "A")
    MEL.connect_material_property(multiply, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(backdrop)
    assert unreal.EditorAssetLibrary.save_loaded_asset(backdrop)
    return strength

def rebuild_bowl_coated():
    """Clear coated metal: readable metal, lower specular glare."""
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    texture = next(
        a.get_asset()
        for a in registry.get_assets_by_path("/Game/ArtPreview/IndustrialGame_v1", recursive=True)
        if str(a.asset_class_path.asset_name) == "Texture2D"
    )
    surface = unreal.load_asset(ASSETS + "/M_IndustrialCoated") or TOOLS.create_asset(
        "M_IndustrialCoated", ASSETS, unreal.Material, unreal.MaterialFactoryNew())
    MEL.delete_all_material_expressions(surface)
    sample = MEL.create_material_expression(surface, unreal.MaterialExpressionTextureSample)
    sample.texture = texture
    MEL.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    # Was roughness .62 / metal .18 / spec .25 — raise roughness, cut specular to reduce glare
    for prop, value in [
        (unreal.MaterialProperty.MP_ROUGHNESS, 0.72),
        (unreal.MaterialProperty.MP_METALLIC, 0.22),
        (unreal.MaterialProperty.MP_SPECULAR, 0.14),
    ]:
        node = MEL.create_material_expression(surface, unreal.MaterialExpressionConstant)
        node.r = value
        MEL.connect_material_property(node, "", prop)
    MEL.recompile_material(surface)
    assert unreal.EditorAssetLibrary.save_loaded_asset(surface)
    return surface

def apply_art():
    portrait = import_hengren_portrait()
    by_label = {a.get_actor_label(): a for a in ACTORS.get_all_level_actors()}
    # Tag presence (names may be on different actors)
    tag_hits = {t: False for t in REQUIRED_TAGS}
    for a in ACTORS.get_all_level_actors():
        for t in a.tags:
            s = str(t)
            if s in tag_hits:
                tag_hits[s] = True
    male = by_label["MaleLead"]
    bowl_actor = by_label["SmoothBowl_v1"]
    bowl = bowl_actor.get_component_by_class(unreal.StaticMeshComponent)
    before_hit = bowl.line_trace_component(unreal.Vector(0, 0, 600), unreal.Vector(0, 0, -200), True, False, False)
    assert before_hit and abs(before_hit[0].z - 42) < 0.05, str(before_hit)
    before_scale = male.get_actor_scale3d().x
    assert abs(before_scale - 2.165) < 0.001

    # Palette: anime navy / cream / muted gold
    navy = material("M_VenueNavy", (0.035, 0.055, 0.095), 0.88, 0.06, 0.12)
    steel = material("M_VenueSteel", (0.085, 0.100, 0.125), 0.70, 0.28, 0.16)
    floor = material("M_VenueFloor", (0.085, 0.078, 0.068), 0.90, 0.04, 0.10)  # cream-tinted
    seam = material("M_FloorSeam", (0.020, 0.028, 0.040), 0.95, 0.0, 0.08)
    gold = material("M_MutedGold", (0.42, 0.32, 0.14), 0.58, 0.45, 0.18)

    ground = by_label["GroundFallback"]
    ground.get_component_by_class(unreal.StaticMeshComponent).set_material(0, floor)
    for label, mat in [
        ("RearVenueWall", navy), ("RearVenueCap", steel), ("RearGoldInlay", gold),
    ]:
        if label in by_label:
            by_label[label].get_component_by_class(unreal.StaticMeshComponent).set_material(0, mat)
    for a in ACTORS.get_all_level_actors():
        lab = a.get_actor_label()
        mesh = a.get_component_by_class(unreal.StaticMeshComponent)
        if not mesh:
            continue
        if lab.startswith("FloorJoint_"):
            mesh.set_material(0, seam)
        elif lab.startswith("RearWallPost_") or lab.startswith("SideBoundaryCap_"):
            mesh.set_material(0, steel)
        elif lab.startswith("SideBoundary_"):
            mesh.set_material(0, navy)

    surface = rebuild_bowl_coated()
    bowl.set_material(0, surface)
    emissive = rebuild_backdrop_emissive(6.5)

    # Soften venue lights (were 1800/1100/4000/600)
    set_rect("VenueSoftKey", intensity=1200, color=(1.0, 0.94, 0.86))
    set_rect("VenueCoolRim", intensity=700, color=(0.55, 0.68, 0.95))
    set_rect("VenueFloorFill", intensity=2200, color=(0.90, 0.88, 0.82))
    set_rect("CharacterSoftFill", intensity=450, color=(1.0, 0.93, 0.84))
    ensure_pp()

    after_hit = bowl.line_trace_component(unreal.Vector(0, 0, 600), unreal.Vector(0, 0, -200), True, False, False)
    assert after_hit and abs(after_hit[0].z - before_hit[0].z) < 0.001
    assert abs(male.get_actor_scale3d().x - before_scale) < 0.001
    assert LEVELS.save_current_level()
    return {
        "map": MAP,
        "center_collision_z_cm": after_hit[0].z,
        "character_scale": before_scale,
        "backdrop_emissive": emissive,
        "bowl_roughness": 0.72,
        "bowl_metallic": 0.22,
        "bowl_specular": 0.14,
        "tag_hits": tag_hits,
        "main_sha256_before": MAIN_HASH,
        "portrait_hengren": portrait,
        "changes": [
            "Lower backdrop emissive 24->6.5",
            "Bowl coated: roughness+.10 metallic+.04 specular-.11",
            "Venue lights softened ~33%",
            "Cream-tint floor + navy/gold walls refreshed",
            "Manual exposure bias -3.2, bloom 0.05",
        ],
    }

STATE = {"phase": "start", "time": time.monotonic(), "busy": False, "handle": None, "report": {}}

def tick(dt):
    if STATE["busy"]:
        return
    STATE["busy"] = True
    try:
        elapsed = time.monotonic() - STATE["time"]
        if STATE["phase"] == "start" and elapsed > 3:
            assert LEVELS.load_level(MAP)
            STATE["report"] = apply_art()
            STATE.update(phase="wait_editor", time=time.monotonic())
        elif STATE["phase"] == "wait_editor" and elapsed > 5:
            LEVELS.editor_request_begin_play()
            STATE.update(phase="wait_pie", time=time.monotonic())
        elif STATE["phase"] == "wait_pie" and elapsed > 8:
            world = UES.get_game_world()
            assert world
            pc = unreal.GameplayStatics.get_player_controller(world, 0)
            unreal.SystemLibrary.execute_console_command(world, "showhud 0", pc)
            path = str(OUT / "stadium_after.png").replace("\\", "/")
            unreal.SystemLibrary.execute_console_command(world, 'HighResShot 1600x900 filename="' + path + '"', pc)
            STATE["report"]["stadium_after"] = path
            STATE.update(phase="hud", time=time.monotonic())
        elif STATE["phase"] == "hud" and elapsed > 4:
            world = UES.get_game_world()
            pc = unreal.GameplayStatics.get_player_controller(world, 0)
            unreal.SystemLibrary.execute_console_command(world, "showhud 1", pc)
            path = str(OUT / "lobby_or_hud_after.png").replace("\\", "/")
            unreal.SystemLibrary.execute_console_command(world, 'HighResShot 1600x900 filename="' + path + '"', pc)
            STATE["report"]["lobby_after"] = path
            STATE.update(phase="flush", time=time.monotonic())
        elif STATE["phase"] == "flush" and elapsed > 5:
            assert Path(STATE["report"]["stadium_after"]).is_file()
            after = hashlib.sha256((ROOT / "Content/Maps/Main.umap").read_bytes()).hexdigest()
            assert after == MAIN_HASH
            STATE["report"]["main_sha256_after"] = after
            STATE["report"]["status"] = "PASS"
            (OUT / "after_report.json").write_text(json.dumps(STATE["report"], indent=2), encoding="utf8")
            unreal.unregister_slate_post_tick_callback(STATE["handle"])
            LEVELS.editor_request_end_play()
            unreal.log("GROK_ART_AFTER_POLISH_COMPLETE")
            unreal.SystemLibrary.quit_editor()
    except Exception:
        (OUT / "error.txt").write_text(traceback.format_exc(), encoding="utf8")
        unreal.log_error(traceback.format_exc())
        try:
            unreal.unregister_slate_post_tick_callback(STATE["handle"])
        except Exception:
            pass
        unreal.SystemLibrary.quit_editor()
    finally:
        STATE["busy"] = False

STATE["handle"] = unreal.register_slate_post_tick_callback(tick)
