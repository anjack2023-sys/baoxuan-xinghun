# 游戏数据分类与实际接入索引

核对日期：2026-10-27。此文记录当前磁盘与源码实际状态；旧方案中的“建议迁移”“待做骨架”和 Feel85 冻结说明不能直接当作当前状态。

## 工程与两个版本

工程根目录为 `C:\BeybladeUE`，它是桌面 `ai陀螺游戏\beyblade-unreal-prototype` 的目录联接，两者是同一套文件。

| 版本 | 可编辑来源 | 体验入口 | 分工 |
|---|---|---|---|
| 当前工业场馆版 | 根目录 `Source`、`Content`、`Config` | `Preview-Industrial-Stadium.bat` | Grok 优化美术 |
| 旧版手感试验 | `Saved/FeelRef60/work` 内的独立工程 | `Builds/Windows-Feel85-60s/Start-Game.bat` | GPT 调手感，确认后选择性移植 |

旧试玩目录名称保留 Feel85，但当前试验已为 ContactFeelTrial=86；不要按目录名判断参数。当前说明见 [CURRENT-TUNING](../Builds/Windows-Feel85-60s/CURRENT-TUNING.md)。不要用旧试验的整套 Source/Content 覆盖工业版。

## 分类：放在哪里、是否已经生效

以下均相对工程根目录。

| 分类 | 实际位置 | 当前接入状态与修改规则 |
|---|---|---|
| 游戏属性：攻击、防御、质量、衰减 | `Content/Beyblade/Data/grade1-loadouts.csv`；文档镜像 `docs/balance/grade1-loadouts.csv` | `Source/BeybladePrototype/Grade1Balance.h` 已有 CSV 读取及内置回退；Content 优先。两份当前一致，修改时同步并验证读取日志 |
| 其他调参模板 | `docs/balance/tunables-template.csv` | 仅 G1_/G2_/G3_ 支持项可覆盖且跳过 frozen 行；U1–U6 等模板项并非已经接入，不能只改表就认为生效 |
| 文案 | `Content/Beyblade/Data/content-strings.csv`；镜像 `docs/content/content-strings.csv` | `ContentStrings.h` 已读表并有内置回退；尚有直接写在 UI 源码中的文案 |
| 陀螺内容目录表 | `docs/content/content-beys.csv` | 目前是占位模板，不是完整模型/立绘注册表；资源绑定仍需核对源码 |
| UI 内容目录表 | `docs/content/content-ui.csv` | 目前是占位模板，未成为统一运行时来源 |
| 陀螺模型 | `Content/Beyblade/Art/Tripo_v1`；旧资源 `Content/Imported/Beys`、`Content/VisualPass/Beys` | UE 运行资产；具体使用对象以地图和源码引用为准 |
| UI、立绘 | `Content/Beyblade/UI/P3` | 已导入的 UI 资产；部分路径仍在 `ArtHUD.cpp`、`PrototypeBattle.cpp` 中绑定 |
| 音效 | `Content/Beyblade/Audio` | 已导入运行资产；播放机制在 `PrototypeBattle.cpp` |
| 场馆、人物、材质与地图 | `Content/Imported/Stadium`、`Content/Imported/Character`、`Content/VisualPass/Materials`、`Content/Maps` | 仍有旧目录资源被引用。工业地图为 `StadiumIndustrialPolish_v1`；禁止仅为分类直接搬动 uasset |
| 待审美术与原图 | `docs/P3-art-inbox/batch1`、`batch2`、`approved`、`batch3-tripo-v1` 等 | 原始素材/审核区；放进 approved 不等于已经导入 UE。桌面 bey-art-refs 也是制作参考区 |
| 机制文档 | `docs/mechanics`，统筹方案 `docs/planner`，属性说明 `docs/balance` | 设计与说明资料，不是全部自动读取的配置 |
| 机制实现 | `Source/BeybladePrototype/BattleSimulation.h`、`MatchFlow.h`、`PrototypeBattle.cpp` | 碰撞/胜负、选螺与计分、场景与输入连接；改动需要回归验证 |
| 玩家存档结构与服务 | `Source/BeybladePrototype/PlayerSaveGame.h`、`PlayerSaveService.h` | 已落地并由主流程接入；保存版本、解锁、胜场、上次模式，以及音量/静音/语言字段骨架。字段存在不代表所有设置均已接到 UI/音频 |
| 玩家存档文件 | 当前工程 `Saved/SaveGames/BeybladeSlot0.sav` | 当前文件已存在；槽名 BeybladeSlot0、用户索引 0。不是策划属性表，不应提交或覆盖玩家进度 |
| 玩家与窗口设置 | `Saved/Config/WindowsEditor/GameUserSettings.ini`；自定义镜头 `Saved/FaceCamera.ini` | 用户生成数据。已确认镜头 Pitch=-43、Height=220、Locked=true；美术调整时保留 |
| 引擎默认配置 | `Config/DefaultEngine.ini`、`DefaultGame.ini`、`DefaultInput.ini` | 默认地图、打包、输入等工程配置；区别于玩家个人设置 |
| 日志、报告与历史基线 | `Saved/BattleLogs`、`Saved/Logs`、`docs/reports`、`docs/freeze` | 诊断/历史资料；不是当前调参的唯一来源。旧 Feel85 冻结不再约束已授权的隔离试验 |

打包后的玩家数据位置由 UE 的 Saved 路径及启动方式决定，可能在包旁或用户本地数据目录；不能把编辑器存档路径视为所有版本通用路径。目前核对的是本地存档骨架，未见已接入的账号/云端数据库。

## 旧版试验参数单独管理

`Saved/FeelRef60/work/Source/BeybladePrototype/FeelLabTuning.h` 管发射位置、目标速度及试验开关；`MobilityProfile.h` 管 120 秒、前 90 秒保持 90 档、后 30 秒分段衰减；`SpinPresentation.h` 管旋转表现；该副本的 `BattleSimulation.h` 管试验碰撞常数。

这些仍是隔离源码里的参数，尚未完成外置数据化。正式合入前应迁到同一可读取的调参来源并验证，不能宣称“所有数据已经分离”。旧试验当前绕过菜单/玩家存档流程，因此不写存档不是主工程 Save 骨架缺失。

## 尚待完成的分离与验证

1. 补齐陀螺、UI 内容表，并真正接到运行时资源绑定；现在两表仅模板。
2. 把隔离手感参数和未接入的 tunables 项迁入统一配置；避免表格与源码各维护一套有效值。
3. 确认正式打包会携带原始 CSV，并通过 `GRADE1_DATA loaded_from_csv=1` 等日志验证。旧试验包曾记录 csv=0 并使用内置回退；编辑 CSV 不保证已打包程序自动变化。
4. 后续按需完善设置界面、音频和保存字段的连接；不要为检查而运行会覆盖实际槽位的存档默认值测试。

本次只完善分类、真实状态与交接记录，没有移动 UE 资产、修改游戏数值或读取/重置玩家存档内容。`Saved` 还包含隔离源码与备份，不能整体当缓存删除。

## 修改后的记录约定

- 属性：注明表格键、旧值/新值、同步镜像、运行时读表日志及试玩结论。
- 美术：在 [Grok 美术进度](GROK-ART-PROGRESS.md) 中记录资源路径、地图/材质引用、截图；文件尚未创建时由 Grok 完工后创建。
- 机制：注明修改源码、验收及基线；手感试验确认后逐项移植，保留工业美术改动。
- 玩家数据：记录结构版本与迁移方式，避免在共享美术素材或属性表中放个人存档。

原方案与历史记录：[三类规格](数据分离三类-规格-2026-10-26.md)、[布局方案](data-layout-数值美术机制-2026-10-26.md)、[变更日志](DATA-LAYOUT-LOG-2026-10-26.md)、[美术交接](GROK-ART-HANDOFF-20261027.md)。

2026-10-27 追加：旧版新增 [1–100 重量调节](FeelLab-weight-controls.md)，独立设置为运行时 Saved/FeelLabWeight.ini；不写玩家进度槽。重量映射与碰撞接入位于隔离源码，尚未合入工业版。

2026-10-27 追加：工业版 [大厅、图鉴与技能实际接入说明](UI-SKILLS-IMPLEMENTED-20261027.md)。技能表 Content/Beyblade/Data/skills-grade1.csv 已读表并与 docs/balance 镜像同步；16 行主被动效果可执行，实际出战仍为五卡池。详情见专项文档，旧方案“主动效果为壳”已过时。

2026-10-27 追加：[单场对战首轮改进](BOUT-GAMEPLAY-20261027.md)：工业版发射角度/力度、程序骨骼动作、倒数/拉绳/释放音效、类型路线倾向、真实末局复盘已接入，31项回归通过；旧隔离包未改。

### 2026-10-28 旧版人物发射预览
说明：OLD-HERO-LAUNCH-20261028.md。仅 Saved/FeelRef60/work：Content/FeelLab/Characters/MaleLauncher_v1 为角色与八段动画，LabSources 保留原始 FBX 和导入脚本，Source/BeybladePrototype/LabLaunchPresentation.h 为发射时序。原旧包 Builds/Windows-Feel85-60s 已更新。工业版物理及权威 CSV 未变。

