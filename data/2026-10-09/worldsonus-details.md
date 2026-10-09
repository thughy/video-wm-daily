**结构**：AR 主干 + flow head；视觉条件 = DINO 特征 + 时间差分（双时间尺度）；causal stereo VAE 改自 SoundReactor；立体声监督来自 FOA 转换；训练期 ShiftNCE 借冻结的同步专家剔除时间模糊的负样本。

**结果**

- VGG 5s：FAD 1.73（PrismAudio 2.09，V-AURA 4.06）。
- Inter. 30s：BiasSkill 15.90（其余 ≤4.19）。
- 30s 流末段 vs 冷启动直接生成：FAD 2.51 vs 2.63。
- prompt 切换增益 G=+0.051，置信区间不含 0；但双匹配率绝对值约 25%。
- DeSync 0.686，双向基线 0.481。
- 用户研究 20 人、40 段视频。

**声道实测**（ffmpeg，1s/2s 窗口，`benchmark_case0002`）

| 时刻 | L−R 差 |
|---|---|
| 0s | 4.9 dB |
| 2s | 19.2 dB |
| 4s | 5.3 dB |
| 5–8s | 约 7–9 dB |

AudioX 基线同一 case：L−R 差信号平均 −90dB（两声道实际相同）。河流→火车 30s case：响度 −35dB → −21dB。宇航员 case：3s 后右声道高 7–12dB（视频分析报的是左声道更响，与实测相反）。

**代码证据**（[NoizAI/WorldSonus](https://github.com/NoizAI/WorldSonus)，CC BY-NC 4.0）

- `push()` 不读未来帧：`worldsonus/streaming.py:9-14`
- SWA 窗口 100 token（每 chunk 2 token，约 5s Ring-KV）：`streaming.py:41,43`
- 切 prompt 只换 prompt KV、保留音频历史：`streaming.py:55`
- flow head 默认 15 步：`streaming.py:17`；CFG 3 路 batch：`streaming.py:43`
- 最大时长需预先给定（分配 RoPE 和 prompt mask）：`streaming.py:12-13`
