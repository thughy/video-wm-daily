> 返回：[DLSS 5 深读专题](../dlss5/index.html)。标注：**[官方 url]** 表示出自 NVIDIA 官方页面，**[社区 url]** 表示出自非官方来源，**[推断]** 表示我们的判断。核查日期：2026-10-16。

## 一、先说结论

- **目前没有官方、合法的办法，让开发者在自己的内容上调用 DLSS 5 NR。** 官方已上线的只有 NBA 2K27 和 GeForce NOW 两处 [[官方博客](https://developer.nvidia.com/blog/whats-new-for-game-developers-dlss-5-with-3d-guided-neural-rendering-nvidia-ace-updates-and-new-rtx-kit-capabilities/)]。NVIDIA 的 DLSS 开发者页面只提供 **DLSS 4.5** 的 UE 插件（SL 2.14.1 / NGX 310.9.1）和 Streamline 的 SR、RR、MFG 插件，**没有 NR 插件** [[官方 DLSS 页](https://developer.nvidia.com/rtx/dlss)]。开发者论坛上有人在问 UE 5.8 的 DLSS 5 插件，以及能否用 MRQ 离线渲染，官方都没有答复 [[NVIDIA 论坛](https://forums.developer.nvidia.com/t/official-dlss-5-neural-rendering-plugin-access-for-unreal-engine-5-8-2/382731)]。
- 现在能找到的「视频跑 DLSS 5」工具，包括 ComfyUI-RH-DLSS5、DLSS5VKLayer、DLSS5ForUE5 和 OpenDLSS-NR，**全部要用从驱动或泄露包里取出的 `nvngx_dlssnr.dll`（310.8.0）** [[社区 ComfyUI-RH-DLSS5](https://comfy.icu/extension/RH-RunningHub__ComfyUI-RH-DLSS5)] [[社区 DLSS5VKLayer](https://github.com/bmitch87/DLSS5VKLayer)]。这违反我们「不提取 DLL、不用 NVIDIA 权重」的规则，也有法律风险，**不推荐**。
- **它不是超分**：输入输出同分辨率，是显示前的一道照片化处理 [原文报告 §1.2、§4.2]。所以「高清化」只能理解为「更像照片」；要提分辨率，得另外接 DLSS SR 或视频超分 [推断]。
- **推荐的路线**：先跑路线 C（开源视频增强模型做对照 demo，马上能做），同时准备路线 A（UE5 重渲染，先用 DLSS 4.5 RR 加路径追踪当基线），并以公司名义向 NVIDIA 申请 DLSS 5 开发者权限。拿到官方插件后再补跑 DLSS 5 那一组。路线 B 只作为研究备注，不执行。

## 二、(a) DLSS 5 能不能直接吃 mp4？

**不能直接吃。** 它是渲染管线里的一级，每帧需要 [原文报告 §2.1、§2.5] [[官方博客](https://developer.nvidia.com/blog/whats-new-for-game-developers-dlss-5-with-3d-guided-neural-rendering-nvidia-ace-updates-and-new-rtx-kit-capabilities/)]：

| 每帧输入 | 要求 | 从 mp4 能拿到吗 |
|---|---|---|
| 渲染颜色 | 引擎当前帧，同分辨率；推理时转成 LDR 代理图（按纸白归一，0.75 以上软压缩，sRGB 编码）[OpenDLSS-NR 文档 frame.md，作者自报] | 能拿到，但 mp4 已经过色调映射、压缩和色度下采样，和引擎原始帧不是一个分布 [推断] |
| 引擎运动矢量 | 逐像素、包含物体运动，还要标出是否有历史 | 只能用光流去估，遮挡区和透明物体都会出错 [推断] |
| 时序状态 | 上一帧输出经重投影后喂回网络，由网络给出融合门 | 运行时自己维护 |
| 艺术控制 | 外观模型、Structure/Tone 强度、mask | 运行时参数 |

报告还写明：输入分布偏离训练分布时（不同的着色方式、伪影模式）效果会下降，而且它保留输入里的缺陷，不会去修 [原文报告 §5.4]。所以压缩过的 mp4 是最差的一种输入 [推断]。

## 三、(b) 路线 A：在引擎里从 CG 源场景重渲染（主线）

前提：**有 CG 的源工程**，比如 UE 工程、或 FBX/USD 加材质和相机动画。

1. **场景**：导入 UE 5.7/5.8，确认相机动画、材质和光照都完整。
2. **基线**：装官方 DLSS 4.5 UE 插件 [[官方 DLSS 页](https://developer.nvidia.com/rtx/dlss)]，录三组：光栅化、Lumen 加 DLSS RR、路径追踪（高 spp 当参考）。
3. **离线输出**：用 Movie Render Queue 按固定帧率（24 或 30 fps）输出 EXR 和 PNG 序列，**同时输出运动矢量、深度、albedo 和法线这几个 pass**，留给评测和将来使用。MRQ 和 DLSS 插件能不能一起用，我们没在官方文档里找到确认，需要实测 [推断]。
4. **DLSS 5 那一组**：等官方 UE 插件或 SDK 出来、或拿到 NVIDIA 授权后，在同一工程里打开 NR，按 Structure/Tone 做网格（见第七节），用 MRQ 或实时录屏输出。**现在做不了** [[NVIDIA 论坛](https://forums.developer.nvidia.com/t/official-dlss-5-neural-rendering-plugin-access-for-unreal-engine-5-8-2/382731)]。
5. **备选引擎**：Omniverse 或 RTX Remix。我们没有找到它们支持 DLSS 5 NR 的官方说明，暂不考虑 [推断]。

## 四、(c) 路线 B：从现成视频出发（只作为研究备注，不执行）

- 设想的流程是：mp4 → 解码成帧 → RAFT 或 SEA-RAFT 估光流当运动矢量，再用前后向一致性检查生成「是否有历史」的 mask → 交给 NR 运行时 → 编码输出。
- **官方 NGX 运行时**：现在没有公开的 NR SDK 或头文件可以合法调用。官方 DLSS SDK 只有 SR、RR 和 FG [[官方 DLSS 页](https://developer.nvidia.com/rtx/dlss)]。
- **OpenDLSS-NR 或 ComfyUI 桥接**：要从驱动里取 `nvngx_dlssnr.dll` 或权重，有法律风险（OpenDLSS-NR 的 issue #7）。NVIDIA 论坛上也有人直说这些社区插件用的是泄露的 310.8.0 DLL [[NVIDIA 论坛](https://forums.developer.nvidia.com/t/official-dlss-5-neural-rendering-plugin-access-for-unreal-engine-5-8-2/382731)]。**不建议做**；要做必须先经过法务确认。
- 即使跑通了，光流运动矢量和 mp4 的输入分布偏差，也会让结果不能代表 DLSS 5 的真实水平 [推断]。

## 五、(d) 路线 C：不用 DLSS 的对照方案（现在就能做）

- 用开源的视频到视频增强或重打光模型来做，比如以 Wan2.x 或 HunyuanVideo 为底座的 video-to-video、带深度或边缘控制，或者逐帧图像编辑后再做时序融合。这样做出的就是「通用生成模型 vs 渲染器锚定」的对照，正好对应报告 Fig.9 的论点 [推断]。
- 要事先说清楚：这类方法通常要多步采样、做不到实时；内容和身份可能漂移；chunk 边界可能闪烁 [推断]。这些恰恰是我们要量化的指标。
- 跑之前要先查清所选模型的许可，也不能调用要收费的 API。

## 六、(e) 阿里云 5090 的实际问题

| 问题 | 结论 |
|---|---|
| 系统 | 跑 UE 编辑器和官方 DLSS 插件、以及将来的 DLSS 5，**最好用 Windows 实例**。NR 的运行时是 Windows 的 DLL，社区在 Linux 上只能靠 Wine 或 Proton 桥接，而且仍要那个 DLL [[社区 DLSS5VKLayer](https://github.com/bmitch87/DLSS5VKLayer)]。路线 C 用 Linux 就行 [推断] |
| 驱动 | 5090 是 Blackwell（sm_120），需要较新的 GRD 或 Studio 驱动。社区工具的说明写的是 580+ [[社区](https://comfy.icu/extension/RH-RunningHub__ComfyUI-RH-DLSS5)]。阿里云实例的具体镜像和驱动要由 Henry 确认 [推断] |
| 显示 | UE 编辑器和 MRQ 需要一个图形会话：Windows 上用 RDP 或 Parsec 加虚拟显示器；没有显示器时可能需要虚拟显示驱动或 HDMI 欺骗器（云上一般是虚拟显示）[推断] |
| 无头渲染 | MRQ 可以从命令行启动 UE 做离线渲染，但仍需要 GPU 和 D3D12 设备；路线 C 的 Linux 推理完全可以无头 [推断] |
| 是否算「消费级 GPU」 | 阿里云上的 5090 是否是带完整图形驱动的 GeForce 形态，需要确认。DLSS 5 官方只说支持 RTX 50 系列 [[官方博客](https://developer.nvidia.com/blog/whats-new-for-game-developers-dlss-5-with-3d-guided-neural-rendering-nvidia-ace-updates-and-new-rtx-kit-capabilities/)] |

## 七、(f) Demo 设计

**素材**：一段 10–20 秒、1080p、24 或 30 fps 的 CG 片段。要求有人物特写（皮肤、头发）、植被、明暗对比强的室内外光照，以及缓慢的相机运动加一次快速转身（用来测遮挡和历史拒绝）。最好用 UE 示例工程或 CC0 资产，比如 Bistro 加 MetaHuman，避免版权问题 [推断]。

**对照组**（同一相机路径、同一帧率、逐帧对齐）：

| 组 | 内容 |
|---|---|
| A0 | 光栅化原始输出 |
| A1 | 路径追踪参考（高 spp） |
| A2 | 加 DLSS 4.5 RR（官方插件） |
| A3 | 加 DLSS 5 NR：Structure ∈ {0, 0.5, 1} × Tone ∈ {0, 1}，模型 A/B/C 各一组（**等拿到官方授权后**） |
| C1 | 开源视频到视频增强（路线 C） |

**指标**：
- 时序闪烁：用源序列的运动矢量把第 t−1 帧输出 warp 到第 t 帧，算可见区域的误差（warped error），同时报光流幅度 [推断]。
- 内容保持：输出和输入之间的 LPIPS、DINOv2 patch 距离（和报告 Table 1 同口径）。
- 身份：人脸用 ArcFace 余弦相似度。
- 结构：用同一个估计器分别估输入和输出的法线和深度，算误差。
- 主观：盲测两两比较真实感（和 Table 2 同口径），另外单独打分闪烁和改脸。

**交付物**：并排对比视频、指标表、structure × tone 网格图，放在一个站点页面上。

**时间线**（不含等 NVIDIA 授权的时间）：
- 第 1 天：起实例、装驱动、装 UE，跑通 A0/A1/A2；
- 第 2 天：跑路线 C；
- 第 3 天：算指标、写页面；
- 拿到 DLSS 5 授权后，再用 1 天补跑 A3。

**风险**：
- 官方 DLSS 5 开发包何时发布不确定，这是最大的风险；
- MRQ 和 DLSS 插件可能不兼容；
- 云实例的驱动或显示配置可能不支持 UE 图形会话；
- 路线 C 的模型许可；
- 如果有人提议用泄露的 DLL「先跑起来」，必须拒绝。

## 八、Henry 需要提供或决定的事

1. CG 片段的**源工程**（UE、FBX 或 USD），而不只是 mp4；如果只有 mp4，就只能走路线 C。
2. 阿里云 5090 实例的系统（建议 Windows）、驱动版本和远程桌面方式。登录由 Henry 自己完成，我们不接触凭据。
3. 是否以公司名义向 NVIDIA 申请 DLSS 5 NR 的开发者权限（可以通过 Developer Relations 或在论坛发帖）。
4. 确认路线 B（社区 DLL 方案）不执行。
