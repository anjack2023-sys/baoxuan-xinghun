# Developer handoff

This is a source/data handoff, not a ready-to-play game distribution. All art and maps are excluded. Start with the README and the artwork license before attempting runtime restoration. The original project used UE 5.8.4 on Windows; the `.uproject` is associated with 5.8. Compile `BeybladePrototypeEditor` using the engine's Build.bat or generated Visual Studio solution. No build was rerun as part of this source release.

## Where behavior lives

| Area | Files under Source/BeybladePrototype |
|---|---|
| Fixed-step battle, contacts, endings | `BattleSimulation.h`, `RingoutPresentation.h`, `StadiumObstacles.h`, `StarCrownRim.h` |
| Match state, score and roster | `MatchFlow.h`, `CollectionCatalog.h` |
| Runtime glue, launch, input and map assets | `PrototypeBattle.cpp/.h`, `BoutPresentation.h`, `ArenaWalker.cpp/.h` |
| UI and localized strings | `ArtHUD.cpp`, `ContentStrings.h`, `LobbyClickUI.h` |
| Skills, types and tuning | `SkillRuntime.h`, `SkillBalance.h`, `Grade1Balance.h`, `IndustrialFeelSettings.h`, `MobilityProfile.h`, `FeelLabTuning.h` |
| Character-specific visuals | `*EffectComponent.cpp/.h`, `IronWallPresentation.h` |
| Save schema and operations | `PlayerSaveGame.cpp/.h`, `PlayerSaveService.h`, `BeybladeGameInstance.cpp/.h` |

Asset references retain original `/Game/...` paths. The current full-project launch is `/Game/Maps/RankedArena_AccentPreview -AvatarSelection`; neither that map nor its assets are included. `Config/DefaultEngine.ini` still contains the original default/startup map settings. Replace these and the C++ asset references when supplying your own content. The battle lookup expects arena actors with actor tags `BattleBowl` and `BattleGround`; restore suitable geometry/collision and verify those lookup paths in `PrototypeBattle.cpp`. No placeholder generator is provided.

## Data and design

All five runtime CSVs are copied unchanged under `Content/Beyblade/Data`; historical design mirrors live under `docs/balance` and `docs/content`. Some mirrors differ from current runtime tables, including `grade1-loadouts.csv` and `content-strings.csv`: do not overwrite runtime files with old mirrors. Keep `feel-lab-types.csv` in place (its absence can reject startup), and preserve `skills-grade1.csv` (missing skill data can disable skills). `Grade1Balance.h`, `SkillBalance.h` and `ContentStrings.h` implement readers/fallbacks. Some values and bindings are still C++, and some design-table columns are templates. Preserve encoding and validate CSV loading in runtime logs after changes; a successful fallback does not prove an edited CSV was used.

`docs/mechanics/talents-passives-2026-10-30.md` supersedes passive sections in older skill documents. Other retained documents describe dated decisions and may contain older assumptions; current code/data take precedence when they conflict. Latest stamina wall-window behavior is implemented and covered in `SkillEffectsTest.cpp`; inspect the current implementation rather than relying on older threshold wording.

## Checks and deterministic batches

The module includes UE automation tests named `Beyblade.Battle.*`, `Beyblade.Match.*`, `Beyblade.Skills.*`, `Beyblade.Arena.*`, `Beyblade.Launch.*`, `Beyblade.Presentation.*`, `Beyblade.Mobile.*` and `Beyblade.Save.*`. Open Session Frontend / Automation after compiling and run a suitable focused group. Some tests load maps/meshes and cannot pass without replacements or licensed originals. Inspect save tests before running; use a disposable project/user profile and never copy someone else's progress into a test run. No new UE test-pass claim is made by this handoff.

Historical deterministic batch arguments are `-ProtoSeed=4242 -ProtoAuto=24`; an explicit seed is required for automatic batches. Inspect `PrototypeBattle.cpp` and use an appropriate restored map. Check for `BATTLE_AUTO_COMPLETE matches=24`, then compare paired CSV logs using `Tools/verify_match_logs.py`. `Tools/run_seed_batches.ps1` and other launchers contain original-machine paths and excluded build locations: adapt them before use. Automated batches bypass parts of the interactive match flow and are not a full interactive acceptance test.

## Optional tools

UE editor Python tools require Unreal's Python Editor Script Plugin; some external model/export tools expect Blender. Many tools depend on excluded `Saved/FeelRef60/work/LabSources`, `_import_staging`, `D:/Downloads` and other original-machine paths. These scripts document production steps, not a complete reproducible asset pipeline. `make_launch_audio.py` and `make_collision_audio.py` synthesize sound but original generated sound assets are not included. AI-player scripts require Pillow, a Windows desktop session, your own paid API access and a separately packaged game. Headless CLI reads `SK` from the process environment and clears it on exit. The GUI accepts a key in a masked input field and clears the field before the worker runs. No literal live credentials should be stored in either. External AI-player access is a local observation/input bridge, not online multiplayer.

## What was removed for public release

- Every original `.uasset`/`.umap`, model, texture, portrait, environment, UI image, sound and other binary art/media file.
- Saved/Builds/Binaries/Intermediate/DerivedDataCache, backups, personal saves, logs and reference videos.
- Entire AndroidFileServerEditor runtime-settings section from DefaultEngine.ini, including the original security token.
- DefaultEditor.ini with local editor history/metadata.
- Historical reports, AI task/chat records and full art inboxes. A small original Tripo provenance text is retained without distributing any model.

`RELEASE_AUDIT.json` records byte-for-byte copy checks and public-text credential scan results. `MANIFEST.sha256` lists the final file hashes, excluding the manifest itself. The scanner detects common credential forms and literal secret assignments; it is a static check, not a guarantee against every possible secret or a legal audit of generated assets. Source and included runtime CSVs are checked against the working originals; no original project file was changed.
