**方法**：同一网络两次 forward。History-Free 分支遮掉历史预测当前 chunk 的 x0；History-Conditioned 分支在 sg[x̂_free] 上只预测残差（latent fusion）。互信息链式分解：历史信息 = 当前输入本可推出的部分 + 只有历史能给的部分；teacher forcing 下模型会从干净历史里抄前者，推理时这部分累积误差。另把 Wan VAE 换成逐帧 image VAE，temporal patch 层把 4 帧 latent 合并输入，DiT 计算量不变。x0-prediction。

**受控实验**（4M 视频，256p，VBench）

| 配置 | 分数 |
|---|---|
| 双向 | 77.28 |
| 因果基线 | 71.14 |
| + x0 | 72.41 |
| + CRP | 77.09 |
| + image VAE | 77.48 |

- rollout 与 teacher forcing 的质量差：0.138 → 0.066 → 0.039。
- 去掉 CRP 时训练 loss 最低但 VBench 最差，符合「过度依赖历史」的假设。
- 完整模型：从 SANA 图像模型起步，15M 视频训练 2B 因果模型，VBench 82.78；Quality 子项比蒸馏系模型低 1–4 分。
- 推理 50 步、每步 2 次 forward；只评 5s。
