"""전처리된 산불 데이터(data/processed/fires.csv)의 집계 함수."""

import pandas as pd


def yearly_counts(df: pd.DataFrame) -> pd.DataFrame:
    """연도별 발생 건수와 피해면적 합계를 반환한다 (발생 없는 연도는 0)."""
    years = range(int(df["year"].min()), int(df["year"].max()) + 1)
    out = (
        df.groupby("year")
        .agg(count=("year", "size"), damage_area_ha=("damage_area_ha", "sum"))
        .reindex(years, fill_value=0)
        .rename_axis("year")
        .reset_index()
    )
    return out


def region_counts(df: pd.DataFrame) -> pd.DataFrame:
    """시도별 발생 건수·피해면적·건수 비중(%)을 건수 내림차순으로 반환한다."""
    out = (
        df.groupby("sido")
        .agg(count=("sido", "size"), damage_area_ha=("damage_area_ha", "sum"))
        .sort_values("count", ascending=False)
        .reset_index()
    )
    out["share_pct"] = out["count"] / out["count"].sum() * 100
    return out


def monthly_pattern(df: pd.DataFrame) -> pd.DataFrame:
    """월별 연평균 발생 건수와 전체 대비 비중(%)을 반환한다."""
    years = range(int(df["year"].min()), int(df["year"].max()) + 1)
    grid = pd.MultiIndex.from_product([years, range(1, 13)], names=["year", "month"])
    per_year = df.groupby(["year", "month"]).size().reindex(grid, fill_value=0)
    out = per_year.groupby("month").mean().rename("avg_count").reset_index()
    out["share_pct"] = out["avg_count"] / out["avg_count"].sum() * 100
    return out


def cause_share(df: pd.DataFrame) -> pd.DataFrame:
    """발생원인별 건수와 비중(%)을 건수 내림차순으로 반환한다."""
    out = df["cause"].value_counts().rename_axis("cause").reset_index(name="count")
    out["share_pct"] = out["count"] / out["count"].sum() * 100
    return out
