# -*- coding: utf-8 -*-
"""Import missing heroes-8 meshes into Content/Beyblade/Art/Tripo_v1/. Feel untouched."""
import json, traceback
from pathlib import Path
import unreal

root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
report = {"imports": {}, "status": "FAIL"}
try:
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    jobs = [
        ("Chiwen", root / "docs/P3-art-inbox/heroes-8/batch2-side-v2/tech-v1/BEY_chiwen_ATTACK_side_tech_v1.glb"),
        ("Huangkai", root / "docs/P3-art-inbox/heroes-8/batch2-side-v2/tech-v1/BEY_huangkai_DEFENSE_side_tech_v1.glb"),
        ("Cuipan", root / "docs/P3-art-inbox/heroes-8/batch2-side-v2/tech-v1/BEY_cuipan_STAMINA_side_tech_v1.glb"),
        ("Shuanghuan", root / "docs/P3-art-inbox/heroes-8/batch2-side-v2/tech-v1/BEY_shuanghuan_BALANCE_side_tech_v1.glb"),
        ("Changxuan", root / "docs/P3-art-inbox/heroes-8/batch1-lock/BEY_changxuan_STAMINA_tripo_v1.glb"),
    ]
    for name, source in jobs:
        assert source.is_file(), f"missing {source}"
        destination = f"/Game/Beyblade/Art/Tripo_v1/{name}"
        stable = f"/Game/Beyblade/Art/Tripo_v1/SM_{name}"
        if unreal.EditorAssetLibrary.does_asset_exist(stable):
            mesh = unreal.load_asset(stable)
            bounds = mesh.get_bounds()
            report["imports"][name] = {"mesh": mesh.get_path_name(), "extent": str(bounds.box_extent), "skipped": True}
            continue
        task = unreal.AssetImportTask()
        task.filename = str(source)
        task.destination_path = destination
        task.automated = True
        task.save = True
        task.replace_existing = False
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        meshes = [a.get_asset() for a in registry.get_assets_by_path(destination, recursive=True)
                  if str(a.asset_class_path.asset_name) == "StaticMesh"]
        assert len(meshes) >= 1, f"no mesh for {name} in {destination}"
        # Prefer largest mesh if multiple
        meshes.sort(key=lambda m: m.get_bounds().box_extent.x * m.get_bounds().box_extent.y, reverse=True)
        src_path = meshes[0].get_path_name()
        if not unreal.EditorAssetLibrary.does_asset_exist(stable):
            assert unreal.EditorAssetLibrary.duplicate_asset(src_path, stable), f"dup fail {name}"
        mesh = unreal.load_asset(stable)
        assert mesh, f"load fail {stable}"
        bounds = mesh.get_bounds()
        assert unreal.EditorAssetLibrary.save_loaded_asset(mesh)
        report["imports"][name] = {"mesh": mesh.get_path_name(), "extent": str(bounds.box_extent), "source": str(source)}
        unreal.log(f"HEROES8_IMPORT {name} -> {stable}")
    report["status"] = "PASS"
except Exception:
    report["error"] = traceback.format_exc()
    unreal.log_error(report.get("error", ""))
finally:
    out = root / "Tools" / "heroes8_mesh_import_report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf8")
    unreal.SystemLibrary.quit_editor()
