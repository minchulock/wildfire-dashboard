#!/usr/bin/env bash
# PostToolUse(Edit|Write): 수정된 .py 파일을 ruff로 자동 포맷·린트 수정한다.

file_path=$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))')

[[ "$file_path" != *.py ]] && exit 0
command -v ruff >/dev/null 2>&1 || { echo "ruff 미설치: pip install ruff" >&2; exit 0; }

ruff format --quiet "$file_path"
ruff check --fix --quiet "$file_path" || true
exit 0
