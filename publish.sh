#!/usr/bin/env bash
# 一条命令发布：校验 + 本地构建 + commit + push（GitHub Actions 负责部署到 Pages）
#   ./publish.sh                 # 提交信息自动用最新数据日期
#   ./publish.sh "自定义提交信息"
#   NO_WAIT=1 ./publish.sh        # 推送后不等待部署完成
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
[ -x /home/box/agent-data/paper-digest/.venv/bin/python ] && PY=/home/box/agent-data/paper-digest/.venv/bin/python

"$PY" optimize_assets.py --audit
"$PY" build.py                      # 本地构建一遍确保不报错（docs/ 不入库）

latest=$(ls data/*.json 2>/dev/null | sed -E 's#.*/##; s#\.json$##' | sort | tail -1 || true)
msg="${1:-digest ${latest:-update}}"

git add -A data assets static build.py optimize_assets.py publish.sh README.md SCHEMA.md .github .gitignore 2>/dev/null || true
if git diff --cached --quiet; then
  echo "没有改动需要提交"
else
  git commit -q -m "$msg"
  git push -q origin HEAD:main
  echo "已推送：$msg"
fi

if [ -z "${NO_WAIT:-}" ] && command -v gh >/dev/null; then
  sha=$(git rev-parse HEAD); run=""
  for i in $(seq 1 20); do
    run=$(gh run list --workflow pages.yml --limit 5 --json databaseId,headSha -q ".[] | select(.headSha==\"$sha\") | .databaseId" 2>/dev/null | head -1 || true)
    [ -n "$run" ] && break; sleep 3
  done
  if [ -n "$run" ]; then
    if gh run watch "$run" --exit-status >/dev/null 2>&1; then echo "部署完成（run $run）"; else echo "⚠ 部署失败：gh run view $run --log-failed"; exit 1; fi
  else
    echo "⚠ 没找到对应的部署 run（可能已部署过或尚未触发）"
  fi
  base="https://thughy.github.io/video-wm-daily"
  url="$base/"; [ -n "$latest" ] && url="$base/daily/$latest/"
  for i in 1 2 3 4 5 6; do
    code=$(curl -s -o /dev/null -w '%{http_code}' "$url?t=$(date +%s)")
    [ "$code" = 200 ] && break; sleep 10
  done
  echo "线上检查 $url -> HTTP $code"
fi
