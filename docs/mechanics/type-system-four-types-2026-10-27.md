# 四类型机制定稿 · Grade1（2026-10-27）

> 作者：系统机制设计执行器  
> 用户授权：整表四类型 + Grade1 数值锁定；文案「持久型」禁用「耐力型」  
> **Feel85 冻结常数只引用、禁止改写进工程建议**：`SPIN_KICK` / `RESTITUTION` / `ContactFeelTrial` / `KickReferenceSpeed` / `MaxFrames`  
> 数据分离：正文用 key；裸数只在 `docs/balance/*.csv`

权威数值源：

- 行表：`docs/balance/grade1-loadouts.csv`
- 键表：`docs/balance/tunables-template.csv`（`G1_ATK_*` … `G1_BAL_*`）
- 内容绑螺：`docs/content/content-beys.csv`

---

## 1. 四类型语义（本阶段无克制）

| type | 中文 | 角色 |
|------|------|------|
| ATTACK | 攻击型 | 高 Attack、低 Defense/Mass、快衰减 → 易打出界、易先停 |
| DEFENSE | 防御型 | 高 Defense、中 Mass、中慢衰减 → 抗撞 |
| STAMINA | **持久型** | 最高 Mass、最慢衰减 → 超时动量优、长局（**禁用「耐力型」**） |
| BALANCE | 均衡型 | 攻防接近、Mass 略高于 1、衰减贴近中位锚 |

`TypeMul_ATK` / `TypeMul_DEF` / `TypeMul_STA` / `TypeMul_BAL` = **1.0**（预留键；本阶段恒 1，无克制乘区）。

---

## 2. 结束优先级（不可调换）

```
ringout  →  spinout  →  timeout(residual_momentum)
```

| 次序 | 原因 | 判定 | 胜者 |
|------|------|------|------|
| 1 | ringout | 越过出界门控（现行几何；本表不改 rim） | 仍在场内方 |
| 2 | spinout | 任一方 `Spin <= SpinStopThreshold` | 另一方（先停者负） |
| 3 | timeout | 打满 `TimeLimitSeconds`（键见 freeze）且双方仍在转 | `M_i = \|V_i\| * Mass_i` 较大者；极近 → DRAW |

---

## 3. 转速衰减

```
Spin_0 = 1.0
Spin *= Exp(-k * dt)
SpinStopThreshold = 0.02
```

中位锚（设计意图）：`k_mid = -ln(0.02) / 30 ≈ 0.1304 /s` → 约 30s 触停转。

衰减序（硬约束）：**ATTACK > BALANCE > DEFENSE > STAMINA**  
即 `G1_ATK_SpinDecay` > `G1_BAL_SpinDecay` > `G1_DEF_SpinDecay` > `G1_STA_SpinDecay`。

---

## 4. Grade1 数值（权威在 CSV；正文只引用 key）

| type | Attack key | Defense key | Mass key | spin_decay_k key | 约停转 |
|------|------------|-------------|----------|------------------|--------|
| ATTACK | `G1_ATK_Attack` | `G1_ATK_Defense` | `G1_ATK_Mass` | `G1_ATK_SpinDecay` | ~24s |
| DEFENSE | `G1_DEF_Attack` | `G1_DEF_Defense` | `G1_DEF_Mass` | `G1_DEF_SpinDecay` | ~32s |
| STAMINA | `G1_STA_Attack` | `G1_STA_Defense` | `G1_STA_Mass` | `G1_STA_SpinDecay` | ~38s |
| BALANCE | `G1_BAL_Attack` | `G1_BAL_Defense` | `G1_BAL_Mass` | `G1_BAL_SpinDecay` | ~30s |

行级对照：`grade1-loadouts.csv` 四行（type=ATTACK/DEFENSE/STAMINA/BALANCE, grade=1）。

硬约束：

- `G1_STA_Mass` **最高**（超时动量定位给持久）
- BALANCE Mass（`G1_BAL_Mass`）低于 DEF/STA，不抢持久定位
- 衰减序见上节

---

## 5. BALANCE 审改说明（临时 → 定稿）

| 字段 | 临时（ray/UE 已落地） | **定稿** | 理由 |
|------|----------------------|----------|------|
| Attack / Defense / Mass | 1.10 / 1.10 / 1.05 | **不变** | 攻防接近、Mass 略高于 1 |
| `spin_decay_k` / `G1_BAL_SpinDecay` | **0.135** | **0.130** | 对齐 `k_mid≈0.1304`；约停转 ~30s；仍满足 ATK>BAL>DEF>STA |

**工程同步要求（数据/回退字面量，非 Feel）**：内置回退与 CSV 中 BALANCE `spin_decay_k` 从 `0.135` 改为 `0.130`；自动化断言同步。  
**禁止**借此改 Feel85 五常数源码。

---

## 6. 碰撞公式（乘属性；Feel 常数只引用）

```
kickScale = clamp(closing / KickReferenceSpeed, 0, 1)
ExtraOntoOther = SPIN_KICK * kickScale * Attack_self * (2 / (1 + Defense_other))
```

引用键（`frozen=true`，见 `tunables-template.csv`）：

- `SPIN_KICK`
- `RESTITUTION`
- `ContactFeelTrial`
- `KickReferenceSpeed`
- `MaxFrames`（及 `TimeLimitSeconds`）

规则：

- Mass **不**进碰撞冲量（本阶段）
- Attack / Defense **不**进超时动量
- `Attack=Defense=1` 时与 Feel85 等大反向冲量一致 → ContactWeight 自动化须保持绿
- `TypeMul_* = 1.0`，本阶段不进公式乘区

---

## 7. 八只英雄绑定（content；外观路径以 content 表为准）

| bey_id | 名 | type | 标记 |
|--------|----|------|------|
| chifeng | 赤锋 | ATTACK | 定妆 |
| bilei | 壁垒 | DEFENSE | 定妆 |
| changxuan | 长旋 | STAMINA | 定妆 · 文案**持久型** |
| hengblade | 衡刃 | BALANCE | 定妆 |
| chiwen | 炽纹 | ATTACK | 侧视新批 |
| huangkai | 煌铠 | DEFENSE | 侧视新批 |
| cuipan | 翠磐 | STAMINA | 侧视新批 · 文案**持久型** |
| shuanghuan | 霜环 | BALANCE | 侧视新批 |

- mesh / portrait 等路径：**只引用** `docs/content/content-beys.csv`，本文不复写裸路径堆。
- **侧视四只是新英雄，禁止覆盖定妆四只外观资产**。

---

## 8. 禁止项

1. 禁止改 Feel85：`SPIN_KICK` / `RESTITUTION` / `ContactFeelTrial` / `KickReferenceSpeed` / `MaxFrames`（及同源 `TimeLimitSeconds` 墙钟约定）
2. 禁止把 Grade1 裸数散写进源码而不走 CSV / `G1_*` 键（内置回退仅作离线缺表兜底，须与 CSV 一致）
3. 禁止 UI/字符串使用「耐力型」；统一「持久型」
4. 禁止用侧视批 mesh 覆盖定妆四只

---

## 9. 相关路径

- 本机制：`docs/mechanics/type-system-four-types-2026-10-27.md`
- UE 验收：`docs/mechanics/type-system-ue-acceptance-2026-10-27.md`
- 摘要表：`docs/balance/min-mech-table-grade1.md`
- 变更条：`docs/reports/MECH-TYPE4-LOCK-2026-10-27.md`
