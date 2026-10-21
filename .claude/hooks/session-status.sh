#!/usr/bin/env bash
# SessionStart: CLAUDE.md 체크리스트에서 진행 상황을 계산해 Claude 컨텍스트에 넣는다.
# (SessionStart hook의 stdout은 Claude의 컨텍스트로 추가된다)

cd "$CLAUDE_PROJECT_DIR" || exit 0
done_n=$(grep -c '^- \[x\]' CLAUDE.md)
todo_n=$(grep -c '^- \[ \]' CLAUDE.md)
next=$(grep -m1 '^- \[ \]' CLAUDE.md | sed 's/^- \[ \] //')

echo "📋 실습 진행 상황: 완료 ${done_n}개 / 남음 ${todo_n}개"
[[ -n "$next" ]] && echo "👉 다음 할 일: ${next}"
exit 0
