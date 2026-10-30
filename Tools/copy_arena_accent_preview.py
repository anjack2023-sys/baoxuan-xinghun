import unreal
source = '/Game/Maps/RankedArena_v1'
preview = '/Game/Maps/RankedArena_AccentPreview'
lib = unreal.EditorAssetLibrary
assert not lib.does_asset_exist(preview)
asset = lib.duplicate_asset(source, preview)
assert asset and lib.save_loaded_asset(asset, False)
unreal.SystemLibrary.quit_editor()
