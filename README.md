# 爆旋星魂：《开始即结束》

我是一个普通游戏玩家，不会编程，也不会美术。这个陀螺对战项目由我提出想法，主要通过 ChatGPT 完成，3D 模型使用 Tripo 生成。我喜欢它，但它还不完善：玩法、美术和对战体验都还需要优化。现在我要把时间放回找工作上，先停在这里。把源码放出来，希望有人愿意 fork，继续走下去。

**代码、机制文档与纯文本数据按 MIT 开源；全部美术保留权利，需要另行付费授权。** 本仓库没有模型、贴图、人物、场景、UI 图片或 UE 二进制关卡。源码面向编译与继续开发提供；由于缺少原始关卡/美术，不能直接复现视频里的游戏。你可以自行制作替代资产，或通过 GitHub Issue 联系作者协商付费授权。详见 [美术授权](ART_LICENSE.md) 和 [第三方说明](THIRD_PARTY_NOTICES.md)。

> 学我者生，像我者死。
>
> 借走方法，走出自己的路。

## 项目状态

- Unreal Engine C++ 本地陀螺对战原型，含发射、碰撞、技能、计分、选螺、角色选择与本地存档代码。当前没有已完成的线上联机服务，外部 AI 玩家桥接也不是联网对战实现。
- 原工程实际开发引擎为 **Unreal Engine 5.8.4**，`.uproject` 关联 **5.8**。需单独安装引擎、Windows C++ 开发工具和 Windows SDK。
- 原完整工程当前体验入口为 `/Game/Maps/RankedArena_AccentPreview -AvatarSelection`。此源码仓库不含该地图、其依赖或其他美术资源。
- 物理与技能是可玩的简化实现，平衡、动画、美术、关卡衔接与移动端表现仍需继续完善。文档中的历史验证记录不代表本次副本重新完成了引擎编译或试玩。

## 打开、编译与继续运行

1. 将仓库放在短英文路径，例如 `C:\Projects\baoxuan-xinghun`。安装 UE 5.8.4 和支持该引擎的 Visual Studio C++ 工具链/Windows SDK。
2. 右键 `beyblade-unreal-prototype.uproject` 生成 Visual Studio 工程文件，打开生成的解决方案，选择 `Development Editor / Win64`，编译 `BeybladePrototypeEditor`。也可以使用下方 PowerShell 命令。
3. 用 UE 打开 `.uproject`。由于默认配置仍引用原工程地图，美术已排除，可能提示缺失地图/资源；自行新建关卡并替换/移除源码中的软/硬资源引用，然后配置适用的 GameMode、相机、场地与陀螺资产。
4. 补齐资源并配置好地图后再 Play。只有获得原地图及依赖、放回对应 `/Game/...` 路径后，才可用原体验入口运行。这里不承诺解压即玩。

```powershell
$ue = 'C:\Program Files\Epic Games\UE_5.8'
$project = Join-Path $PWD 'beyblade-unreal-prototype.uproject'
& "$ue\Engine\Build\BatchFiles\Build.bat" BeybladePrototypeEditor Win64 Development "-Project=$project" -WaitMutex -NoHotReloadFromIDE
# 仅补齐原关卡和全部依赖后使用：
& "$ue\Engine\Binaries\Win64\UnrealEditor.exe" $project /Game/Maps/RankedArena_AccentPreview -game -AvatarSelection
```

## 目录

| 路径 | 内容 |
|---|---|
| `Source/BeybladePrototype` | 仿真、技能、赛制、UI、存档及 UE 自动化测试 |
| `Config` | 工程默认设置；已移除 Android 文件服务器凭据段和本机编辑器历史 |
| `Content/Beyblade/Data` | 原样保留的运行时 CSV 文本，不含美术 |
| `Content/Python` | 原工程编辑器 Python 辅助代码 |
| `Tools` | 原有制作、检查、导入和 AI 玩家脚本；许多依赖本机路径与未公开资源 |
| `docs` | 精选机制说明、数据镜像与原始 Tripo 来源文字记录 |
| `HANDOFF.md` | 接手重点、测试与参数入口 |
| `MANIFEST.sha256` | 本次副本逐文件 SHA-256（不包含清单自身） |

不要直接批量运行 `Tools`：其中包括历史修补、资源导入和改写脚本，部分路径仍指向原开发机器；先阅读并改为你自己的路径和资源。`deepseek_player_headless.py` 从当前进程的 `SK` 环境变量读取你自己的 API 密钥，GUI 版本通过输入框提供密钥；不要把密钥写入文件或提交仓库。桥接依赖本地已打包 Windows 游戏，此仓库没有打包程序。

## 已知限制与交接

源码/数据原样复制，配置只做公开所需的脱敏；未为缺失美术制作替代品。没有携带 `Saved`、用户进度、构建产物、备份、私人日志、参考视频或全部 AI 工作记录。CSV 存在不等于所有参数均已外置；一些资源绑定、技能和手感仍在 C++ 中。`Content/Beyblade/Data` 是运行时数据，`docs/balance`、`docs/content` 是历史镜像，部分与当前运行表不同，不要用旧镜像覆盖运行表。自动化用例中有需要资产/关卡的检查，源码副本无法完整运行这些检查。完整说明见 [HANDOFF](HANDOFF.md)。

---

# Baoxuan Xinghun — The Beginning Is the End

I am an ordinary game player who cannot program or make art. I supplied the ideas; this project was made mainly with ChatGPT, and the 3D models were generated with Tripo. I care about this spinning-top battle prototype, but its gameplay, visuals and battles still need work. I now need to focus on finding a job, so I am stopping development for now. I am sharing the source in the hope that someone will fork it and continue.

**Code, included documentation and plain-text game data are MIT licensed. All artwork is reserved and requires a separate paid license.** Models, textures, characters, environments, UI images and binary UE levels are not included. The source is provided for compilation and further development; it cannot reproduce the demonstrated game without replacement assets or separately licensed originals. Contact the author through a GitHub Issue to discuss paid asset licensing. See [ART_LICENSE](ART_LICENSE.md) and [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md).

> Learn from the approach; find your own path.

The original development engine is **Unreal Engine 5.8.4**; the project association is **5.8**. Install the engine, a compatible Windows C++ toolchain and Windows SDK separately. Generate Visual Studio project files from the `.uproject`, build `BeybladePrototypeEditor` in `Development Editor / Win64`, then open it in Unreal. The PowerShell commands above provide the equivalent build command. This handoff has not been recompiled or play-tested as a standalone art-free copy.

The original experience launches with `/Game/Maps/RankedArena_AccentPreview -AvatarSelection`. That map and its dependencies are absent here. Create a replacement level and replace/remove asset references in the code, or restore properly licensed originals at their original `/Game/...` paths before trying that launch command. The default map settings still refer to original levels, so missing-resource messages are expected until this work is done.

This is a local prototype, with simplified physics, skills, scoring, selection and local saves. It does not provide a completed online multiplayer service. Balance, animation, visual polish, asset integration and mobile validation remain unfinished. Some settings and asset bindings remain hardcoded; not every CSV field is wired into runtime behavior. Automation tests that require missing art or maps cannot pass in this source-only handoff.

The directory table above maps the project. Read [HANDOFF.md](HANDOFF.md) before making changes. `Tools` contains historical import/patch scripts with machine-specific paths and dependencies; review each script before running it. The headless AI-player bridge reads your API credential from the process environment variable `SK`; never commit credentials. It also expects a separately packaged Windows game, which is not included. No engine files, builds, saves, private logs, backup trees, reference videos or complete AI chat history are distributed.
