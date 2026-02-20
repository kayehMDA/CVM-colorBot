# Aimbot 模式: NCAF

返回: [Aimbot](../Aimbot.md) | [Sec Aimbot](../Sec-Aimbot.md)

## Main Aimbot

| UI Name | Config Key | Type | Range/Options | Default | Description | Notes |
|---|---|---|---|---|---|---|
| Alpha (Speed Curve) | `ncaf_alpha` | float | `0.1` 到 `5.0` | `1.5` | NCAF 速度曲线形状参数。 | 值越高会改变速度攀升曲线。 |
| Snap Boost Factor | `ncaf_snap_boost` | float | `0.01` 到 `2.0` | `0.3` | 触发 snap 条件时的额外加速因子。 | 可提升锁定时的激进程度。 |
| Max Step | `ncaf_max_step` | float | `1` 到 `200` | `50.0` | 单次更新最大移动步长。 | 限制突发大幅位移。 |
| Min Speed Multiplier | `ncaf_min_speed_multiplier` | float | `0.01` 到 `1.0` | `0.01` | 自适应速度倍率下限。 | 防止移动过慢。 |
| Max Speed Multiplier | `ncaf_max_speed_multiplier` | float | `1.0` 到 `20.0` | `10.0` | 自适应速度倍率上限。 | 防止移动过快。 |
| Prediction Interval (ms) | `ncaf_prediction_interval` | float (seconds in config) | UI `1` 到 `100` ms | `0.016` s | NCAF 目标预测时间间隔。 | UI 以毫秒显示，配置以秒保存。 |
| Snap Radius (Outer) | `ncaf_snap_radius` | float | `10` 到 `500` | `150.0` | 外层 snap 作用半径。 | 应大于 near radius。 |
| Near Radius (Inner) | `ncaf_near_radius` | float | `5` 到 `400` | `50.0` | 内层近距离精细控制半径。 | 应小于 snap radius。 |

## Sec Aimbot

| UI Name | Config Key | Type | Range/Options | Default | Description | Notes |
|---|---|---|---|---|---|---|
| Alpha (Speed Curve) | `ncaf_alpha_sec` | float | `0.1` 到 `5.0` | `1.5` | 副 NCAF 速度曲线参数。 | 与主自瞄参数独立。 |
| Snap Boost Factor | `ncaf_snap_boost_sec` | float | `0.01` 到 `2.0` | `0.3` | 副 NCAF snap 加速因子。 | 与主自瞄参数独立。 |
| Max Step | `ncaf_max_step_sec` | float | `1` 到 `200` | `50.0` | 副 NCAF 单次更新最大步长。 | 与主自瞄参数独立。 |
| Min Speed Multiplier | `ncaf_min_speed_multiplier_sec` | float | `0.01` 到 `1.0` | `0.01` | 副 NCAF 速度倍率下限。 | 与主自瞄参数独立。 |
| Max Speed Multiplier | `ncaf_max_speed_multiplier_sec` | float | `1.0` 到 `20.0` | `10.0` | 副 NCAF 速度倍率上限。 | 与主自瞄参数独立。 |
| Prediction Interval (ms) | `ncaf_prediction_interval_sec` | float (seconds in config) | UI `1` 到 `100` ms | `0.016` s | 副 NCAF 预测时间间隔。 | UI 以毫秒显示，配置以秒保存。 |
| Snap Radius (Outer) | `ncaf_snap_radius_sec` | float | `10` 到 `500` | `150.0` | 副 NCAF 外层 snap 半径。 | 应大于副 near radius。 |
| Near Radius (Inner) | `ncaf_near_radius_sec` | float | `5` 到 `400` | `50.0` | 副 NCAF 内层 near 半径。 | 应小于副 snap radius。 |

## Practical tuning tips

1. 先定几何关系：先定 `ncaf_snap_radius`，再定明显更小的 `ncaf_near_radius`。
2. 再调运动上限：若跳变明显，优先降低 `ncaf_max_step`。
3. 再调曲线形状：`ncaf_alpha` 建议小步改（每次 `0.1` 到 `0.2`）。
4. 倍率做边界保护：近距离跟不上可微升 `ncaf_min_speed_multiplier`；过猛可降 `ncaf_max_speed_multiplier`。
5. `ncaf_snap_boost` 建议最后调，过高会在阈值附近产生突兀吸附。
6. `ncaf_prediction_interval` 要接近你的帧节奏，预测不稳就逐步下调。
7. `*_sec` 参数按同顺序调，但建议比主自瞄略保守，确保副模式稳定兜底。
