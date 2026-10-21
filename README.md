# 산불 발생 현황 분석 및 시각화 대시보드

산림청 산불통계 OpenAPI로 2015~2024년 산불 발생 5,455건을 수집·전처리·분석하고, Streamlit 대시보드로 시각화한 프로젝트입니다.
연도별 추이, 시도별 순위, 월별·시간대 패턴, 시군구 지도를 한 화면에서 확인할 수 있습니다.

이 프로젝트는 **바이브 코딩 실습용**으로, Claude Code의 `CLAUDE.md`(프로젝트 메모리), skills, agents(서브에이전트), hooks, MCP를 활용해 단계별(수집 → 분석 → 시각화 → 대시보드 → 배포)로 만들었습니다.

> 배포 URL: https://wildfire-dashboard-h67fydbx2pc6qchpdja3fl.streamlit.app

<!-- 스크린샷을 docs/screenshot.png 에 추가한 뒤 아래 줄의 주석을 풀어 주세요.
![대시보드 스크린샷](docs/screenshot.png)
-->

## 주요 기능

- KPI 카드: 총 건수, 총 피해면적, 최다 발생 시도, 대형 산불(100ha 이상)
- 탭 4개: 추이 / 지역 / 월별 패턴 / 지도
- 사이드바 필터: 연도 범위, 시도
- 탭별 인사이트 문구: 필터 결과로 매번 새로 계산 (고정 숫자 없음)

## 로컬 실행

데이터(`data/processed/`)가 저장소에 포함되어 있어 **API 키 없이** 실행됩니다.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py               # http://localhost:8501
```

개발용(테스트·린트) 도구까지 설치하려면 `pip install -r requirements-dev.txt`, 테스트는 `pytest -q` 입니다.

## 데이터 다시 수집 (선택)

공공데이터포털에서 활용신청 후 발급받은 인증키가 필요합니다. 키는 환경설정 파일(`.env`)에만 입력하고 커밋하지 마세요.

```bash
cp .env.example .env               # 복사한 파일에 FOREST_FIRE_SERVICE_KEY 입력
python -m src.fetch_api --start-year 2015 --end-year 2024   # data/raw/ 에 원본 CSV 저장
python -m src.preprocess                                    # data/processed/fires.csv 생성
python -m src.build_centroids                               # (선택) 시군구 중심 좌표 재생성
```

## 프로젝트 구조

```
.
├── app.py                 # Streamlit 진입점
├── src/
│   ├── config.py          # 환경변수(.env / Streamlit secrets) 로딩
│   ├── fetch_api.py       # OpenAPI 호출 -> data/raw/
│   ├── load.py            # 데이터 로딩
│   ├── preprocess.py      # 정제·파생 컬럼
│   ├── analysis.py        # 집계 함수
│   ├── insights.py        # 탭별 인사이트 문구
│   ├── build_centroids.py # 경계 GeoJSON -> 시군구 중심 좌표
│   └── charts.py          # plotly / folium 차트
├── data/
│   ├── raw/               # API 수집 원본 (수정 금지)
│   ├── processed/         # 전처리 결과
│   └── reference/         # 시군구 경계·중심 좌표
├── tests/                 # pytest
├── CLAUDE.md              # Claude Code 프로젝트 메모리
├── requirements.txt       # 실행용 의존성 (버전 고정)
└── requirements-dev.txt   # 개발용 의존성
```

## 데이터 출처 및 라이선스

- **산불 통계**: 산림청 「산불통계 정보」 OpenAPI (공공데이터포털 data.go.kr, 「산림청_산불발생통계(대국민포털)」).
  이 데이터는 공공누리(KOGL) 이용허락 조건에 따라 이용합니다. 정확한 이용허락범위(공공누리 유형)는
  공공데이터포털의 해당 데이터 페이지에 표시된 내용을 따릅니다.
- **시군구 경계**: 통계청(KOSTAT) 2013 행정구역 경계를 [southkorea-maps](https://github.com/southkorea/southkorea-maps)를 통해 사용했습니다 (`data/reference/`).
  - 한계: 2013년 이후 행정구역 개편(청주 청원·서원구 신설, 2023년 군위군의 대구 편입 등)은 반영되지 않아, 해당 지역은 상위 시 또는 옛 소속으로 표시됩니다.

## 데이터 처리 메모

- 진화시간이 음수이거나 30일을 초과하는 27건은 진화시간만 결측 처리했습니다 (행은 삭제하지 않음).
- 시군구가 결측인 11건은 지도에서 제외됩니다.
- 자세한 전처리 규칙은 `CLAUDE.md` §4-3을 참고하세요.

## 배포 (Streamlit Community Cloud)

1. 이 프로젝트를 GitHub 저장소에 push 합니다 (`data/processed/`, `data/reference/` 포함).
2. [share.streamlit.io](https://share.streamlit.io)에 GitHub 계정으로 로그인하고 **Create app**을 누릅니다.
3. 저장소를 선택하고 브랜치는 `main`, Main file path는 `app.py`로 지정합니다.
4. **Advanced settings**에서 Python 버전을 선택합니다 (로컬은 3.14, 고정한 패키지가 지원하는 버전을 선택).
5. **Deploy**를 누르고, 발급된 URL을 이 README의 `배포 URL`에 기재합니다.

Secrets는 필요 없습니다. 배포된 앱은 API를 호출하지 않고 저장소에 포함된 데이터 파일만 읽습니다.
