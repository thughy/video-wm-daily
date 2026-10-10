# 数据格式

所有内容都是 UTF-8 JSON。长文本字段都写 Markdown（支持表格、列表、代码）。
任何长文本字段也可以写成 `{"file": "2026-10-09/pac-details.md"}`，路径相对 `data/`，适合很长的「完整细节」。

## 每日文件 `data/YYYY-MM-DD.json`

| 字段 | 必填 | 说明 |
|---|---|---|
| `date` | ✔ | 与文件名相同，如 `2026-10-09` |
| `headline` | ✔ | 一句话头条：今天最重要的进展 |
| `papers` | ✔ | 论文数组，可为空 `[]`（当天没有达标论文） |
| `trend_summary` |  | 当天趋势总结（Markdown） |
| `resources` |  | 「可用资源」区：开源工程/工具，`[{"title", "url", "license", "note"}]`，不参与原创性评级 |
| `redo` |  | 「重做」区：每篇一行，`[{"title", "url", "note"}]`，放在页底 |
| `draft` |  | `true` 时不发布 |
| `example` |  | 仅示例数据使用；正式 `data/` 中出现会被 build.py 拒绝 |

### `papers[]` 每篇论文

页面中卡片按下表顺序固定展示（空字段自动省略）。手机端（≤600px）超过 160 字的字段默认折叠（`static/fold.js`），`comparison` / `context` 除外；宽表横滑，首列固定。

| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | ✔ | 当天唯一的短 slug（小写字母/数字/连字符），用作锚点 `#p-<id>` |
| `rating` | ✔ | `must`（必读）/ `worth`（值得看）/ `fyi`（了解即可，页底折叠，不进汇总页） |
| `originality` |  | 原创性：`mechanism`（新机制）/ `finding`（新发现）/ `redo`（重做，一般不单独成卡，放 `redo` 区） |
| `credibility` |  | 可信度：`solid`（站得住）/ `doubtful`（存疑）/ `insufficient`（证据不足）。`must` 要求原创（非 redo）且 `solid`，build.py 会校验 |
| `directions` | ✔ | 数组，取值：`av-streaming`（音视频流式，速览置顶专区）、`streaming`、`world-model`、`video-gen`、`video-edit`、`other` |
| `title` | ✔ | 论文标题（原文） |
| `tldr` | ✔ | 一句话结论（速览和汇总页显示的就是它） |
| `institutions` |  | 机构数组 |
| `published` |  | 发表信息，如 `arXiv 2026-10-08 (v2)` |
| `links` |  | `{"paper": url, "project": url, "code": url, "other": [{"label": "...", "url": "..."}]}` |
| `rating_reason` |  | 一句话评级理由 |
| `coverage` |  | 核查深度：`{"paper": v, "demo": v, "code": v, "note": "..."}`，v ∈ `full` / `partial` / `none` / `unavailable` |
| `highlight` |  | `true` 时优先进入汇总页「本周最重要」 |
| `comparison` |  | **新版首字段**：最接近的 2–3 篇工作对比表 + 一句机制级增量 + 反事实结论（能否预测）。手机端不折叠 |
| `context` |  | 旧版「与已有工作的区别 / 脉络」（10-09 使用），手机端不折叠 |
| `insight` |  | 旧版核心 insight |
| `method` |  | 机制 / 方法要点 |
| `media` |  | `[{"src": "assets/YYYY-MM-DD/xxx.webp", "caption": "...", "wide": true}]`；有 `comparison` 时显示在 method 之后，否则在 insight 之后。`wide: true` 用于方法图/宽表截图：手机端按 820px 原宽显示、可横滑、点开看原图。可放 ≤2MB 的 `.mp4` |
| `evidence` |  | 关键证据（数字、表格） |
| `case_analysis` |  | Case 分析（demo / 项目页） |
| `code_analysis` |  | 代码分析（文件:行号） |
| `solidity` |  | 扎实程度 |
| `concerns` |  | 疑点与信息缺口 |
| `takeaways` |  | 对 Henry 的启发 |
| `details` |  | 完整细节，`<details>` 默认折叠 |

媒体文件必须放在 `assets/<同一天日期>/` 下，先用 `optimize_assets.py` 处理：图片 webp、宽 ≤1200px；视频 ≤2MB。

## 周总结 `data/weekly/YYYY-Www.json`（ISO 周，如 `2026-W41`）

| 字段 | 必填 | 说明 |
|---|---|---|
| `week` | ✔ | 与文件名相同 |
| `title` | ✔ | 一句话：本周方向整体走向 |
| `summary` | ✔ | 周总结正文（Markdown） |
| `range` |  | `["2026-10-05", "2026-10-09"]` |
| `highlights` |  | `[{"date": "2026-10-09", "paper_id": "pac", "title": "...", "note": "..."}]`，链接到当天卡片 |
| `threads` |  | 方向脉络（Markdown） |
| `watchlist` |  | 下周关注（Markdown） |

## 最小示例（结构示意，非真实内容）

```json
{
  "date": "2026-10-09",
  "headline": "……",
  "papers": [
    {
      "id": "paper-slug",
      "rating": "must",
      "directions": ["av-streaming"],
      "title": "……",
      "tldr": "……",
      "links": {"paper": "https://arxiv.org/abs/xxxx.xxxxx"},
      "coverage": {"paper": "full", "demo": "partial", "code": "unavailable"}
    }
  ],
  "trend_summary": "……"
}
```

## 专题 `data/topics/<slug>.json`

适合季度综述等长文，生成到 `topics/<slug>/`，汇总页顶部和「专题」区都有入口。

| 字段 | 必填 | 说明 |
|---|---|---|
| `slug` | ✔ | 与文件名相同（小写字母/数字/连字符） |
| `title` | ✔ | 专题标题 |
| `summary` | ✔ | 正文 Markdown，通常写成 `{"file": "topics/<slug>.md"}` |
| `desc` |  | 一句话说明（汇总页显示） |
| `updated` |  | 更新日期，用于排序 |
| `attachments` |  | 相对 `data/` 的附件路径数组，构建时复制到专题页同目录（正文里用文件名链接） |
