---
name: add-chart
description: 대시보드에 새 차트(plotly) 또는 지도(folium)를 추가할 때 사용. 차트 함수 작성 → 테스트 → app.py 연결까지 일관된 규칙으로 처리한다.
argument-hint: "[차트 설명, 예: 시도별 피해면적 막대 차트]"
---

# 차트 추가 절차

요청: $ARGUMENTS

## 1. 차트 함수 작성 (`src/charts.py`)
- 시그니처: `def <이름>_chart(df: pd.DataFrame) -> go.Figure` (지도는 `folium.Map` 반환)
- 입력 `df`는 `src/analysis.py`의 집계 결과를 받는다. 차트 함수 안에서 집계하지 않는다.
- 공통 스타일:
  - 제목·축 라벨·hover 텍스트 한국어, 단위 표기 (건, ha)
  - `template="plotly_white"`, 색상은 산불 테마 `#D9480F`(주), `#868E96`(보조)
  - 범주가 10개 이상이면 가로 막대로 바꾸고 내림차순 정렬
- 지도: 중심 `[36.5, 127.8]`, `zoom_start=7`, 버블 크기는 건수의 제곱근 비례

## 2. 테스트 (`tests/test_charts.py`)
- 작은 가짜 DataFrame으로 함수 호출 → 반환 타입과 trace 개수를 확인한다.

## 3. 대시보드 연결 (`app.py`)
- 알맞은 탭에 `st.plotly_chart(fig, width="stretch")` 또는 `st_folium(m)`으로 배치.
- 사이드바 필터가 적용된 `filtered_df`를 사용하는지 확인한다.

## 4. 확인
- `pytest -q tests/test_charts.py` 실행.
- 대시보드가 실행 중이면 Playwright MCP로 해당 탭 스크린샷을 찍어 확인한다.
- 필요 시 `viz-reviewer` 서브에이전트에게 리뷰를 요청하라고 제안한다.
