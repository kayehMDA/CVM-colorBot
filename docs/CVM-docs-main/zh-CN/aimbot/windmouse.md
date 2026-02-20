# Aimbot 模式: WindMouse

返回: [Aimbot](../Aimbot.md) | [Sec Aimbot](../Sec-Aimbot.md)

## Main Aimbot

| UI Name | Config Key | Type | Range/Options | Default | Description | Notes |
|---|---|---|---|---|---|---|
| Gravity | `wm_gravity` | float | `0.1` 到 `30.0` | `9.0` | 主 WindMouse 向目标吸引力。 | 值越高路径越直接。 |
| Wind | `wm_wind` | float | `0.1` 到 `20.0` | `3.0` | 主 WindMouse 随机摆动强度。 | 值越高路径随机性越强。 |
| Max Step | `wm_max_step` | float | `1` 到 `100` | `15.0` | 单次更新最大步长。 | 限制突发位移。 |
| Min Step | `wm_min_step` | float | `0.1` 到 `20` | `2.0` | 单次更新最小步长。 | 防止移动停滞。 |
| Min Delay (ms) | `wm_min_delay` | float (seconds in config) | UI `0.1` 到 `50` ms | `0.001` s | 更新间隔最小延迟。 | UI 以毫秒显示，配置以秒保存。 |
| Max Delay (ms) | `wm_max_delay` | float (seconds in config) | UI `0.1` 到 `50` ms | `0.003` s | 更新间隔最大延迟。 | UI 以毫秒显示，配置以秒保存。 |
| Distance Threshold | `wm_distance_threshold` | float | `10` 到 `200` | `50.0` | 距离阈值，用于切换行为。 | 常用于近距离行为切换。 |
| FOV Size | `fovsize` | float | `1` 到 `1000` | `100` | 主 WindMouse 模式 FOV。 | 与主其他模式共用此键。 |

## Sec Aimbot

| UI Name | Config Key | Type | Range/Options | Default | Description | Notes |
|---|---|---|---|---|---|---|
| Gravity | `wm_gravity_sec` | float | `0.1` 到 `30.0` | `9.0` | 副 WindMouse 向目标吸引力。 | 与主自瞄参数独立。 |
| Wind | `wm_wind_sec` | float | `0.1` 到 `20.0` | `3.0` | 副 WindMouse 随机摆动强度。 | 与主自瞄参数独立。 |
| Max Step | `wm_max_step_sec` | float | `1` 到 `100` | `15.0` | 副单次更新最大步长。 | 与主自瞄参数独立。 |
| Min Step | `wm_min_step_sec` | float | `0.1` 到 `20` | `2.0` | 副单次更新最小步长。 | 与主自瞄参数独立。 |
| Min Delay (ms) | `wm_min_delay_sec` | float (seconds in config) | UI `0.1` 到 `50` ms | `0.001` s | 副更新间隔最小延迟。 | UI 以毫秒显示，配置以秒保存。 |
| Max Delay (ms) | `wm_max_delay_sec` | float (seconds in config) | UI `0.1` 到 `50` ms | `0.003` s | 副更新间隔最大延迟。 | UI 以毫秒显示，配置以秒保存。 |
| Distance Threshold | `wm_distance_threshold_sec` | float | `10` 到 `200` | `50.0` | 副距离阈值，用于切换行为。 | 与主自瞄参数独立。 |
| FOV Size | `fovsize_sec` | float | `1` 到 `1000` | `150` | 副 WindMouse 模式 FOV。 | 与主 `fovsize` 独立。 |

## Practical tuning tips

1. 先平衡力项：先调 `wm_gravity`，再加 `wm_wind` 到"自然但可控"的程度。
2. 轨迹太飘就降 `wm_wind`，轨迹太死板就小步升 `wm_wind`。
3. 用 `wm_max_step`/`wm_min_step` 限制节奏：不稳就降最大步长，近点卡顿就升最小步长。
4. `wm_min_delay` 与 `wm_max_delay` 建议设得接近，避免节奏忽快忽慢。
5. `wm_distance_threshold` 控制行为切换距离，近距切换太晚就适当调高。
6. `fovsize` 与 `fovsize_sec` 建议独立调，避免副模式抢主模式目标。
7. 副参数（`*_sec`）可先复制主参数，再略降激进度（如 gravity、max step）。
