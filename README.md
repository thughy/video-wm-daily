# video-wm-daily

World Model · 视频生成 · 视频编辑 · 流式视频生成（重点：音视频流式生成）每日论文精读。

- 汇总页：https://thughy.github.io/video-wm-daily/
- 每日页：`https://thughy.github.io/video-wm-daily/daily/YYYY-MM-DD/`（卡片锚点 `#p-<论文id>`）
- 最新一期：https://thughy.github.io/video-wm-daily/latest/
- 周度脉络：`https://thughy.github.io/video-wm-daily/weekly/YYYY-Www/`

纯静态站点，无外部 CDN、无服务器、无费用：`build.py` 把 `data/` 里的 JSON 渲染成 HTML，GitHub Actions（`.github/workflows/pages.yml`）在每次 push 到 main 后构建 `docs/` 并部署到 GitHub Pages。`docs/` 不入库。

## 每日发布流程

1. **写数据**：新建 `data/YYYY-MM-DD.json`，字段见 [SCHEMA.md](SCHEMA.md)。周五可再写 `data/weekly/YYYY-Www.json`。
2. **处理图片/短视频**（可选）：
   ```bash
   python optimize_assets.py YYYY-MM-DD 原始文件或目录 --prefix 论文id
   ```
   输出到 `assets/YYYY-MM-DD/`（图片 webp ≤1200px；视频截 8 秒、≤2MB、保留音轨），按打印出的路径写进 `media[].src`。大视频不入库，只放链接。
3. **本地检查**（可选）：`python build.py --check` 只校验；`python build.py` 生成到 `docs/` 可本地打开。
4. **发布**：
   ```bash
   ./publish.sh
   ```
   会做：资源体积审计 → 校验并构建 → `git commit` → `git push` → 等待 Actions 部署 → curl 检查当天页面返回 200。

依赖：`pip install markdown pillow`，以及 ffmpeg（只有压视频时需要）。

## 页面结构

- 汇总页：本周最重要（最近 7 天的必读，`highlight: true` 优先，音视频流式优先）→ 每日列表（头条 + 必读/值得看数量 + 论文标题，可按方向和评级筛选）→ 周度脉络入口。「了解即可」不进汇总页。
- 每日页：速览（头条；音视频流式专区置顶；每篇一行：评级 + 标题 + 一句话结论）→ 逐篇卡片（固定顺序：TL;DR、核心 insight、图、脉络、方法、证据、case、代码、疑点，完整细节默认折叠）→ 「了解即可」页底折叠 → 趋势总结 → 前一天/后一天导航。
