"""원본(data/raw)·전처리(data/processed) 데이터를 읽는다."""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_PATH = DATA_DIR / "processed" / "fires.csv"
CENTROIDS_PATH = DATA_DIR / "reference" / "sigungu_centroids.csv"

ENCODINGS = ("utf-8-sig", "cp949")


def read_csv_auto(path: Path, **kwargs) -> pd.DataFrame:
    """utf-8-sig → cp949 순서로 인코딩을 시도해 CSV를 읽는다."""
    for enc in ENCODINGS:
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"{path}: {ENCODINGS} 인코딩으로 읽을 수 없습니다.")


def latest_raw_file() -> Path:
    """data/raw/ 의 fire_stats_*.csv 중 가장 최근 파일 경로를 반환한다."""
    files = sorted(RAW_DIR.glob("fire_stats_*.csv"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(
            "data/raw/fire_stats_*.csv 가 없습니다. "
            "python -m src.fetch_api --start-year 2015 --end-year 2024 를 먼저 실행하세요."
        )
    return files[-1]


def load_raw(path: Path | None = None) -> pd.DataFrame:
    """API 수집 원본을 모든 컬럼 문자열로 읽는다 (앞자리 0 보존)."""
    return read_csv_auto(path or latest_raw_file(), dtype=str)


def load_processed(path: Path = PROCESSED_PATH) -> pd.DataFrame:
    """전처리 결과를 날짜 컬럼 타입을 살려 읽는다."""
    if not path.exists():
        raise FileNotFoundError(
            f"{path} 가 없습니다. python -m src.preprocess 를 먼저 실행하세요."
        )
    return read_csv_auto(path, parse_dates=["start_at", "end_at"])


def load_centroids(path: Path = CENTROIDS_PATH) -> pd.DataFrame:
    """시군구 중심 좌표(통계청 2013 경계 기준)를 읽는다."""
    if not path.exists():
        raise FileNotFoundError(
            f"{path} 가 없습니다. python -m src.build_centroids 를 먼저 실행하세요."
        )
    return read_csv_auto(path)
