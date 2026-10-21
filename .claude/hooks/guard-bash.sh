#!/usr/bin/env bash
# PreToolUse(Bash): 위험한 명령(원본 데이터 삭제, 강제 push, 비밀파일 커밋)을 차단한다.

cmd=$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("command",""))')

block() { echo "🚫 차단됨: $1" >&2; exit 2; }

[[ "$cmd" =~ rm[[:space:]].*data/raw ]]           && block "data/raw/ 원본 데이터는 삭제할 수 없습니다."
[[ "$cmd" =~ git[[:space:]]+push.*(--force|-f) ]] && block "강제 push는 실습에서 금지입니다. 일반 push를 사용하세요."
[[ "$cmd" =~ git[[:space:]]+add.*(\.env([[:space:]]|$)|secrets\.toml) ]] && block ".env / secrets.toml 은 커밋하면 안 됩니다."
[[ "$cmd" =~ (cat|less|more|head|tail|grep|source|printenv|env)([[:space:]].*)?\.env([[:space:]]|$) ]] && block ".env 에는 인증키가 있어 열람할 수 없습니다. 설정 확인은 .env.example 을 보세요."
[[ "$cmd" =~ (echo|printenv).*FOREST_FIRE_SERVICE_KEY ]] && block "인증키 값을 출력할 수 없습니다."
exit 0
