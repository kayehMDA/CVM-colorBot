# Aimbot 模式: Silent

返回: [Aimbot](../Aimbot.md) | [Sec Aimbot](../Sec-Aimbot.md)

## Main Aimbot

| UI Name | Config Key | Type | Range/Options | Default | Description | Notes |
|---|---|---|---|---|---|---|
| Distance (Multiplier) | `silent_distance` | float | `0.1` 到 `10.0` | `1.0` | 目标修正距离倍率。 | 值越大，修正幅度可能越大。 |
| Delay (ms) | `silent_delay` | float | `0.001` 到 `300.0` ms | `100.0` | Silent 动作开始前延迟。 | 当前配置以毫秒值保存。 |
| Move Delay (ms) | `silent_move_delay` | float | `0.001` 到 `300.0` ms | `500.0` | 移动到目标阶段延迟。 | 值越大，Silent 序列响应越慢。 |
| Return Delay (ms) | `silent_return_delay` | float | `0.001` 到 `300.0` ms | `500.0` | 回位阶段延迟。 | 建议与 Move Delay 联动调整。 |
| FOV Size | `fovsize` | float | `1` 到 `1000` | `100` | 主 Silent 模式使用的 FOV。 | 与主其他模式共用此键。 |

## Sec Aimbot

| UI Name | Config Key | Type | Range/Options | Default | Description | Notes |
|---|---|---|---|---|---|---|
| X-Speed | `normal_x_speed_sec` | float | `0.1` 到 `2000` | `2` | 当前 UI 下副 Silent 使用此 X 速度键。 | 标签页未暴露独立 `silent_*_sec` 参数。 |
| Y-Speed | `normal_y_speed_sec` | float | `0.1` 到 `2000` | `2` | 当前 UI 下副 Silent 使用此 Y 速度键。 | 标签页未暴露独立 `silent_*_sec` 参数。 |
| FOV Size | `fovsize_sec` | float | `1` 到 `1000` | `150` | 当前 UI 下副 Silent 使用此 FOV 键。 | 与主 `fovsize` 独立。 |

## Practical tuning tips

1. 先定 `fovsize`；FOV 过大时，复杂场景下 Silent 触发会更不稳定。
2. 延迟建议按顺序调：`silent_delay` -> `silent_move_delay` -> `silent_return_delay`。
3. 如果触发明显偏晚，先减 `silent_delay`；如果移动阶段拖沓，再减 `silent_move_delay`。
4. 回位不自然时，只改 `silent_return_delay`，不要一次联动全部延迟。
5. `silent_distance` 建议先围绕 `1.0` 微调，确认修正不足再逐步增加。
6. 副 Silent 目前用的是 `normal_x_speed_sec`、`normal_y_speed_sec`、`fovsize_sec`，请保守调节。
7. 务必在近/中/远三种距离都验证一次，避免只在单一距离有效。
