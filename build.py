#!/usr/bin/env python3
"""构建每日论文精读静态站点。

用法:
  python build.py                       # data/ + assets/ -> docs/（输出目录不入库，由 GitHub Actions 部署）
  python build.py --check               # 只校验数据，不生成
  python build.py --data DIR --assets DIR --out DIR   # 用其他目录预览（例如示例数据）

依赖：python-markdown（pip install markdown）。
"""
import argparse, datetime as dt, html, json, os, re, shutil, sys
from pathlib import Path

try:
    import markdown as _md
except ImportError:
    sys.exit("缺少依赖：pip install markdown")

ROOT = Path(__file__).resolve().parent
SITE_TITLE = "视频生成 · World Model 每日精读"
RATINGS = {"must": ("必读", "b-must"), "worth": ("值得看", "b-worth"), "fyi": ("了解即可", "b-fyi")}
RATING_ORDER = {"must": 0, "worth": 1, "fyi": 2}
DIRECTIONS = {
    "av-streaming": "音视频流式",
    "streaming": "流式视频",
    "world-model": "World Model",
    "video-gen": "视频生成",
    "video-edit": "视频编辑",
    "other": "其他",
}
COVERAGE_KEYS = [("paper", "论文"), ("demo", "Demo/Case"), ("code", "代码")]
COVERAGE_VALUES = {"full": "✔ 已深读", "partial": "◐ 部分", "none": "✘ 未看", "unavailable": "— 未公开"}
CARD_FIELDS = [  # 固定顺序
    ("insight", "核心 insight"),
    ("context", "与已有工作的区别 / 脉络"),
    ("method", "方法要点"),
    ("evidence", "关键证据"),
    ("case_analysis", "Case 分析"),
    ("code_analysis", "代码分析"),
    ("concerns", "疑点与信息缺口"),
]
MAX_IMAGE_BYTES = 600 * 1024
MAX_VIDEO_BYTES = 2 * 1024 * 1024
IMAGE_EXT = {".webp", ".png", ".jpg", ".jpeg", ".gif", ".svg"}
VIDEO_EXT = {".mp4", ".webm"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
WEEK_RE = re.compile(r"^\d{4}-W\d{2}$")

e = lambda s: html.escape(str(s or ""), quote=True)


def md(text):
    if not text:
        return ""
    return _md.markdown(str(text), extensions=["extra", "sane_lists"], output_format="html")


class DataError(Exception):
    pass


# ---------------------------------------------------------------- 读取与校验
def resolve_text(value, data_dir):
    """字段可以是字符串，也可以是 {"file": "相对 data/ 的 .md 路径"}。"""
    if isinstance(value, dict) and "file" in value:
        p = data_dir / value["file"]
        if not p.exists():
            raise DataError(f"找不到 Markdown 文件 {p}")
        return p.read_text(encoding="utf-8")
    return value or ""


def load_days(data_dir, assets_dir, errors, warnings):
    days = []
    for f in sorted(data_dir.glob("*.json")):
        if not DATE_RE.match(f.stem):
            warnings.append(f"跳过不符合 YYYY-MM-DD 命名的文件 {f.name}")
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as ex:
            errors.append(f"{f.name}: JSON 解析失败 {ex}")
            continue
        where = f.name
        if d.get("date") != f.stem:
            errors.append(f"{where}: date 字段必须等于文件名 {f.stem}")
        if not d.get("headline"):
            errors.append(f"{where}: 缺少 headline")
        if d.get("draft"):
            warnings.append(f"{where}: draft=true，跳过")
            continue
        ids = set()
        for i, p in enumerate(d.get("papers", [])):
            pw = f"{where} papers[{i}]"
            for k in ("id", "rating", "directions", "title", "tldr"):
                if not p.get(k):
                    errors.append(f"{pw}: 缺少 {k}")
            pid = p.get("id", "")
            if not re.match(r"^[a-z0-9][a-z0-9-]*$", pid or "x"):
                errors.append(f"{pw}: id 只能用小写字母/数字/连字符")
            if pid in ids:
                errors.append(f"{pw}: id 重复 {pid}")
            ids.add(pid)
            if p.get("rating") not in RATINGS:
                errors.append(f"{pw}: rating 必须是 {list(RATINGS)}")
            for dname in p.get("directions", []):
                if dname not in DIRECTIONS:
                    errors.append(f"{pw}: 未知方向 {dname}，可选 {list(DIRECTIONS)}")
            for k, _ in CARD_FIELDS + [("details", "")]:
                try:
                    p[k] = resolve_text(p.get(k), data_dir)
                except DataError as ex:
                    errors.append(f"{pw}.{k}: {ex}")
            for k, v in (p.get("coverage") or {}).items():
                if k in dict(COVERAGE_KEYS) and v not in COVERAGE_VALUES:
                    errors.append(f"{pw}.coverage.{k}: 取值必须是 {list(COVERAGE_VALUES)}")
            for m in p.get("media", []):
                src = m.get("src", "")
                if not src.startswith(f"assets/{f.stem}/"):
                    errors.append(f"{pw}: 媒体路径必须放在 assets/{f.stem}/ 下：{src}")
                    continue
                ap = assets_dir / src[len("assets/"):]
                if not ap.exists():
                    errors.append(f"{pw}: 媒体文件不存在 {src}")
                    continue
                ext, size = ap.suffix.lower(), ap.stat().st_size
                if ext in VIDEO_EXT and size > MAX_VIDEO_BYTES:
                    errors.append(f"{pw}: 视频 {src} {size/1e6:.1f}MB 超过 2MB，先跑 optimize_assets.py")
                elif ext in IMAGE_EXT and size > MAX_IMAGE_BYTES:
                    warnings.append(f"{pw}: 图片 {src} {size/1e3:.0f}KB 偏大，建议 optimize_assets.py 压缩成 webp")
                elif ext not in IMAGE_EXT | VIDEO_EXT:
                    errors.append(f"{pw}: 不支持的媒体类型 {src}")
        try:
            d["trend_summary"] = resolve_text(d.get("trend_summary"), data_dir)
        except DataError as ex:
            errors.append(f"{where}.trend_summary: {ex}")
        days.append(d)
    days.sort(key=lambda x: x["date"])
    return days


def load_weeks(data_dir, errors):
    weeks = []
    wd = data_dir / "weekly"
    if not wd.exists():
        return weeks
    for f in sorted(wd.glob("*.json")):
        if not WEEK_RE.match(f.stem):
            continue
        try:
            w = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as ex:
            errors.append(f"weekly/{f.name}: JSON 解析失败 {ex}")
            continue
        if w.get("week") != f.stem:
            errors.append(f"weekly/{f.name}: week 字段必须等于文件名")
        if not w.get("title") or not w.get("summary"):
            errors.append(f"weekly/{f.name}: 缺少 title 或 summary")
        try:
            w["summary"] = resolve_text(w.get("summary"), data_dir)
            w["threads"] = resolve_text(w.get("threads"), data_dir)
        except DataError as ex:
            errors.append(f"weekly/{f.name}: {ex}")
        weeks.append(w)
    weeks.sort(key=lambda x: x["week"], reverse=True)
    return weeks


# ---------------------------------------------------------------- HTML 片段
def page(title, body, rel, desc=""):
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<link rel="stylesheet" href="{rel}static/style.css">
</head><body><div class="wrap">
<header class="site"><a class="brand" href="{rel}index.html">{e(SITE_TITLE)}</a>
<nav><a href="{rel}index.html">汇总</a><a href="{rel}index.html#weekly">周度脉络</a></nav></header>
{body}
<footer>纯静态页面 · 每个工作日更新 · 评级：必读 / 值得看 / 了解即可</footer>
</div></body></html>
"""


def badge(r):
    label, cls = RATINGS[r]
    return f'<span class="badge {cls}">{label}</span>'


def tags(dirs):
    return "".join(f'<span class="tag{" av" if d=="av-streaming" else ""}">{e(DIRECTIONS[d])}</span>' for d in dirs)


def is_av(p):
    return "av-streaming" in p.get("directions", [])


def sort_papers(ps):
    return sorted(ps, key=lambda p: (RATING_ORDER[p["rating"]], not is_av(p)))


def links_html(p):
    L = p.get("links") or {}
    out = []
    for k, label in (("paper", "论文"), ("project", "项目页 / Demo"), ("code", "代码")):
        if L.get(k):
            out.append(f'<a href="{e(L[k])}" target="_blank" rel="noopener">{label} ↗</a>')
    for x in L.get("other", []) or []:
        out.append(f'<a href="{e(x.get("url"))}" target="_blank" rel="noopener">{e(x.get("label"))} ↗</a>')
    return f'<div class="links">{"".join(out)}</div>' if out else ""


def coverage_html(p):
    c = p.get("coverage") or {}
    if not c:
        return ""
    items = [f"<span>{lab}：{COVERAGE_VALUES.get(c.get(k), '—')}</span>" for k, lab in COVERAGE_KEYS if k in c]
    note = f'<span>{e(c["note"])}</span>' if c.get("note") else ""
    return f'<div class="coverage">{"".join(items)}{note}</div>'


def media_html(p, rel):
    out = []
    for m in p.get("media", []) or []:
        src = rel + m["src"]
        cap = f"<figcaption>{e(m.get('caption'))}</figcaption>" if m.get("caption") else ""
        if Path(m["src"]).suffix.lower() in VIDEO_EXT:
            el = f'<video src="{e(src)}" controls preload="none" playsinline></video>'
        else:
            el = f'<img src="{e(src)}" alt="{e(m.get("caption") or p["title"])}" loading="lazy">'
        out.append(f"<figure>{el}{cap}</figure>")
    return "".join(out)


def card_html(p, rel):
    inst = " · ".join(p.get("institutions", []) or [])
    meta = []
    if inst:
        meta.append(e(inst))
    if p.get("published"):
        meta.append(e(p["published"]))
    fields = []
    for k, label in CARD_FIELDS:
        if p.get(k):
            cls = " concerns" if k == "concerns" else ""
            fields.append(f'<div class="field{cls}"><div class="label">{label}</div><div class="md">{md(p[k])}</div></div>')
        if k == "insight":
            fields.append(media_html(p, rel))
    details = (f'<details><summary>完整细节</summary><div class="md">{md(p["details"])}</div></details>'
               if p.get("details") else "")
    reason = f'<div class="meta">评级理由：{e(p["rating_reason"])}</div>' if p.get("rating_reason") else ""
    return f"""<article class="card {p['rating']}" id="p-{e(p['id'])}">
<div>{badge(p['rating'])} {tags(p.get('directions', []))}</div>
<h3 style="margin-top:8px">{e(p['title'])}</h3>
<div class="meta">{' ｜ '.join(meta)}</div>
{links_html(p)}{coverage_html(p)}{reason}
<div class="tldr">{e(p['tldr'])}</div>
{''.join(fields)}{details}
</article>"""


def quick_li(p):
    return (f'<li>{badge(p["rating"])}<a href="#p-{e(p["id"])}"><span class="t">{e(p["title"])}</span>'
            f'<span class="s">{e(p["tldr"])}</span></a></li>')


# ---------------------------------------------------------------- 页面
def day_url(date):
    return f"daily/{date}/index.html"


def render_day(d, prev_d, next_d, weeks_by_id):
    rel = "../../"
    papers = sort_papers(d.get("papers", []))
    main = [p for p in papers if p["rating"] != "fyi"]
    fyi = [p for p in papers if p["rating"] == "fyi"]
    av = [p for p in main if is_av(p)]
    rest = [p for p in main if not is_av(p)]
    n_must = sum(p["rating"] == "must" for p in papers)
    n_worth = sum(p["rating"] == "worth" for p in papers)

    quick = []
    if av:
        quick.append(f'<div class="zone av"><h4>音视频流式 · 重点方向</h4><ul class="quick">{"".join(map(quick_li, av))}</ul></div>')
    if rest:
        quick.append(f'<div class="zone"><h4>其他方向</h4><ul class="quick">{"".join(map(quick_li, rest))}</ul></div>')
    if not main:
        quick.append('<p class="sub">今天没有达到「值得看」标准的论文。</p>')

    week_id = "%d-W%02d" % dt.date.fromisoformat(d["date"]).isocalendar()[:2]
    week_link = (f' ｜ <a href="{rel}weekly/{week_id}/index.html">本周脉络总结</a>' if week_id in weeks_by_id else "")
    example = '<p class="headline" style="border-left-color:#c00">⚠ 示例数据，仅用于测试排版，内容不是真实论文分析。</p>' if d.get("example") else ""
    body = [example,
            f'<h1>{e(d["date"])} 精读</h1>',
            f'<p class="sub">必读 {n_must} · 值得看 {n_worth} · 了解即可 {len(fyi)}{week_link}</p>',
            f'<div class="headline">{e(d["headline"])}</div>',
            '<h2 id="quick">速览</h2>', "".join(quick)]
    if main:
        body.append('<h2 id="cards">逐篇精读</h2>')
        body += [card_html(p, rel) for p in main]
    if fyi:
        body.append(f'<details class="fyi" id="fyi"><summary>了解即可（{len(fyi)} 篇，默认折叠）</summary>'
                    + "".join(card_html(p, rel) for p in fyi) + "</details>")
    if d.get("trend_summary"):
        body.append(f'<h2 id="trend">趋势总结</h2><div class="md">{md(d["trend_summary"])}</div>')
    pv = (f'<a href="{rel}{day_url(prev_d)}">← 前一天 {prev_d}</a>' if prev_d else '<span class="disabled">← 没有更早的了</span>')
    nx = (f'<a href="{rel}{day_url(next_d)}">后一天 {next_d} →</a>' if next_d else '<span class="disabled">已是最新 →</span>')
    body.append(f'<nav class="pager">{pv}<a href="{rel}index.html">汇总</a>{nx}</nav>')
    return page(f'{d["date"]} · {SITE_TITLE}', "\n".join(body), rel, d["headline"])


def render_week(w):
    rel = "../../"
    hl = []
    for h in w.get("highlights", []) or []:
        href = f'{rel}{day_url(h["date"])}' + (f'#p-{h["paper_id"]}' if h.get("paper_id") else "")
        hl.append(f'<li><a href="{e(href)}">{e(h.get("title") or h["date"])}</a>'
                  + (f' — {e(h["note"])}' if h.get("note") else "") + "</li>")
    rng = w.get("range") or []
    body = (f'<h1>{e(w["week"])} 周度脉络</h1>'
            f'<p class="sub">{e(" ~ ".join(rng))}</p>'
            f'<div class="headline">{e(w["title"])}</div>'
            f'<div class="md">{md(w["summary"])}</div>'
            + (f'<h2>本周关键论文</h2><ul>{"".join(hl)}</ul>' if hl else "")
            + (f'<h2>方向脉络</h2><div class="md">{md(w["threads"])}</div>' if w.get("threads") else "")
            + (f'<h2>下周关注</h2><div class="md">{md(w["watchlist"])}</div>' if w.get("watchlist") else "")
            + f'<nav class="pager"><span></span><a href="{rel}index.html">汇总</a><span></span></nav>')
    return page(f'{w["week"]} 周度脉络 · {SITE_TITLE}', body, rel, w["title"])


def pick_focus(days):
    if not days:
        return []
    last = dt.date.fromisoformat(days[-1]["date"])
    cands = []
    for d in days:
        if (last - dt.date.fromisoformat(d["date"])).days > 6:
            continue
        for p in d.get("papers", []):
            if p["rating"] == "must" or p.get("highlight"):
                cands.append((not p.get("highlight"), not is_av(p), -int(d["date"].replace("-", "")), d["date"], p))
    cands.sort(key=lambda x: x[:3])
    return [(c[3], c[4]) for c in cands[:2]]


def render_index(days, weeks):
    rel = ""
    if not days:
        body = ('<h1>每日论文精读</h1><p class="sub">World Model · 视频生成 · 视频编辑 · 流式视频生成（重点：音视频流式生成）</p>'
                '<div class="empty">第一期即将发布</div>')
        return page(SITE_TITLE, body, rel)
    out = ['<h1>每日论文精读</h1><p class="sub">World Model · 视频生成 · 视频编辑 · 流式视频生成（重点：音视频流式生成）。只收录精读后达到「值得看」以上的论文。</p>']
    focus = pick_focus(days)
    if focus:
        items = "".join(
            f'<a class="item" href="{day_url(dd)}#p-{e(p["id"])}"><div class="when">{badge(p["rating"])} {tags(p.get("directions", []))} {dd}</div>'
            f'<div class="tt">{e(p["title"])}</div><div class="s">{e(p["tldr"])}</div></a>' for dd, p in focus)
        out.append(f'<h2>本周最重要</h2><div class="focus">{items}</div>')
    if weeks:
        w = weeks[0]
        out.append(f'<p class="sub" style="margin-top:14px">最新周度脉络：<a href="weekly/{e(w["week"])}/index.html">{e(w["week"])} · {e(w["title"])}</a></p>')
    btn = lambda k, v, lab, on=False: f'<button data-k="{k}" data-v="{v}" aria-pressed="{"true" if on else "false"}">{lab}</button>'
    used_dirs = [k for k in DIRECTIONS if any(k in p.get("directions", []) for d in days for p in d.get("papers", []))]
    out.append('<h2>每日精读</h2><div class="filters"><div class="grp"><span class="lab">方向</span>'
               + btn("dir", "all", "全部", True) + "".join(btn("dir", k, DIRECTIONS[k]) for k in used_dirs)
               + '</div><div class="grp"><span class="lab">评级</span>' + btn("rating", "all", "全部", True)
               + btn("rating", "must", "必读") + btn("rating", "worth", "值得看") + "</div></div>")
    rows = []
    for d in reversed(days):
        ps = sort_papers([p for p in d.get("papers", []) if p["rating"] != "fyi"])
        nm = sum(p["rating"] == "must" for p in ps)
        nw = len(ps) - nm
        lis = "".join(
            f'<li data-rating="{p["rating"]}" data-dirs="{e(" ".join(p.get("directions", [])))}">{badge(p["rating"])} '
            f'<a href="{day_url(d["date"])}#p-{e(p["id"])}">{e(p["title"])}</a></li>' for p in ps)
        rows.append(f'<li><div class="dayhead"><a class="d" href="{day_url(d["date"])}">{d["date"]}</a>'
                    f'<a class="h" href="{day_url(d["date"])}" style="color:inherit">{e(d["headline"])}</a>'
                    f'<span class="cnt">必读 {nm} · 值得看 {nw}</span></div>'
                    + (f'<ul class="dp">{lis}</ul>' if lis else "") + "</li>")
    out.append(f'<ol class="days">{"".join(rows)}</ol><p class="noresult">没有符合筛选条件的论文。</p>')
    out.append('<h2 id="weekly">周度脉络</h2>' + (
        '<ul class="weeks">' + "".join(f'<li><a href="weekly/{e(w["week"])}/index.html">{e(w["week"])}</a> · {e(w["title"])}</li>' for w in weeks) + "</ul>"
        if weeks else '<p class="sub">每周五发布，第一份即将上线。</p>'))
    out.append('<script src="static/filter.js" defer></script>')
    return page(SITE_TITLE, "\n".join(out), rel)


# ---------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(ROOT / "data"))
    ap.add_argument("--assets", default=str(ROOT / "assets"))
    ap.add_argument("--out", default=str(ROOT / "docs"))
    ap.add_argument("--check", action="store_true", help="只校验，不生成")
    a = ap.parse_args()
    data_dir, assets_dir, out = Path(a.data), Path(a.assets), Path(a.out)
    errors, warnings = [], []
    days = load_days(data_dir, assets_dir, errors, warnings)
    weeks = load_weeks(data_dir, errors)
    if data_dir.resolve() == (ROOT / "data").resolve():
        for d in days:
            if d.get("example"):
                errors.append(f"{d['date']}.json 标记为 example，示例数据不能放进正式 data/ 目录")
    for w in warnings:
        print("警告:", w)
    if errors:
        for x in errors:
            print("错误:", x)
        sys.exit(f"校验失败：{len(errors)} 个错误")
    print(f"校验通过：{len(days)} 天，{len(weeks)} 份周总结")
    if a.check:
        return
    if out.exists():
        shutil.rmtree(out)
    (out / "static").mkdir(parents=True)
    for f in (ROOT / "static").iterdir():
        shutil.copy2(f, out / "static" / f.name)
    (out / ".nojekyll").write_text("")
    if assets_dir.exists():
        shutil.copytree(assets_dir, out / "assets", ignore=shutil.ignore_patterns(".gitkeep"))
    weeks_by_id = {w["week"]: w for w in weeks}
    for i, d in enumerate(days):
        p = out / "daily" / d["date"]
        p.mkdir(parents=True)
        prev_d = days[i - 1]["date"] if i > 0 else None
        next_d = days[i + 1]["date"] if i + 1 < len(days) else None
        (p / "index.html").write_text(render_day(d, prev_d, next_d, weeks_by_id), encoding="utf-8")
    for w in weeks:
        p = out / "weekly" / w["week"]
        p.mkdir(parents=True)
        (p / "index.html").write_text(render_week(w), encoding="utf-8")
    (out / "index.html").write_text(render_index(days, weeks), encoding="utf-8")
    if days:  # latest/ 永远跳到最新一期
        (out / "latest").mkdir()
        (out / "latest" / "index.html").write_text(
            f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=../{day_url(days[-1]["date"])}">'
            f'<a href="../{day_url(days[-1]["date"])}">最新一期</a>', encoding="utf-8")
    print(f"已生成到 {out}")


if __name__ == "__main__":
    main()
