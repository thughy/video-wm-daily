**理论**：因果、时不变、使用当前 iid 噪声的生成器，其输出谱在任何频带都不可能为零（Kolmogorov–Szegő）；要把 δ 比例的频带压到 ε 以下，每步新息方差上限为 ε^δ——对应 talking head 常见的「抖动 vs 呆板」二选一。噪声是合成的，可以提前采未来噪声，所以噪声通路非因果整形不增加音频延迟。

**结构**：噪声栈 2 层双向注意力（半径 64）；条件栈 6 层因果注意力；冻结 Mimi 音频编码器；40ms lookahead；两个多尺度判别器（条件 / 无条件）+ mode-seeking 损失。输出 128 维表情 + 头姿运动码，渲染器来自 Agrawal et al. 2025（Meta 内部）。

**结果**

- 单路延迟 43ms；单张 H200 4096 路并发 62ms。
- 论文 Table 2（with pose / 64 次采样口径）Sync 0.8767 最佳（Fallingwater 0.696）。
- 噪声栈改因果：表情方差降到 0.92–0.93；同宽度表情多样性 −14%、姿态多样性 −22%（三次运行标准差带）。
- 用户研究 19 人、684 次比较：唇同步打平，自然度 57.1%。

**项目页公开指标 JSON**

| 方法 | LSE-C ↑ | LSE-D ↓ | SyncScore（不含 pose）↑ |
|---|---|---|---|
| FaceGAN | 3.80 | 8.14 | 0.749 |
| ARTalk | 4.73 | — | — |
| Fallingwater | 5.13 | — | 0.757 |
| MemoryTalker | 5.31 | — | 0.781 |
| DiffPoseTalk | — | — | 0.846 |

**对比网格**：19 个 clip，6 格顺序 GT / FaceGAN / Fallingwater / DiffPoseTalk / MemoryTalker / ARTalk（页面源码注释说明标签按 `MANIFEST.methods` 顺序、与拼接顺序一致；视频内嵌 GT 音轨）。测试集共 64 条，页面有「Auto-shuffle」，未说明 19 条怎么挑。
