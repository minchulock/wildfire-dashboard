---
name: deploy-check
description: Streamlit Community Cloud 등에 배포하기 전 점검 체크리스트를 실행한다. "배포 준비", "배포 전 확인", "deploy check" 요청 시 사용.
disable-model-invocation: true
---

# 배포 전 점검

아래 항목을 하나씩 실제로 확인하고, 마지막에 ✅/❌ 표로 결과를 보고한다. ❌ 항목은 수정 방법을 제안한다.

## 코드
- [ ] `pytest -q` 전부 통과
- [ ] `ruff check .` 경고 없음
- [ ] `app.py`가 절대경로(`/Users/...`)를 사용하지 않음 — `Path(__file__).parent` 기준 상대경로

## 의존성
- [ ] `requirements.txt` 존재, 실제 import 하는 패키지(streamlit, pandas, plotly, folium, streamlit-folium)가 모두 포함
- [ ] 버전 고정(`==`) 여부 확인

## 데이터
- [ ] 앱이 읽는 데이터 파일이 저장소에 포함되어 있음 (`data/processed/`), 용량 100MB 미만
- [ ] 원본 데이터 출처·라이선스(공공누리)를 README에 기재

## 보안
- [ ] `.env`, `.streamlit/secrets.toml`이 `.gitignore`에 포함
- [ ] 코드/노트북 출력에 API 키가 하드코딩되어 있지 않음 (`git grep -nEi "(servicekey|api[_-]?key|secret|token)\s*=\s*['\"]?[A-Za-z0-9%+/]{20,}"`)
- [ ] `app.py`가 API를 직접 호출하지 않고 `data/processed/` 파일만 읽음 (배포 환경에 키가 없어도 동작)
- [ ] API 호출이 꼭 필요하면 Streamlit Cloud Secrets에 `FOREST_FIRE_SERVICE_KEY` 등록 안내

## Git / GitHub
- [ ] 커밋되지 않은 변경 없음 (`git status`)
- [ ] 원격 저장소가 public 이거나 Streamlit Cloud에 권한 연결됨 (GitHub MCP로 확인)

## 로컬 실행
- [ ] `streamlit run app.py` 후 Playwright MCP로 http://localhost:8501 접속, 에러 메시지 없는지 스크린샷 확인
