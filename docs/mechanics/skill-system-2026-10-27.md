# 技能系统定稿 · Grade1 八螺 · 类型条件递增解锁（对齐 ray CSV · 2026-10-27）

> 作者：系统机制设计  
> **数值权威**：`docs/balance/skills-grade1.csv` + `skills-grade1-overview.csv`（ray 维护；**勿擅自改表**）  
> UI 口径：对战 HUD 主动技能按钮短案 **v4**（`docs/planner/`；已与权威 CSV 同数：quiet_spin / window_hit_bey_and_wall / 攻防撞次 均为 5/10/15/20）  
> 类型基线：`docs/mechanics/type-system-four-types-2026-10-27.md`  
> **Feel85 禁止改**：`SPIN_KICK` / `RESTITUTION` / `ContactFeelTrial` / `KickReferenceSpeed` / `MaxFrames`  
> `TypeMul_*=1.0`；技能不是克制矩阵



---

## 1. 总规则

### 1.1 槽位

| 槽 | 数量/螺 | 触发 | 玩家控制 |
|----|---------|------|----------|
| passive | 1 | `on_spawn` 或事件（造成碰撞/边缘区） | 无按钮 |
| active | 1 | `player_button` | 常驻键；条件达标可点；**自选是否释放** |

### 1.2 主动主循环（废止时间门 CD）

**废止**：开局 3s 就绪、固定 8s CD、`charges:1` / `cd:Ns` 作为主规则。

**现行**：

1. 战斗态右下**常驻**主动键（灰也显示）
2. 本局累计/连段达当前门槛 N → **就绪**
3. 玩家可点可不点；点后效果触发、键回灰、**下一门槛升高**（序列 5→10→15→20）
4. 新一局：进度清零、门槛回到序列首项

### 1.3 类型条件（用户已锁 · 2026-10-27）

| 类型 | condition | 语义 | `cd_or_charges` 列 |
|------|-----------|------|-------------------|
| **ATTACK** | `hits_dealt_ge_N_escalating:5/10/15/20` | 本局对对手有效碰撞次数达 N | `escalating_hits` |
| **DEFENSE** | `hits_taken_ge_N_escalating:5/10/15/20` | 本局被对手有效碰撞次数达 N | `escalating_hits` |
| **STAMINA（持久）** | `quiet_spin_ge_N_escalating:5/10/15/20` | **连续转满 N 秒**，且期间**未碰螺 / 墙 / 障碍**；一碰则安静连转计时清零 | `escalating_quiet_s` |
| **BALANCE（均衡）** | `window_hit_bey_and_wall_ge_N_escalating:5/10/15/20` | 长度为 N 秒的窗口内，**须撞到螺且撞到墙（各≥1 次）**；障碍是否算「墙」以实现备注为准 | `escalating_window_s` |

说明：

- 攻/防：用户确认「没问题」，保持撞次 / 被撞次。
- 持久：强调**安静连转**——碰任何螺、墙、障碍即打断并重计。
- 均衡：强调**时间窗内两类接触都齐**——窗长随档位 N 升（5/10/15/20 秒），窗内须撞螺**且**撞墙（各≥1）才就绪。
- 有效对手碰撞（攻）：Closing>0 的对手侧 Hit，与 Feel 记账同源。

### 1.4 与 Feel 边界

允许：Attack/Defense/Mass 临时乘、spin_decay_k 乘、ExtraOntoOther 派生乘、入站踢偏乘、Reflect 比例、Wear 乘、**击飞率（RingoutRateAdd）结算修正**。

禁止：改 Feel85 五常数字面量；用技能做类型克制表。

```
kickScale = clamp(closing / KickReferenceSpeed, 0, 1)
ExtraOntoOther = SPIN_KICK * kickScale * Attack_self * (2 / (1 + Defense_other))
```

击飞率 ≠ 改 SPIN_KICK；≠ 自动 XTR。

---

## 2. 对战按钮两态

| 态 | 条件 | UI | 输入 |
|----|------|-----|------|
| 灰 | 未达当前门槛 | 半透明；进度可读（撞次 `3/5`、安静秒 `2.1/5`、窗内是否已撞螺且撞墙） | 点击无效 |
| 就绪 | 达标 | 高亮 | 可点；可不点至局终 |
| 释放后 | 效果窗内 | 剩余持续 | 回灰并升门槛 |

---

## 3. 八螺一览（先类型再陀螺；裸数以 CSV 为准）

### 3.1 ATTACK（撞对手次）

| bey | 被动 | 主动 |
|-----|------|------|
| **赤锋** 定妆 | 赤锋锋势：上场 Attack×1.10 | 锋芒一击：5/10/15/20；Attack×1.20 + RingoutRateAdd+0.10，持续 3s |
| **炽纹** 侧视 | 炽纹追击：造成碰撞后 2s Attack×1.08 | 炽焰冲锋：5/10/15/20；下一记 Extra×1.35 |

### 3.2 DEFENSE（被撞次）

| bey | 被动 | 主动 |
|-----|------|------|
| **壁垒** 定妆 | 壁垒沉着：上场 Defense×1.08 | 铁壁：被撞 5/10/15/20；Defense×1.25，持续 3.5s |
| **煌铠** 侧视 | 煌铠外缘：外圈 Defense×1.12 | 金障回击：被撞 5/10/15/20；入站×0.75 + Reflect 0.25（不改 RESTITUTION） |

### 3.3 STAMINA / 持久（安静连转秒）

| bey | 被动 | 主动 |
|-----|------|------|
| **长旋** 定妆 | 长旋绵延：上场衰减×0.92 | 回春延转：安静转满 5/10/15/20s；衰减×0.75，持续 4s |
| **翠磐** 侧视 | 翠磐抗磨：上场磨损×0.88 | 磐石沉坠：同安静条件 5/10/15/20s；Mass×1.15，持续 5s |

实现要点：安静计时在碰螺/墙/障碍时**清零**；释放成功后 N 升档，计时重新从 0 攒下一档。

### 3.4 BALANCE / 均衡（窗口内撞螺且撞墙）

| bey | 被动 | 主动 |
|-----|------|------|
| **衡刃** 定妆 | 衡势微均：上场 Atk/Def/Mass×1.05 | 中正爆发：窗长 5/10/15/20s 内须撞螺且撞墙（各≥1）；Atk×1.15 + Def×1.10，持续 3s |
| **霜环** 侧视 | 霜环冷衡：衰减×0.95 + Defense×1.05 | 霜缚：同「撞螺且撞墙」窗口条件；对手衰减×1.12，持续 3s |

实现要点：当前档窗长 = N；窗滑动或从局开始/上次释放后起算须在 UE 实现注记中写清（建议：就绪判定用「过去 N 秒内撞螺≥1 且撞墙≥1」）。

---

## 4. 数据文件

| 文件 | 角色 |
|------|------|
| `docs/balance/skills-grade1.csv` | **权威数值表** |
| `docs/balance/skills-grade1-overview.csv` | 给人读的类型序总览 |
| `docs/balance/tunables-template.csv` | `SK_*`；Feel 冻结行勿动 |
| `docs/mechanics/skill-system-ue-acceptance-2026-10-27.md` | UE 验收 |

微调数值：**先跟 ray**。

---

## 5. 禁止项

1. 禁止改 Feel85 五常数  
2. 禁止恢复 3s/8s CD / charges 主循环  
3. 禁止擅自改权威 CSV  
4. 禁止 UI「耐力型」；用「持久型」  
5. 禁止同型定妆/侧视技能完全复制  
6. 禁止把持久条件写成「只要转满 N 秒可碰」——必须安静无碰  

## 6. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-10-27 | 对齐撞次递增表 |
| 2026-10-27 | **用户锁**：持久→`quiet_spin_ge_N`；均衡→`window_hit_bey_and_wall_ge_N`；攻防仍撞次/被撞；废止持久「低转+撞」、均衡「总碰撞」旧条件 |
| 2026-10-27 | **HUD v4** 与 CSV 同数确认；去掉双口径提示 |
| 2026-10-27 | **用户纠正**：均衡 `window_hit_bey_and_wall`（窗内撞螺且撞墙各≥1）；废止 `window_hit_any`（或） |
