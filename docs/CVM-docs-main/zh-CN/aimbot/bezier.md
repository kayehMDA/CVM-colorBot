# Aimbot 模式: Bezier

返回: [Aimbot](../Aimbot.md) | [Sec Aimbot](../Sec-Aimbot.md)

## Main Aimbot

| UI Name | Config Key | Type | Range/Options | Default | Description | Notes |
|---|---|---|---|---|---|---|
| Segments | `bezier_segments` | int | `1` 到 `30` | `8` | Bezier 路径采样段数。 | 段数越高通常插值更平滑。 |
| Ctrl X | `bezier_ctrl_x` | float | `0.0` 到 `100.0` | `16.0` | 曲线路径水平控制点影响量。 | 与 `Ctrl Y` 一起决定曲线形状。 |
| Ctrl Y | `bezier_ctrl_y` | float | `0.0` 到 `100.0` | `16.0` | 曲线路径垂直控制点影响量。 | 与 `Ctrl X` 一起决定曲线形状。 |
| Speed | `bezier_speed` | float | `0.1` 到 `20.0` | `1.0` | 沿 Bezier 曲线移动的速度倍率。 | 数值越高，沿曲线移动越快。 |
| Delay (ms) | `bezier_delay` | float (seconds in config) | UI `0.1` 到 `50.0` ms | `0.002` s | Bezier 分段步进延迟。 | UI 以毫秒显示，配置以秒保存。 |
| FOV Size | `fovsize` | float | `1` 到 `1000` | `100` | 主 Bezier 模式使用的 FOV。 | 与主其他模式共用此键。 |

## Sec Aimbot

| UI Name | Config Key | Type | Range/Options | Default | Description | Notes |
|---|---|---|---|---|---|---|
| Segments | `bezier_segments_sec` | int | `1` 到 `30` | `8` | 副 Bezier 路径段数。 | 与主自瞄参数独立。 |
| Ctrl X | `bezier_ctrl_x_sec` | float | `0.0` 到 `100.0` | `16.0` | 副曲线水平控制点影响量。 | 与主自瞄参数独立。 |
| Ctrl Y | `bezier_ctrl_y_sec` | float | `0.0` 到 `100.0` | `16.0` | 副曲线垂直控制点影响量。 | 与主自瞄参数独立。 |
| Speed | `bezier_speed_sec` | float | `0.1` 到 `20.0` | `1.0` | 副沿曲线移动速度倍率。 | 与主自瞄参数独立。 |
| Delay (ms) | `bezier_delay_sec` | float (seconds in config) | UI `0.1` 到 `50.0` ms | `0.002` s | 副 Bezier 分段步进延迟。 | UI 以毫秒显示，配置以秒保存。 |
| FOV Size | `fovsize_sec` | float | `1` 到 `1000` | `150` | 副 Bezier 模式使用的 FOV。 | 与主 `fovsize` 独立。 |

## Practical tuning tips

1. 先调曲线形状再调速度：先定 `bezier_ctrl_x`、`bezier_ctrl_y`。
2. `bezier_segments` 用来提高轨迹细腻度，建议逐步增加，过高会有延迟感。
3. 形状稳定后，再用 `bezier_speed` 调整体响应速度。
4. 如果整体偏慢，优先减 `bezier_delay`，再考虑提高速度。
5. 调曲线参数时先保持中等 `fovsize`，避免频繁换目标干扰判断。
6. 副模式可先复制主参数，再把 `bezier_speed_sec` 略降做稳妥兜底。
7. 调整 FPS/轮询节奏后要复测，因为 Bezier 步进时序对更新频率很敏感。
