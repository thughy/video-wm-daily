**评测设置**：JavisBench-mini 1000 个 prompt，121 帧，832×480，24fps，4 步。

| 480p | VQ ↑ | MQ ↑ | IB-AV ↑ | Javis ↑ | DeSync ↓ |
|---|---|---|---|---|---|
| Salt++ AR–AR | **2.838** | **1.010** | 0.184 | 0.146 | 0.759 |
| OmniForcing | 1.807 | 0.699 | — | — | — |
| TF-dCM | — | — | 0.229 | 0.200 | — |
| LTX-2（40 步） | 1.884 | 0.566 | **0.239** | — | **0.608** |

- 消融：BI-BI → AR-AR，VQ 0.837 → 3.147；teacher guidance 从固定 4.0 改为 U(1, 3.5)，VQ +91.5%。
- 在 LTX-2 PE 改写的 prompt 上，AR–AR 相对 OmniForcing 7 项全优（VQ +59%，MQ +64.6%）。
- 960p（scale-wise，每块 2 次低分辨率 + 2 次高分辨率调用）6/7 项超过 LTX-2 40+3 步，唯一例外是 DeSync；960p 的 OmniForcing 是直接外推、没按同分辨率训练，作者承认这一比较不公平。
- BI-AR 的 DeSync 最好（0.531），作者解释为输出近乎静止——说明 DeSync 在近静态视频上也会失真。

**方法细节**：CSF 阶段学生看混噪历史、EMA 教师看干净历史，目标块不变，对齐中间表征；AR–AR DMD 先在 clean prefix 上蒸馏，再 on-policy 适应自生成历史。训练在 GB300 集群上，数据为内部 AV 数据。

**Case 视频**：`main480-0` 的 LTX-2 / OmniForcing / Salt++ 三路对比和 `hr960-0` 960p，均为论文配图对应的 5s 片段（精选）。
