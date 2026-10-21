#!/usr/bin/env bash
# PreToolUse(Edit|Write): data/raw/ 아래 원본 데이터 수정을 차단한다.
# exit 2 → 도구 실행이 막히고 stderr 메시지가 Claude에게 전달된다.

file_path=$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))')

if [[ "$file_path" == *"/data/raw/"* || "$file_path" == data/raw/* ]]; then
  echo "🚫 data/raw/ 는 원본 데이터 보관 폴더라 수정할 수 없습니다. 가공 결과는 data/processed/ 에 저장하세요. (CLAUDE.md §4)" >&2
  exit 2
fi
exit 0
