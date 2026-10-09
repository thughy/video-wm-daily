> 方法与口径：arXiv 关键词全量召回 1567 篇 → 标题分诊 678 篇 → 667 篇 arXiv HTML 全文解析（机构、表格、代码、参考文献）→ 约 150 篇读摘要+方法+主实验 → 精选 47 篇（见 [signals.csv](survey-2026q3-signals.csv)）。引用信号来自**自建语料内共引图**（Semantic Scholar 被 429 限流）；社区信号来自 HF Daily（93 天）、X、Reddit、GitHub（45 个仓库）。
> 标注：⭐必读；⚠️证据弱或数字需打折；机构“未确认”表示 HTML 中未能确认。所有 FPS 必须看硬件和口径（是否含 VAE、单卡还是多卡）。

---

## 0. 一页总览：本季五大进展与判断

1. **AV 联合流式在 3 个月内从“能跑”走到“能说对话”。** OmniForcing（2603）和 Hallo-Live（2604）是首批实时联合 AV 模型。本季多篇独立论文都显示它们口型和语义很差：LSE-C 约 1.4–2.9，30s WER 超过 90%。之后 [Ripple](https://arxiv.org/abs/2607.26818)、[OmniMate](https://arxiv.org/abs/2607.23023)、[TaoMate](https://arxiv.org/abs/2607.24359)、[Vorch-Streamer](https://arxiv.org/abs/2608.05663)、[Omni-LiveAvatar](https://arxiv.org/abs/2608.13602) 用**记忆 + 说话规划 + RL** 把 LSE-C 拉到约 6、WER 降到约 8%，单卡 H100/H200 约 20–28 FPS。**判断：瓶颈已从“音画同步”转为“说什么、怎么持续说”（语言规划和长时状态）。** Vorch 的消融把这一点量化了：完整语句 WER 从 184% 降到 7.92%。
2. **配方收敛，问题转向 DMD 的副作用。** 流式视频的事实标准是：双向 teacher → block-causal 适配 → Self-Forcing/DMD 少步 → 记忆 → RL。本季的增量工作几乎都在修 DMD：多样性坍缩（[Mask Forcing](https://arxiv.org/abs/2609.09123)、Uncertainty DMD、DistillAlign）、teacher/context 失配（[CMD](https://arxiv.org/abs/2608.13391)、[RMD](https://arxiv.org/abs/2609.37925)）、历史梯度（[SGF](https://arxiv.org/abs/2607.20368)），以及不用双向 teacher 的路线（[Optica/CRP](https://arxiv.org/abs/2610.11479)）。**判断：最有价值的是 CMD/RMD 这类指出目标函数本身错位的工作；单纯加 loss 的增量多半落选。**
3. **世界模型开始“有声音”。** [EchoWM](https://arxiv.org/abs/2608.23189)（JD）、[HelixWorld](https://arxiv.org/abs/2609.38123)、[WorldSonus](https://arxiv.org/abs/2610.08760)、[JoyAI-Echo-1.5](https://arxiv.org/abs/2608.23383) 把环境声、音乐、语音放进可交互的世界模型；[Wan-Streamer v0.3](https://arxiv.org/abs/2607.15038) 提出“Video = World + Event Stream”，做全双工 AV 交互（模型侧约 200ms）。**判断：AV 流式和交互世界模型在合流。但目前两边的评测完全割裂：WM 用 WBench，AV 用 LSE-C。**
4. **评测是最薄弱的一环，本季出现了第一批“打假”工作。** [StreamAV-Bench](https://arxiv.org/abs/2608.26336) 测了 13 个系统，原生流式 AV（OmniForcing 的 AVAlign 0.119）的对齐反而不如级联管线（约 0.26–0.28）。[AV sync 指标审计](https://arxiv.org/abs/2608.25157) 显示各同步指标几乎互不一致（Krippendorff α=0.066）；[PVSync](https://arxiv.org/abs/2610.09223) 与人评的 Spearman 为 0.83，而 LSE-C 只有 0.34。**判断：本季所有以 LSE-C/Sync-C 为主证据的“SOTA”都需要打折。**
5. **底座格局：LTX-2 是 AV teacher，MiniMax-H3 是增长最快的新底座。** 在语料内，LTX-2 被 74 篇引用（AV 子集 44 篇）。[MiniMax-H3](https://arxiv.org/abs/2609.18323) 两个月内 18 篇引用、9.7k★，SolarWM、Video DeltaNet、PAC、TaoMate-H3 都基于它。[Kandinsky 6](https://arxiv.org/abs/2610.05608) 以 MIT 许可开源 29B AV 底座。**判断：下季 AV 流式工作会从 LTX-2 迁到 H3/Kandinsky 6，需盯 teacher 换代带来的可比性问题。**

---

## 1. 研究线

### 1.1 流式 / 自回归视频扩散（ST）
**核心问题**：把双向视频扩散变成能无限长、低延迟、可交互地生成的因果模型，同时不丢质量、动态和多样性。

**本季分化：**
| 子问题 | 代表作（机构，月份） | 要点 |
|---|---|---|
| teacher/context 失配 | ⭐[CMD](https://arxiv.org/abs/2608.13391)（NVIDIA，08）；[RMD](https://arxiv.org/abs/2609.37925)（CUHK MMLab+腾讯，09）；[OPSD-V](https://arxiv.org/abs/2607.08766)（美团/HKUST，07） | CMD 用因果 teacher + Prefix Scoring，指出“双向 teacher 给因果学生打分”本身是错位的；RMD 用 chunk 边际打分，60s VBench-Long Total 81.26（Self-Forcing 为 70.94） |
| DMD 模式坍缩（多样性、动态） | [Mask Forcing](https://arxiv.org/abs/2609.09123)（HKUST-GZ，09）；[Uncertainty DMD](https://arxiv.org/abs/2609.11265)（NJU/TeleAI，09）；[DistillAlign](https://arxiv.org/abs/2607.26811)（Riemann Dynamics，07）；[DuoMatching](https://arxiv.org/abs/2610.03543)（10） | reverse-KL 导致动态和多样性下降，是本季最集中的痛点 |
| 跨 chunk 梯度 | ⭐[Self Gradient Forcing](https://arxiv.org/abs/2607.20368)（JD，07） | 本季新文里被引最快（语料内 15 篇），已被 JD 自家 Echo-1.5/EchoWM 采用；后续 SGF+、Connected SF 增益很小，均落选 |
| 噪声历史与流水线 | [In-Context Forcing](https://arxiv.org/abs/2608.05237)；[Rethinking Streaming Video Diffusion](https://arxiv.org/abs/2609.22283)；[SAF](https://arxiv.org/abs/2609.38114)（Monash/Vivix，4×H100 49.1 FPS）；[FlashForward](https://arxiv.org/abs/2609.32540)（Meta+NTU）；[Stream Forcing](https://arxiv.org/abs/2608.10439)（HUST） | 更多是系统层面的优化 |
| 不用双向 teacher | [Optica/CRP](https://arxiv.org/abs/2610.11479)（CUHK-SZ+混元，10） | 从图像模型起步，只预测残差，受控实验把 6.14 分差距收窄到约 0.2；50 步，不实时 |
| 即插即用 | [LongLive-Plug](https://arxiv.org/abs/2609.38154)（NVIDIA，09） | 覆盖 54 个下游模型 |
| 记忆综述 | [The Past Frames the Future](https://arxiv.org/abs/2609.28466)（HKUST 等，09）；[Compress to Remember / PACC](https://arxiv.org/abs/2609.36364)（CMU/Rice，09） | 综述 + on-policy 压缩记忆 |

**理论与诊断（本季最值得读的“非刷榜”工作）：**
- ⭐[The Seriality Gap](https://arxiv.org/abs/2607.13031)（UC Berkeley，07）：增加去噪步不增加串行计算；AR/blockwise 生成和网络深度才增加串行计算。这为“为什么因果分块有效”提供了解释。
- ⭐[Can Video World Models Track Unobserved World States?](https://arxiv.org/abs/2608.30692)（SNU/Roblox，Xun Huang，08）：用 5 杯 Shell Game（S5 状态追踪）测试。只追加的 KV cache 和普通因果 DiT 都无法外推。能外推的只有两类：一是转移矩阵允许负特征值的线性 RNN（GDN-neg），二是 TTT 快权重。LaCT8 在 N=20 时准确率 0.98，在 N=30 时 0.69；加 1 层 MLP 后崩溃。**结论：记忆必须是“可修改的状态”，而不是只增不改的缓存。**
- [Tracking Is Not Permanence](https://arxiv.org/abs/2610.07355)（TUM，10）、[Training Object Permanence](https://arxiv.org/abs/2609.28654)（CMU 等，09，HF 241 赞）：物体恒常性的诊断，以及用合成数据补救。

**瓶颈**：①DMD 的多样性与动态问题仍未根治；②记忆普遍是只追加的形式，不能修正（见上文 Shell Game）；③评测几乎只用 VBench / VBench-Long。

### 1.2 交互式世界模型（WM）
**核心问题**：给定动作（键鼠、相机轨迹、文本事件），实时、长时、一致地生成可探索的世界。

| 类型 | 代表作 | 要点 / 扎实度 |
|---|---|---|
| 开源系统 | [LingBot-World 2.0](https://arxiv.org/abs/2607.07534)（蚂蚁，07，720p 60fps，语料内 30 引，本季最高）；[Matrix-Game 3.5](https://arxiv.org/abs/2608.29910)（Skywork 系，08，开权重）；[AlayaWorld](https://arxiv.org/abs/2607.18367)（盛大 Alaya，07，15B 开源）；[ABot-World-0](https://arxiv.org/abs/2607.19191)（高德，07，720P 16FPS@RTX 5090，延迟 1.2s）；[WorldPlay2](https://arxiv.org/abs/2609.35560)（腾讯混元，09） | 工程完整，多为技术报告 |
| 消费级硬件 | ⭐[Waypoint-1.5](https://arxiv.org/abs/2609.37107)（Overworld，09） | 1.28B 单流因果 DiT，配方为 Diffusion Forcing → Self-Forcing DMD，配 TAEHV 1.5，用 10 万小时 Owl-Control 手柄同步数据训练。**它明确区分 rendered FPS、latent FPS 和 control rate，并给出从 RTX 3070 到 PRO 6000 的完整吞吐表**（例：4090 上 720P INT8 为 72.9 latent FPS）。延迟口径值得全领域借鉴 |
| 记忆 | [WorldCrafter](https://arxiv.org/abs/2609.24984)（PKU+腾讯 ARC，09，隐式 3D 记忆，AK 201 赞，⚠️热度高于证据）；[Addressable Memory](https://arxiv.org/abs/2608.07408)（NVIDIA，08，training-free RoPE 可寻址）；[WorldAttention](https://arxiv.org/abs/2609.34606)（DAMO） | |
| 数据与复现 | ⭐[SolarWM](https://arxiv.org/abs/2609.02886)（CUHK-SZ，09） | 开放数据，并在 Wan2.2/LTX-2.5/MiniMax-H3 上训练了 4 个模型；GitHub 近 30 天 10 个新 issue，**是本季真实使用度最高的 WM 仓库之一** |
| 显式状态 | [Programmable World Model](https://arxiv.org/abs/2609.10540)（Alaya，09）；[From Pixels to States](https://arxiv.org/abs/2607.14076)（07） | 显式状态 + 视频渲染器，与 Shell Game 的结论呼应 |
| 有声世界模型 | 见第 2 章 | |

**瓶颈**：动作空间大多只有导航和相机，几乎没有“交互改变世界状态”；评测（WBench）偏视觉；各家延迟口径不一（Waypoint 例外）。

### 1.3 视频编辑（ED）
| 子线 | 代表作 | 要点 |
|---|---|---|
| 实时 / 流式编辑 | ⭐[JoyAI-Video-Edit](https://arxiv.org/abs/2608.03974)（JD，08）；[InfinityEdit](https://arxiv.org/abs/2608.20910)（机构未确认，作者含阿里系，08）；[SVEET](https://arxiv.org/abs/2609.24788)（SJTU，09，15 FPS@H100）；[EditStream](https://arxiv.org/abs/2608.21424)（据作者推断为 Adobe，08）；Vidu S2 的流式编辑 | JoyAI-Video-Edit 为 16B AR 扩散，提出 SA-DMD，720p 约 30 FPS@单 B200，代码开源（1.9k★） |
| 图像编辑 → 视频编辑迁移 | [VINCIE-NExT](https://arxiv.org/abs/2610.12104)（NUS+字节 Seed，10）；[AVE](https://arxiv.org/abs/2610.11037)（10）；[Qwen-Video-Edit](https://arxiv.org/abs/2608.14790)（08）；[FlowMimic](https://arxiv.org/abs/2607.18227)（字节，07） | 多篇独立工作得出同一结论：**视频编辑质量与图像编辑器强相关，逐帧视频 latent 离图像域足够近** |
| 数据与评测 | [VideoX-Qwen](https://arxiv.org/abs/2609.26015)（120 万条）；[RefVideo-6M](https://arxiv.org/abs/2608.26101)（TeleAI，真实视频作为目标）；[CoinVE-200K](https://arxiv.org/abs/2608.17566)（腾讯）；[OmniEdit-Bench](https://arxiv.org/abs/2608.05049)（HKU+Wan，带 accuracy-aware penalty） | |
| AV 编辑 | [CrossEdit](https://arxiv.org/abs/2610.10264)（Adobe/CMU）、AVE-Compass 等 | 起步阶段，未深读 |

### 1.4 底座与效率（FD）
- [SANA-Video 2.0](https://arxiv.org/abs/2607.21553)（NVIDIA，07）：gated linear 与 softmax 按 3:1 混合，5B/14B，单 GPU 可出 720p，为长流式打基础。
- [Chimera](https://arxiv.org/abs/2607.28611)（据作者推断为 Adobe，07）：KDA + MLA + MoE 的混合扩散骨干，附 Chinchilla 式 scaling。
- [Video DeltaNet](https://arxiv.org/abs/2609.20744)（OpenVDN，09）：基于 MiniMax-H3 的线性化，8×B200 上 14.5× 加速，代码已开源。
- 表征 latent：[V-RAE](https://arxiv.org/abs/2608.13556)、[VideoRAE](https://arxiv.org/abs/2607.14088)、[GRACE](https://arxiv.org/abs/2610.10524)。
- [Rethinking CFG in On-Policy Distillation](https://arxiv.org/abs/2607.24731)（Qwen，07）：在 CFG 下做 OPD 时，分支级误差会互相抵消，对 AV 蒸馏同样适用。

---

## 2. 专章：音视频联合流式生成（P0）

### 2.1 路线图
```
                ┌─ 原生联合 (joint AV DiT → 因果化) ──────────────┐
 联合AV底座      │  LTX-2/2.3 (14B+5B 双流) ← 绝大多数                  │
 (双向,多步)  ───┤  MiniMax-H3 (PAC, TaoMate-H3)                      │
                │  Ovi/MOVA/Kandinsky6 (尚无流式化工作)               │
                └───────────────────────────────────────────────┘
   因果化顺序：A) 先 block-causal 适配(TF/DF/ODE init) → 再 Self-Forcing+DMD 少步  ← Ripple / Vorch / Omni-LiveAvatar / TaoMate
               B) 直接 Self-Forcing DMD（原 LTX-2 当 teacher，跳过双向 DMD）       ← OmniForcing 新版
               C) 冻结底座 + 并行 adapter 相加（因果 adapter ⊕ few-step LoRA）     ← PAC (on H3)
               D) 先双向少步 → 不做因果（只“快”不“流”）                         ← TurboT2VA
   之后：记忆（anchor / 压缩 AV 状态 / recurrent memory）→ 说话规划（LLM plan token / GPC）→ online RL
 级联 / 半级联：流式视频 + 流式 V2A（WorldSonus、StreamAV-Bench 中的 Odyssey-2/LongLive+V2A）
 全双工交互：Thinker (理解+语言动作) → Performer (AV latent 流匹配)  ← Wan-Streamer v0.1–0.3
```

### 2.2 关键工作精读摘要
| 工作 | 机构 | 底座 | 路线 | 速度（口径） | 质量证据 | 扎实度 |
|---|---|---|---|---|---|---|
| ⭐[Ripple](https://arxiv.org/abs/2607.26818) | China Telecom AI（Yali Wang） | LTX-2.3 | 记忆增强 block-causal → memory-forcing 蒸馏 → online RL | 约 28 FPS 480P @1×H100，比 teacher 快 15× | VerseBench 延迟 5.9s（teacher 74s）；LSE-C 6.08（teacher 6.37 / OmniForcing 1.42 / Hallo-Live 4.28）；30s ID 一致性 0.944 | 高；无代码 |
| [OmniMate](https://arxiv.org/abs/2607.23023) | 同上 | LTX-2.3 | Generation Progress Controller + 多参考 | 27.64 FPS，TTFF 3.49s @H100 | LSE-C 4.06（OmniForcing 2.85）；240s 稳定 | 中高；自述有漏词/重复 |
| [TaoMate](https://arxiv.org/abs/2607.24359) | 淘宝直播 AIGC | LTX-2.x，22.1B | 不变 anchor + 压缩 AV 状态 | DiT 16.32 FPS @RTX PRO 5000（**不含 VAE**）；3 卡 stage-parallel 35 FPS | LipSync 5.918（OmniForcing 1.590） | 中高；有仓库 499★ |
| ⭐[Vorch-Streamer](https://arxiv.org/abs/2608.05663) | Vorch/同济/哈工深/上交 | LTX-2.x | 8 万条合成 avatar；TF/DF 混合 → 长时 Self-Forcing+DMD；LLM speech-plan token（25Hz） | 27.12 FPS @H200（DiT 吞吐） | Sync-C 6.62，WER 7.92%（30s 时 OmniForcing 98.79%、Hallo-Live 94.13%）；speech-plan 消融 184% → 7.92% | 高 |
| [Omni-LiveAvatar](https://arxiv.org/abs/2608.13602) | 机构未确认（作者含 Guanglu Song、Yu Liu、Jun Zhang） | LTX-2 | 分钟级 | 19.57 FPS @H200，比 LTX-2 快 33× | Sync-C 6.16（5s）；分钟级 6.76（OmniForcing 0.28） | 中；仓库 8★ 基本为空 |
| [PAC](https://arxiv.org/abs/2610.10343) | LIGHTSPEED + 独立研究者 | MiniMax-H3（冻结） | 因果 adapter ⊕ few-step LoRA | 6 GPU 约 26 FPS，TTFF 4.2s（GPU 型号未写） | WER 约为 teacher 的 3 倍；长时音色下降 41% | 中 |
| [Salt++](https://arxiv.org/abs/2609.36995) | HKUST/Vivix/USyd/Westlake | LTX-2 | Causal Self-Flow + AR-AR DMD，4 步 | 未报 | VQ/MQ 上升，但 IB-AV/Javis/DeSync 变差 | 中 ⚠️ |
| [JoyAI-Echo-1.5](https://arxiv.org/abs/2608.23383) | JD | 自家 AV | 长视频 AV 记忆 + SGF 因果 4 步 | — | WBench Navigation 81.7（因果版 81.0） | 中高；开源 |
| ⭐[EchoWM](https://arxiv.org/abs/2608.23189) | JD | 同上 | 双向多步 AV → 流式 AR 后训练；第一/第三人称统一的 6-DoF 轨迹控制 | — | 4 源数据引擎；**首个同时有环境声、音乐、语音的可进入世界模型**；自述无显式 3D 记忆，动作仅限导航 | 中 |
| [HelixWorld](https://arxiv.org/abs/2609.38123) / [WorldSonus](https://arxiv.org/abs/2610.08760) | HKUST+NoizAI | — | 联合 / 模块化流式 V2A | RTF 0.77 @H800 / 0.41 @H100 | 立体声、Ring-KV；视觉 WBench 低于基线 | 中 |
| [Wan-Streamer v0.3](https://arxiv.org/abs/2607.15038) | Wan-AI | 自研 Thinker + Ulysses 并行 Performer | 全双工；语言形式的“说话 + 行为”事件流条件化 AV 生成 | 640×368@25FPS；160ms 单元；模型侧约 200ms，总延迟约 550ms（含 350ms 网络预算） | **只有延迟和定性观察，没有定量质量评测**（正文约 3.6k 词） | ⚠️方向最重要但证据弱 |
| [UniSwap](https://arxiv.org/abs/2608.11752) | CUHK+Qwen Apps | — | 流式 AV 身份替换 | 13.6 FPS @H100（**低于 25 FPS 播放速率**） | | 中 |
| [TurboT2VA](https://arxiv.org/abs/2608.24674) | ZJU/清华 thu-ml | LTX-2 | 4 步双向（非流式） | 20.1× 加速，2.51s | | 中 |
| [Vidu S1](https://arxiv.org/abs/2607.03118)/[S2](https://arxiv.org/abs/2609.11638) | 清华+生数 | 自研 | 产品级实时交互 | S1：540p 最高 42 FPS（消费级 GPU）；S2：720p 25–42 FPS | 消融很少 | ⚠️产品报告 |

周边工作：
- tokenizer：[OmniVAE](https://arxiv.org/abs/2607.23855)（OpenMOSS，联合 AV VAE）、[KVAE](https://arxiv.org/abs/2608.05798)（48kHz 音频，已开源）。
- avatar 加速：[LeapTalk](https://arxiv.org/abs/2608.00079)（1 步 bridge，200 FPS）、[AptAvatar](https://arxiv.org/abs/2607.24013)（2 NFE）、[FaceGAN](https://arxiv.org/abs/2610.11070)（Meta，因果生成器的频谱约束理论，43ms）。
- 线上服务：[DHSched](https://arxiv.org/abs/2609.26363)（约 5 万会话的 avatar 调度）。

### 2.3 tokenizer / latent 设计
- 主流：沿用 LTX-2 的视频 VAE（时间步长 8）+ 音频 VAE。OmniForcing 用 1 秒宏块对齐 3 个视频 latent 帧和 25 个音频 latent 帧，再用 Audio Sink Token + Identity RoPE 解决音频 token 稀疏导致的梯度爆炸。后续工作基本继承这套对齐方式。
- 新尝试：联合 AV VAE（OmniVAE）、高采样率音频 tokenizer（KVAE 48kHz）、Wan-Streamer 的 160ms 统一流单元。**尚无论文系统比较不同 AV latent 帧率对首帧延迟和同步的影响**，这是一个空白。

### 2.4 延迟如何测：现状混乱
| 口径 | 谁在用 | 问题 |
|---|---|---|
| DiT FPS（不含 VAE 解码） | TaoMate、Vorch | 高估端到端速度 |
| 多卡 stage-parallel FPS | TaoMate（3 卡）、PAC（6 卡）、SAF（4×H100） | 不可与单卡比较 |
| TTFF / TTFC | OmniMate 3.49s、PAC 4.2s、OmniForcing 约 0.7s（项目页） | 定义不一（是否含文本编码、prompt 预填充） |
| 信号到信号延迟（输入单元可用 → 响应单元解码完成） | Wan-Streamer | 最接近交互体验，但网络预算是假设值 |
| RTF | HelixWorld、WorldSonus | 音频领域口径 |
| rendered FPS / latent FPS / control rate | Waypoint-1.5（WM） | **最规范，建议采用** |

**建议统一报告**：硬件；分辨率；单卡还是多卡；是否含 VAE；TTFF（含与不含文本编码）；稳态 FPS 与播放帧率之比；交互任务另报信号到信号延迟。

### 2.5 关键团队
JD Joy Future Academy（OmniForcing → SGF → Echo-1.5 → EchoWM → Video-Edit，全链路且开源）、China Telecom AI（Ripple/OmniMate）、阿里系（淘宝直播 TaoMate、Wan-AI Wan-Streamer、Qwen Apps UniSwap/LiveAnimate、夸克 Live Avatar）、HKUST+NoizAI（HelixWorld/WorldSonus/Salt++）、清华+生数（Vidu、TurboDiffusion）、BAAI/PKU（StreamAV-Bench）。

### 2.6 评测问题
1. **同步指标不可靠**：审计论文显示各指标间 α=0.066，DeSync 跟踪偏移最好（τ=0.84）；PVSync 与人评的相关性远高于 LSE-C。→ 只报 LSE-C 的论文应视为弱证据。
2. **原生和级联没有公平对比**：StreamAV-Bench 显示原生流式在 AV 对齐上落后于级联，但它测的原生系统（OmniForcing、PixVerse R1、HappyOyster）都早于本季的 Ripple/Vorch，**本季新方法尚未进入该 benchmark**。
3. **长时语义只有少数论文评测**：Vorch 和 OmniMate 测了 30s 以上的 WER，其余多为 5s。
4. **商业系统不透明**：PixVerse R1/R2、HappyOyster、Odyssey-2、Krea Realtime 只出现在别人的对比表或 X 上（例：[Visko Orbis 1.0](https://arxiv.org/abs/2607.26694) 横向比较了这几家），无技术报告。
5. **teacher 天花板**：几乎都蒸馏自 LTX-2.x，学生在多数指标上难以超过 teacher。少数“学生超 teacher”的结论（HelixWorld 音频指标、Ripple 30s ID 一致性）没有充分解释。

---

## 3. 必读清单（12 篇）
1. [Ripple](https://arxiv.org/abs/2607.26818)：China Telecom AI。最完整的 AV 流式三阶段配方，对比也最全。
2. [Vorch-Streamer](https://arxiv.org/abs/2608.05663)：Vorch/同济/哈工深/上交。用消融证明“说什么”是因果 T2AV 的核心瓶颈。
3. [StreamAV-Bench](https://arxiv.org/abs/2608.26336)：BAAI/PKU。流式 AV 的第一个系统评测，覆盖原生与级联。
4. [What Do AV Sync Metrics Actually Measure?](https://arxiv.org/abs/2608.25157)：机构未确认。读任何 AV 同步数字之前先读它。
5. [EchoWM](https://arxiv.org/abs/2608.23189)：JD。AV 和交互世界模型的合流点，开源。
6. [Wan-Streamer v0.3](https://arxiv.org/abs/2607.15038)（配合 [v0.1](https://arxiv.org/abs/2606.25041)、[v0.2](https://arxiv.org/abs/2607.04443) 一起读）：Wan-AI。全双工 AV 交互的系统设计；论文证据薄，按“方向”来读。
7. [CMD](https://arxiv.org/abs/2608.13391)：NVIDIA。指出双向 teacher 给因果学生打分的错位，并给出因果 teacher 方案。
8. [Self Gradient Forcing](https://arxiv.org/abs/2607.20368)：JD。本季被引最快的新方法，已进入工业系统。
9. [Can Video World Models Track Unobserved World States?](https://arxiv.org/abs/2608.30692)：SNU/Roblox（Xun Huang）。记忆机制的受控理论检验。
10. [The Seriality Gap](https://arxiv.org/abs/2607.13031)：UC Berkeley。解释 AR/blockwise 生成为什么有效。
11. [SolarWM](https://arxiv.org/abs/2609.02886)：CUHK-SZ。开放数据 + 多底座复现，社区真实使用度高。
12. [JoyAI-Video-Edit](https://arxiv.org/abs/2608.03974)：JD。实时流式编辑的工业级实现，开源。

次一级（选读）：OmniMate、TaoMate、RMD、Waypoint-1.5、PAC、MiniMax-H3、LingBot-World 2.0、Kandinsky 6、VINCIE-NExT、Optica/CRP。

---

## 4. 开放问题
1. **可修改的长时 AV 状态**：Shell Game 的结论能否迁移到 AV？说话人音色漂移（PAC 下降 41%）和场景状态都需要能修改的记忆，而非只追加的 KV。
2. **语言规划与 AV 生成的接口**：Vorch 用 plan token，Wan-Streamer 用语言形式的事件流，OmniMate 用 GPC。哪一种可扩展？与 omni LLM（Qwen-Omni 类）如何端到端联合？
3. **原生 vs 级联的公平对比**：需要用本季的新方法重跑 StreamAV-Bench，并同时报告 DeSync、人评和 WER。
4. **AV latent 帧率与首帧延迟的权衡**：目前没有系统研究。
5. **摆脱 teacher 天花板**：teacher-free（Optica/CRP）或 RL（Ripple online RL、AV-GRPO、Adaptive Reward Routing）能否让学生超过 LTX-2？
6. **统一延迟口径**：见 2.4 的建议。
7. **交互世界模型的音频评测**：需要空间声学和事件因果性指标（HelixWorld 的自定义指标尚未经验证）。

---

## 附：覆盖缺口（如实说明）
- Semantic Scholar（429）和 OpenReview（403）不可用，没有全网引用数和 ICLR 2027 投稿信息。共引只基于 667 篇全文。
- 知乎和公众号几乎没有召回。商业系统（PixVerse、HappyOyster、Odyssey、Krea）没有一手技术资料。
- HF 2026-09-29 的第 2 页（9 篇）未抓取。arXiv 关键词检索可能漏掉标题和摘要都不含关键词的工作。
- 编辑和底座线只读到摘要与部分实验，深度低于 AV 和 ST 两条线。
- GitHub star 增速：stargazer 时间戳接口对多数仓库返回 404，用“总星数 / 建库天数”估算，可能低估近期的爆发。
