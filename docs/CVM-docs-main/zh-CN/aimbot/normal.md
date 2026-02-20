# Aimbot 模式: Normal

返回: [Aimbot](../Aimbot.md) | [Sec Aimbot](../Sec-Aimbot.md)

## Main Aimbot

| UI Name | Config Key | Type | Range/Options | Default | Description | Notes |
|---|---|---|---|---|---|---|
| X-Speed | `normal_x_speed` | float | `0.1` 到 `2000` | `3` | 主自瞄水平跟踪速度。 | 数值越大，响应越快。 |
| Y-Speed | `normal_y_speed` | float | `0.1` 到 `2000` | `3` | 主自瞄垂直跟踪速度。 | 建议与 X-Speed 平衡调整。 |
| Smoothing | `normalsmooth` | float | `1` 到 `30` | `30` | 主自瞄移动平滑强度。 | 数值越高通常越稳但更慢。 |
| FOV Size | `fovsize` | float | `1` 到 `1000` | `100` | 主自瞄视野范围大小。 | 控制候选目标区域。 |
| FOV Smooth | `normalsmoothfov` | float | `1` 到 `30` | `30` | 主自瞄 FOV 过渡平滑。 | 可减少 FOV 边缘突变。 |

## Sec Aimbot

| UI Name | Config Key | Type | Range/Options | Default | Description | Notes |
|---|---|---|---|---|---|---|
| X-Speed | `normal_x_speed_sec` | float | `0.1` 到 `2000` | `2` | 副自瞄水平跟踪速度。 | 与主自瞄速度独立。 |
| Y-Speed | `normal_y_speed_sec` | float | `0.1` 到 `2000` | `2` | 副自瞄垂直跟踪速度。 | 与主自瞄速度独立。 |
| Smoothing | `normalsmooth_sec` | float | `1` 到 `30` | `20` | 副自瞄移动平滑强度。 | 与主自瞄平滑独立。 |
| FOV Size | `fovsize_sec` | float | `1` 到 `1000` | `150` | 副自瞄视野范围大小。 | 与主自瞄 FOV 独立。 |
| FOV Smooth | `normalsmoothfov_sec` | float | `1` 到 `30` | `20` | 副自瞄 FOV 过渡平滑。 | 与主自瞄 FOV 平滑独立。 |

## Practical tuning tips

1. 先保持默认值，在固定测试场景连续测试 2-3 分钟后再改参数。
2. 先单独调 `normal_x_speed`（只看水平目标），再调 `normal_y_speed`（补垂直偏差）。
3. 如果出现过冲，先小步降低速度（每次约 `0.2` 到 `0.5`），再考虑加平滑。
4. `normalsmooth` 用来压微抖；如果变得太迟缓，先小降平滑再微加速度。
5. `fovsize` 只在目标重捕慢时再加大；若误选目标多，优先缩小 FOV。
6. 如果副自瞄是兜底，建议 `*_sec` 参数比主自瞄稍慢、稍平滑。
7. 游戏内灵敏度变化后（`in_game_sens`）通常要重新微调速度与平滑。
