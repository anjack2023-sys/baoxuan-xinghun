# 单场对战第一轮改进 2026-10-27

范围：当前工业场馆版；旧手感隔离包不改。备份 Saved/Backups/before-launch-gameplay-20261027。

## 发射
- 准备界面角度 -45 至 +45 度，力度 70 至 120%；按钮与 A/D、W/S 同一路径，每次5。
- 角度旋转初始速度方向，力度乘初速度；不增加基础旋转寿命，后续仍使用已有速度衰减和恢复逻辑。
- 1.5秒倒数/准备动作，随后0.6秒飞行落盘；落盘前冻结物理帧，避免演出消耗对战时间。
- 点击/空格不能重复发射；R 或回大厅取消演出，出界落地锁保留。
- 使用已有41骨人物，运行时 PoseableMesh 驱动脊柱、头部、双臂及前臂；是程序骨骼动作第一版，不是精修动捕。新增三段程序音效 Count/Pull/Release，落盘复用已有碰撞样本。

## 类型
- interactive 才启用 bTacticalSteering；ProtoAuto 与默认仿真不启用。
- 攻击：温和朝对手转向；防御：小圈守中；持久：中圈巡航；均衡：每2秒交替接近/巡航。
- 只改变航向，不直接添加速度；碰撞后18帧不转向，末段移动因子低于0.25停用。
- 不改 SPIN_KICK / RESTITUTION / 现有类型CSV / 技能表 / 质量基线 / 胜负优先级。
- 这套路线倾向是首轮可试玩方案，不是完整陀螺动力学，也未声称四类型已平衡。

## 结算
- 按真实 Reason / Winner 解释出界、爆裂、陷阱停转、自然停转、超时残余动量和平局。
- 出界只报告最近0.5秒内是否发生碰螺，不把相关性直接写成对手击飞。
- 显示用时、碰螺次数、最强闭合速度、每方墙/障碍接触次数、P1发射设定/主动次数和剩余旋转值。
- 比赛结算明确标记末局复盘，避免把末局数据当全场统计。

## 文件
Source/BeybladePrototype/BoutPresentation.h：发射设定/按钮命中/类型说明/原因解释。
BattleSimulation.h：路线倾向与只读复盘统计；PrototypeBattle.cpp/h：输入、动作、演出和声音；ArtHUD.cpp：准备与复盘UI。
Content/Beyblade/Audio/S_LaunchCount、S_LaunchPull、S_LaunchRelease。
Tools/make_launch_audio.py、import_launch_audio.py、check_bout_presentation.py：声音制作和引擎内演出检查。

## 验证
编辑器编译通过；首轮31/31测试通过；布局调整后再次运行，31/31通过。
第一次实际PIE日志证实41骨人物、倒数/拉绳/释放音效均触发，LAUNCH_LANDED simulation_frame=0。
完整PIE一局通过：23.8667秒、9次碰螺、P2爆裂、P1得2分；无场内缺面报错。已检查 launch-action.png / launch-battle.png / launch-recap.png，人物未被设置面板遮挡，复盘文字不遮下一局按钮。尚未真机验证安卓触摸/性能，也未把本轮重打包到旧Windows发行ZIP或上传TapTap。
