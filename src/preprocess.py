"""API 원본을 분석용 데이터로 정제해 data/processed/fires.csv 로 저장한다.

사용법:
    python -m src.preprocess
"""

import pandas as pd

from src.load import PROCESSED_PATH, load_raw

# API 응답 필드 → 분석용 컬럼 (CLAUDE.md §4-3)
COLUMN_MAP = {
    "startdayofweek": "weekday",
    "locsi": "sido",
    "locgungu": "sigungu",
    "locmenu": "eupmyeon",  # 오타 아님: API의 '읍면' 필드명
    "locdong": "dongri",
    "locbunji": "bunji",
    "firecause": "cause",
    "damagearea": "damage_area_ha",
}

# 긴 이름·개편 전후 이름을 API가 쓰는 짧은 이름으로 통일
SIDO_NORMALIZE = {
    "서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구", "인천광역시": "인천",
    "광주광역시": "광주", "대전광역시": "대전", "울산광역시": "울산", "세종특별자치시": "세종",
    "경기도": "경기", "강원도": "강원", "강원특별자치도": "강원",
    "충청북도": "충북", "충청남도": "충남",
    "전라북도": "전북", "전북특별자치도": "전북", "전라남도": "전남",
    "경상북도": "경북", "경상남도": "경남", "제주도": "제주", "제주특별자치도": "제주",
}  # fmt: skip

MAX_DURATION_MIN = 30 * 24 * 60  # 30일 초과 진화시간은 입력 오류로 본다

OUTPUT_COLUMNS = [
    "year", "month", "day", "weekday", "start_at", "end_at", "duration_min",
    "sido", "sigungu", "region", "eupmyeon", "dongri", "bunji", "cause", "damage_area_ha",
]  # fmt: skip


def _to_datetime(df: pd.DataFrame, prefix: str) -> pd.Series:
    """{prefix}year/month/day/time 4개 컬럼을 하나의 datetime으로 합친다."""
    text = (
        df[f"{prefix}year"].str.strip()
        + df[f"{prefix}month"].str.strip().str.zfill(2)
        + df[f"{prefix}day"].str.strip().str.zfill(2)
        + " "
        + df[f"{prefix}time"].str.strip()
    )
    return pd.to_datetime(text, format="%Y%m%d %H:%M:%S", errors="coerce")


def preprocess(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """원본 DataFrame을 정제하고 (결과, 처리 보고서)를 반환한다."""
    report: dict = {"원본 행 수": len(raw)}
    df = raw.copy()

    df["start_at"] = _to_datetime(df, "start")
    df["end_at"] = _to_datetime(df, "end")
    report["발생일시 변환 실패(삭제)"] = int(df["start_at"].isna().sum())
    df = df.dropna(subset=["start_at"])

    df["year"] = df["start_at"].dt.year
    df["month"] = df["start_at"].dt.month
    df["day"] = df["start_at"].dt.day

    duration = (df["end_at"] - df["start_at"]).dt.total_seconds() / 60
    invalid = (duration < 0) | (duration > MAX_DURATION_MIN)
    report["진화시간 이상(음수·30일 초과 → 결측)"] = int(invalid.sum())
    df["duration_min"] = duration.mask(invalid)

    df = df.rename(columns=COLUMN_MAP)
    text_cols = ["weekday", "sido", "sigungu", "eupmyeon", "dongri", "bunji", "cause"]
    df[text_cols] = df[text_cols].apply(lambda s: s.str.strip())
    df["sido"] = df["sido"].replace(SIDO_NORMALIZE)
    # '광주'처럼 시도·시군구 이름이 겹치므로 지역 키는 시도와 함께 만든다
    df["region"] = (df["sido"] + " " + df["sigungu"].fillna("")).str.strip()

    df["damage_area_ha"] = pd.to_numeric(df["damage_area_ha"], errors="coerce")
    report["피해면적 숫자 변환 실패(결측)"] = int(df["damage_area_ha"].isna().sum())

    out = df[OUTPUT_COLUMNS].sort_values("start_at").reset_index(drop=True)
    report["결측 개수"] = {k: int(v) for k, v in out.isna().sum().items() if v > 0}
    report["최종 행 수"] = len(out)
    return out, report


def main() -> None:
    df, report = preprocess(load_raw())
    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_PATH, index=False, encoding="utf-8-sig")
    for key, value in report.items():
        print(f"- {key}: {value}")
    print(f"저장 완료: {PROCESSED_PATH}")


if __name__ == "__main__":
    main()
