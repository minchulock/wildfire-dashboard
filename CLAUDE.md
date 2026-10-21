# CLAUDE.md — 산불 발생 현황 분석 및 시각화 대시보드

> 이 파일은 Claude Code가 세션을 시작할 때마다 자동으로 읽는 **프로젝트 메모리**입니다.
> 바이브 코딩 실습에서 Claude가 지켜야 할 규칙, 구조, 작업 순서를 정의합니다.

## 1. 프로젝트 개요

- **목표**: 공공데이터포털(data.go.kr)의 산림청 「산불발생통계(대국민포털)」 데이터를 **OpenAPI로 수집**·분석하고,
  Streamlit 대시보드로 시각화한 뒤 클라우드에 배포하여 외부 URL로 공개한다.
- **대상**: 바이브 코딩 입문 실습생. 코드는 **읽기 쉽고 짧게**, 설명은 **한국어로** 작성한다.
- **실습 방식**: 단계(1~5)별로 진행하며, 한 단계가 끝나면 체크리스트(§7)를 갱신하고 커밋한다.

## 2. 기술 스택

| 영역 | 선택 | 비고 |
|---|---|---|
| 언어 | Python 3.11+ | |
| 데이터 수집 | requests + python-dotenv | 산림청 산불통계 OpenAPI (REST GET, XML) |
| 데이터 처리 | pandas | |
| 시각화 | plotly (차트), folium + streamlit-folium (지도) | matplotlib 사용 금지(대시보드 인터랙션 일관성) |
| 웹 대시보드 | Streamlit | React 버전은 심화 과제로만 |
| 포맷터/린터 | ruff | PostToolUse hook으로 자동 실행 |
| 테스트 | pytest | |
| 배포 | GitHub + Streamlit Community Cloud | 대안: Render, Hugging Face Spaces |

## 3. 디렉터리 구조

```
.
├── CLAUDE.md                 # (이 파일) 프로젝트 메모리
├── .env.example              # API endpoint·인증키 템플릿 → .env 로 복사해서 사용 (커밋 금지)
├── .streamlit/secrets.toml.example  # 배포용 Secrets 템플릿
├── .mcp.json                 # MCP 서버 설정 (GitHub, Playwright, Context7)
├── .claude/
│   ├── settings.json         # hooks · 권한 설정
│   ├── hooks/                # hook 스크립트
│   ├── skills/               # 재사용 작업 절차 (SKILL.md)
│   └── agents/               # 역할별 서브에이전트
├── data/
│   ├── raw/                  # API 수집 원본 CSV (fetch_api.py만 생성, 수정 금지! hook으로 보호됨)
│   ├── processed/            # 전처리 결과 (parquet/csv)
│   └── reference/            # 시군구 경계 GeoJSON·중심 좌표 (지도용)
├── src/
│   ├── config.py             # 1단계: 환경변수(.env / Streamlit secrets) 로딩
│   ├── fetch_api.py          # 1단계: 산불통계 OpenAPI 호출 → data/raw/ 저장
│   ├── load.py               # 1단계: 원본 CSV 로딩
│   ├── preprocess.py         # 1단계: 정제·파생 컬럼
│   ├── analysis.py           # 2단계: 집계 함수 (+4단계 hourly_pattern, kpi_summary)
│   ├── insights.py           # 4단계: 탭별 인사이트 문구
│   ├── build_centroids.py    # 3단계: 경계 GeoJSON → 시군구 중심 좌표 CSV
│   └── charts.py             # 3단계: plotly/folium 차트 생성 함수
├── app.py                    # 4단계: Streamlit 진입점
├── tests/                    # pytest
├── requirements.txt
└── README.md
```

## 4. 데이터 규칙 (매우 중요)

### 4-1. 데이터 출처: 산림청 산불통계 OpenAPI
CSV 파일 다운로드는 제공되지 않으며 **API 호출로만** 받는다. (근거: OpenAPI 활용가이드 v1.3)

| 항목 | 값 |
|---|---|
| 요청 주소 | 환경변수 `FOREST_FIRE_API_ENDPOINT` (기본: `http://apis.data.go.kr/1400000/forestStusService/getfirestatsservice`) |
| 방식 | REST GET, 응답 XML |
| 요청 파라미터 | `ServiceKey`(필수), `numOfRows`(필수), `pageNo`(필수), `searchStDt`·`searchEdDt`(옵션, `YYYYMMDD`, 발생일 기준) |
| 제한 | 초당 최대 30tps, `numOfRows`는 항목크기 2자리 → 99 이하 사용 |
| 정상 코드 | `resultCode=00`, 데이터 없음 `03`. 인증키 오류(`30`·`31`)는 `OpenAPI_ServiceResponse/cmmMsgHeader/returnReasonCode`로 옴 |

- 수집은 **연도 단위로 나눠** 페이지를 끝까지 돈다 (`src/fetch_api.py`). 수집 결과는 `data/raw/fire_stats_<시작>_<끝>.csv`(utf-8-sig).
- API를 반복 호출하지 않는다. 이미 받은 CSV가 있으면 그것을 쓰고, 대시보드는 **API를 직접 호출하지 않고** `data/processed/` 파일만 읽는다.

### 4-2. 인증키·환경설정 (비밀값)
- `FOREST_FIRE_SERVICE_KEY`, `FOREST_FIRE_API_ENDPOINT`, `FOREST_FIRE_NUM_OF_ROWS`는 **사용자가 `.env`에 직접 입력**한다. Claude는 `.env`를 읽거나 만들거나 키 값을 코드·문서·로그에 쓰지 않는다.
- 코드에서는 반드시 `src.config.get_api_config()`로만 읽는다. 키가 없으면 `.env.example` 안내 메시지를 띄운다.
- 배포 시에는 Streamlit Cloud **Secrets**에 같은 이름으로 등록한다 (`.streamlit/secrets.toml.example` 참고).
- 키는 Decoding 키 권장. Encoding 키(`%` 포함)는 `config.py`가 자동으로 디코딩한다.

### 4-3. 전처리 규칙
- **원본 보존**: `data/raw/` 파일은 Claude가 수정·삭제하지 않는다(수집 스크립트 실행만 허용). 가공 결과는 `data/processed/`에 저장.
- **컬럼명**: API 응답 필드를 `src/preprocess.py`의 `COLUMN_MAP`으로 변환한다.

  | API 필드 | 변환 컬럼 | 비고 |
  |---|---|---|
  | `startyear`·`startmonth`·`startday`·`starttime` | `year`, `month`, `day`, `start_at`(datetime) | |
  | `startdayofweek` | `weekday` | 예: 월요일 |
  | `endyear`·`endmonth`·`endday`·`endtime` | `end_at`(datetime) | 진화 소요시간 `duration_min` 파생 |
  | `locsi` / `locgungu` / `locmenu` / `locdong` / `locbunji` | `sido` / `sigungu` / `eupmyeon` / `dongri` / `bunji` | `locmenu`는 오타가 아니라 '읍면' 필드명 |
  | `firecause` | `cause` | |
  | `damagearea` | `damage_area_ha` | float 변환 |
- 일부 항목(예: `locdong`)은 응답에서 빠질 수 있다 → 결측으로 처리.
- **진화시간**: 음수(종료 `00:00:00` 기록) 또는 30일 초과(종료연도 오타)는 `duration_min` 결측 처리 (2015~2024 기준 27건). 행은 삭제하지 않는다.
- **지역 키**: `광주`처럼 시도·시군구 이름이 겹치므로 시군구 단위 집계·지도는 `region`(`"시도 시군구"`) 컬럼을 쓴다.
- **시도명 표준화**: `강원` / `강원도` / `강원특별자치도` 처럼 표기가 섞여 있으면 하나로 통일한다(`SIDO_NORMALIZE` 딕셔너리).
- **좌표**: API 응답에는 위경도가 없으므로 시군구 중심 좌표(`data/reference/sigungu_centroids.csv`)와 조인한다. 좌표를 지어내지 않는다.
  - 출처: 통계청 2013 시군구 경계([southkorea-maps](https://github.com/southkorea/southkorea-maps)) → `python -m src.build_centroids`로 생성
  - 매칭 규칙(`analysis.region_points`): 정확히 일치 → 별칭(`대구 군위`→2013 `경북 군위`) → 2013년 이후 신설 일반구는 상위 시(예: `청주 청원`→`청주`). 세종은 읍면 이름이 들어오거나 비어 있으므로 세종 중심 1곳에 표시
- **결측치**: 삭제 전에 몇 건이 빠지는지 반드시 출력/보고한다.

## 5. 코딩 규칙

- 분석 로직(`src/`)과 화면 로직(`app.py`)을 분리한다. `app.py`에는 pandas 집계 코드를 직접 쓰지 않는다.
- 모든 집계 함수는 `DataFrame`을 받아 `DataFrame`을 반환하는 **순수 함수**로 작성하고, `tests/`에 최소 1개 테스트를 둔다.
- Streamlit 데이터 로딩 함수에는 `@st.cache_data`를 붙인다.
- 차트 제목·축 라벨·범례는 **한국어**로, 단위(건, ha)를 표기한다.
- 함수에는 한 줄 한국어 docstring을 단다. 과도한 주석은 달지 않는다.
- 비밀값(API 키 등)은 `.env` / `st.secrets`로만 다루고 커밋하지 않는다. (§4-2)

## 6. 자주 쓰는 명령

```bash
pip install -r requirements.txt     # 의존성 설치
cp .env.example .env                # 환경설정 파일 생성 → 인증키는 사용자가 직접 입력
python -m src.fetch_api --start-year 2015 --end-year 2024   # API 수집 → data/raw/
streamlit run app.py                # 로컬 대시보드 실행 (http://localhost:8501)
pytest -q                           # 테스트
ruff check . && ruff format .       # 린트/포맷 (hook이 자동 실행하지만 수동도 가능)
```

## 7. 실습 단계 & 체크리스트

각 단계에서 **어떤 Claude Code 기능을 연습하는지** 함께 표시했다.

### 1단계 — 데이터 수집  `[CLAUDE.md] [Hooks]`
- [x] data.go.kr에서 「산림청_산불발생통계(대국민포털)」 OpenAPI 활용신청 → 인증키 발급 (사람이 직접)
- [x] `cp .env.example .env` 후 `FOREST_FIRE_SERVICE_KEY` 입력 (사람이 직접)
- [x] `pytest -q tests/test_fetch_api.py` 통과 (가이드 예제 XML로 파서 검증)
- [x] `python -m src.fetch_api --start-year 2015 --end-year 2024` 실행 → `data/raw/` CSV 생성 (5,455건)
- [x] `src/load.py`: 원본 CSV 로더 작성
- [x] `src/preprocess.py`: 컬럼명 변환, 날짜·진화시간 파생, 시도명 표준화, 결측치 보고 → `data/processed/fires.csv`
- 💡 실습 포인트: Claude에게 `data/raw/` 파일 수정이나 인증키 하드코딩을 시켜보고 **hook이 차단**하는 것을 확인

### 2단계 — 데이터 분석  `[Skills] [Subagents]`
- [x] 연도별 발생 건수 / 피해면적 (`yearly_counts`)
- [x] 시도별 발생 건수 순위 (`region_counts`)
- [x] 월별 발생 패턴 (봄철 집중 여부 확인) (`monthly_pattern`) → 3~4월 46.1%
- [x] (선택) 원인별 비중 (`cause_share`)
- 💡 실습 포인트: `/wildfire-eda` 스킬로 정해진 절차의 EDA 실행, `data-analyst` 에이전트에게 인사이트 요약 위임

### 3단계 — 시각화  `[Skills] [Subagents]`
- [x] 연도별 추이 라인 차트 (건수 라인 + 피해면적 막대, 이중축 대신 2개 차트)
- [x] 시도별 막대 차트 (건수/피해면적 전환)
- [x] folium 지도 (시군구 중심 좌표 버블, 반지름 ∝ √건수)
- 💡 실습 포인트: `/add-chart` 스킬로 차트 추가 규칙 통일, `viz-reviewer` 에이전트로 차트 품질 리뷰

### 4단계 — 웹 대시보드  `[MCP: Playwright, Context7]`
- [x] `app.py`: 사이드바 필터(연도 범위 슬라이더, 시도 멀티셀렉트)
- [x] KPI 카드(총 건수, 총 피해면적, 최다 발생 시도, 대형 산불 100ha↑) — `analysis.kpi_summary`
- [x] 탭 구성: 추이 / 지역 / 월별 패턴(월별·시간대) / 지도
- [x] 탭별 인사이트 문구 (`src/insights.py`, data-analyst 제안 문구를 **필터 결과로 매번 다시 계산** — 고정 숫자 금지)
- 💡 실습 포인트: Context7 MCP로 최신 Streamlit 문서 조회, Playwright MCP로 실행 중인 대시보드 화면 자동 점검

### 5단계 — 배포  `[MCP: GitHub] [Skills] [Subagents]`
- [ ] `requirements.txt` 버전 고정, `.gitignore` 정리
- [ ] GitHub 저장소 생성 및 push (GitHub MCP 또는 `gh`)
- [ ] `data/processed/` 결과 파일 커밋 (배포 앱은 API를 호출하지 않음)
- [ ] Streamlit Community Cloud 연결 → (필요 시) Secrets 등록 → 공개 URL 확보
- [ ] README에 URL·스크린샷·데이터 출처 기재
- 💡 실습 포인트: `/deploy-check` 스킬로 배포 전 점검, `deploy-engineer` 에이전트에게 배포 문서 작성 위임

## 8. Claude Code 확장 기능 맵

| 기능 | 위치 | 이 프로젝트에서의 역할 |
|---|---|---|
| **CLAUDE.md** | `./CLAUDE.md` | 프로젝트 규칙·구조·단계 공유 (이 파일) |
| **Skills** | `.claude/skills/wildfire-eda/` | 산불 데이터 표준 EDA 절차 |
| | `.claude/skills/add-chart/` | 차트 추가 시 코드·테스트·대시보드 연결 규칙 |
| | `.claude/skills/deploy-check/` | 배포 전 체크리스트 자동 점검 |
| **Subagents** | `.claude/agents/data-analyst.md` | 집계 결과 해석·인사이트 도출 (읽기 전용) |
| | `.claude/agents/viz-reviewer.md` | 차트 가독성·접근성 리뷰 (읽기 전용) |
| | `.claude/agents/deploy-engineer.md` | requirements·README·배포 설정 정리 |
| **Hooks** | `.claude/settings.json` | ① `data/raw/` 수정 차단 ② 인증키 하드코딩 차단 ③ `.py` 저장 시 ruff 자동 포맷 ④ 위험한 git 명령·`.env` 열람 차단 ⑤ 세션 시작 시 진행 상황 안내 |
| **MCP** | `.mcp.json` | GitHub(저장소·이슈), Playwright(대시보드 화면 점검), Context7(라이브러리 최신 문서) |

## 9. Claude에게 요청하는 작업 방식

- 새 단계를 시작할 때는 먼저 **계획을 짧게 제시**하고 진행한다.
- 실습생이 이해할 수 있도록, 코드 작성 후 **무엇을 왜 했는지 3줄 이내로** 설명한다.
- 실제 데이터 파일을 열어보기 전에는 컬럼명·값을 추측해서 코드를 확정하지 않는다.
- 한 단계가 끝나면 §7 체크리스트를 갱신하고 커밋 메시지를 제안한다. (예: `feat(step2): 연도별/월별 집계 함수 추가`)
