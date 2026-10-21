#!/usr/bin/env bash
# PreToolUse(Edit|Write): 인증키처럼 보이는 값을 파일에 직접 쓰는 것을 차단한다.
# 키는 사용자가 .env 에 직접 넣고, 코드는 src.config.get_api_config() 로만 읽어야 한다.

python3 -c '
import json, re, sys
ti = json.load(sys.stdin).get("tool_input", {})
text = (ti.get("content") or "") + (ti.get("new_string") or "")
text += "".join(e.get("new_string", "") for e in ti.get("edits", []))
pattern = r"(ServiceKey|SERVICE_KEY)\s*[=:]\s*[\"\x27]?[A-Za-z0-9%+/]{20,}"
if re.search(pattern, text):
    print("🚫 인증키로 보이는 값이 포함되어 있습니다. 키는 .env(FOREST_FIRE_SERVICE_KEY)에만 두고 src.config.get_api_config()로 읽으세요. (CLAUDE.md §4-2)", file=sys.stderr)
    sys.exit(2)
'
