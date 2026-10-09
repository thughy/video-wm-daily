**训练设置**：rank-128 LoRA；每个 chunk F=34 帧；16 张 GPU 训练 2 个 epoch，lr 1e-4，训练 clip 5–10s。few-step 一侧直接用公开的 [lightx2v/Minimax-h3-Turbo](https://huggingface.co/lightx2v/Minimax-h3-Turbo)，**没有和 causal adapter 联合训练过**。

**基线**（全部共用同一 backbone 和 pipeline）：Teacher（50 步双向）、Whole-seg（4 步双向）、Chained-DA（先蒸馏再因果化，OmniForcing 式）、Chained-AD（先因果化再蒸馏，causal-forcing++ 路线，带 anchor 的 checkpoint）、Decoupled-50。

| 指标（held-out，4 步 AR） | PAC | Chained-DA | Chained-AD | Teacher |
|---|---|---|---|---|
| IQA ↑ | **0.914** | 0.854 | — | 0.908 |
| Sync-C ↑ | 7.44 | — | **8.02** | 8.41 |
| FAD ↓ | **3.19** | 5.02 | — | — |
| WER ↓ | 0.127 | — | — | 0.041 |

- Whole-seg 与教师几乎一样（Sync-C 8.403 vs 8.412），说明「4 步不够」解释不了后面的差距，差距来自因果化方式。
- public 集（AVSpeech / HDTF / VidChatBench 各 100 条）IQA 0.866 / 0.866 / 0.892，AR 系统中第一；FID 66.15（教师下限 67.10，Chained-DA 70.31）。
- 30s 外推（Table 2）：PAC IQA 末段相对开头 +2.6%，Sync-C 末段 5.69（−29.6%）；Chained-AD 7.82；Chained-DA 唇同步掉 43.7% 且逐渐失声。
- 正交性（Table 3）：两份更新的范数只占投影的 0.28% / 0.15%；读入子空间有重叠，但写出方向近似正交，二阶代价只剩 Hessian 交叉项。

**推理**：7 个 chunk 的滑窗 + 首帧 anchor，chunk 位置做 position-anchored 处理；clean-context teacher forcing 时 token 轴复制一份，clean / noisy 共用 RoPE，noisy chunk 只能看严格更早的 clean chunk。

**Case 实测补充**（ffmpeg volumedetect，3s 窗口）：hdtf-028 PAC 平均响度 0s −24.3dB → 20s −14.8dB，峰值 −0.3～−0.7dBFS；Chained-DA 0s −28.9dB → 16–24s 约 −40dB。项目页给的 ρ（末 10s / 首 10s RMS）：PAC 1.55，Chained-DA 0.46。
