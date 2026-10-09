#!/usr/bin/env python3
"""把原始图片 / 视频压缩后放进 assets/YYYY-MM-DD/。

  python optimize_assets.py 2026-10-09 raw/fig1.png raw/demo.mp4 ...
  python optimize_assets.py 2026-10-09 raw/           # 整个目录
  python optimize_assets.py --audit                    # 检查 assets/ 下是否有超限文件

图片 -> webp，宽度 ≤1200px，quality 80（超过 400KB 自动降质量）。
视频 -> mp4(H.264 + AAC 64k，保留音轨：音视频方向需要听)，宽度 ≤720px，默认截前 8 秒，
        逐步提高压缩直到 ≤2MB；做不到就放弃并提示只放链接。
依赖：Pillow（pip install pillow）、ffmpeg。
"""
import argparse, re, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IMG = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".gif"}
VID = {".mp4", ".mov", ".webm", ".mkv", ".avi", ".m4v"}
MAX_W, MAX_IMG, MAX_VID = 1200, 400 * 1024, 2 * 1024 * 1024


def slug(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "file"


def do_image(src, dst_dir, name):
    from PIL import Image
    im = Image.open(src)
    im.seek(0)
    im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB")
    if im.width > MAX_W:
        im = im.resize((MAX_W, round(im.height * MAX_W / im.width)), Image.LANCZOS)
    out = dst_dir / f"{name}.webp"
    for q in (80, 70, 60, 50, 40):
        im.save(out, "WEBP", quality=q, method=6)
        if out.stat().st_size <= MAX_IMG:
            break
    return out


def do_video(src, dst_dir, name, start, seconds):
    if not shutil.which("ffmpeg"):
        sys.exit("需要 ffmpeg")
    out = dst_dir / f"{name}.mp4"
    for crf, w in ((28, 720), (32, 640), (35, 480), (38, 360)):
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as t:
            tmp = Path(t.name)
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", str(start), "-t", str(seconds), "-i", str(src),
               "-vf", f"scale='min({w},iw)':-2,fps='min(25,source_fps)'", "-c:v", "libx264", "-preset", "slow",
               "-crf", str(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart",
               "-c:a", "aac", "-b:a", "64k", "-ac", "2", str(tmp)]
        r = subprocess.run(cmd)
        if r.returncode != 0:  # fps 表达式在老版 ffmpeg 不支持时退回
            cmd[cmd.index("-vf") + 1] = f"scale='min({w},iw)':-2"
            subprocess.run(cmd, check=True)
        if tmp.stat().st_size <= MAX_VID:
            shutil.move(tmp, out)
            return out
        tmp.unlink()
    print(f"  ✘ {src} 压不到 2MB，请缩短 --seconds，或只在数据里放链接")
    return None


def audit():
    bad = 0
    for f in sorted((ROOT / "assets").rglob("*")):
        if f.is_file() and f.name != ".gitkeep":
            lim = MAX_VID if f.suffix.lower() in VID else MAX_IMG * 1.5
            if f.stat().st_size > lim:
                bad += 1
                print(f"超限 {f.relative_to(ROOT)} {f.stat().st_size/1e6:.2f}MB")
    total = sum(f.stat().st_size for f in (ROOT / "assets").rglob("*") if f.is_file())
    print(f"assets 总大小 {total/1e6:.1f}MB，超限文件 {bad} 个")
    sys.exit(1 if bad else 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("date", nargs="?")
    ap.add_argument("inputs", nargs="*")
    ap.add_argument("--seconds", type=float, default=8, help="视频截取时长（秒）")
    ap.add_argument("--start", type=float, default=0, help="视频起始时间（秒）")
    ap.add_argument("--prefix", default="", help="输出文件名前缀，通常用论文 id")
    ap.add_argument("--audit", action="store_true")
    a = ap.parse_args()
    if a.audit:
        return audit()
    if not a.date or not re.match(r"^\d{4}-\d{2}-\d{2}$", a.date) or not a.inputs:
        ap.error("用法：optimize_assets.py YYYY-MM-DD 文件或目录 ...")
    dst = ROOT / "assets" / a.date
    dst.mkdir(parents=True, exist_ok=True)
    files = []
    for x in map(Path, a.inputs):
        files += sorted(p for p in x.rglob("*") if p.is_file()) if x.is_dir() else [x]
    for f in files:
        name = slug((a.prefix + "-" if a.prefix else "") + f.stem)
        ext = f.suffix.lower()
        if ext in IMG:
            o = do_image(f, dst, name)
        elif ext in VID:
            o = do_video(f, dst, name, a.start, a.seconds)
        else:
            print(f"  跳过 {f}")
            continue
        if o:
            print(f"  ✔ {o.relative_to(ROOT)}  {o.stat().st_size/1024:.0f}KB  -> 数据里写 \"src\": \"{o.relative_to(ROOT).as_posix()}\"")


if __name__ == "__main__":
    main()
