**数据**：4.1k 小时原始数据 → 3.0k 小时：去掉伪立体声和非 diegetic 声音；VGGT-Ω + Depth Anything V3 恢复度量尺度位姿；三轨 caption。

**训练**：先训控制模块 → 视频分支 → 全量；因果蒸馏 = ODE 初始化 → self-forcing（DMD）+ online trajectory distillation（PF-ODE 目标）→ 长时 streaming 微调。

**HelixBench（1015 例；DeSync 只算 165 个 Event 例）**

| 模型 | KL ↓ | FAD ↓ | DeSync ↓ | Spatial ↑ |
|---|---|---|---|---|
| LTX-2.3（base） | 1.804 | 7.635 | **0.404** | 0.98 |
| EchoWM | 1.953 | 7.747 | 0.675 | 12.65 |
| HelixWorld + AudioX | 2.019 | 3.917 | 1.176 | −5.74 |
| HelixWorld + ThinkSound | 2.234 | 6.188 | 0.424 | 14.85 |
| HelixWorld + PrismAudio | 2.243 | 6.387 | 0.458 | −9.51 |
| HelixWorld 双向教师 | 1.541 | 3.078 | 0.499 | 33.24 |
| HelixWorld 因果学生 | **1.393** | **2.387** | 0.587 | **41.8** |

- WBench 视觉均分 79.9，低于 Alaya 82.0、EchoWM 81.0、Zing 81.0。
- L_traj 消融：DINOv3 多样性 +21.7%。

**代码证据**（[NoizAI/HelixWorld](https://github.com/NoizAI/HelixWorld) 预览版）

- 每块 4 个 latent 帧：`code/LTX-2.3/projects/helixworld_runtime/scripts/generation_runner.py:24`
- 4 步 schedule (1.0, 0.9, 0.7, 0.4, 0)：`.../scripts/schedule_runtime.py:9`；`generation_core.py` 强制 5 个 sigma 节点
- KV 提交时 detach：`.../scripts/context_cache.py:159-160`
- sink + 最近块：`.../scripts/context_runtime.py:64-84`；发布策略 `history_limit=3, fixed_prefix=1`：`scripts/infer_model.py:31-37`
- 每块重新编码历史：`generation_core.py:250-256` → `context_runtime.py:153-202`
- PRoPE / 动作 MLP：`packages/ltx-core/src/ltx_core/model/transformer/video_control.py:204-206, 209-284`
- 立体声校验：`packages/ltx-core/src/ltx_core/model/audio_vae/model_configurator.py:54`
- `configs/inference_config.json`：768×512，24fps，每轮 121 帧，`audio_video_joint_generation: true`
