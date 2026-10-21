"""전처리된 산불 데이터(data/processed/fires.csv)의 집계 함수."""

import pandas as pd


def yearly_counts(df: pd.DataFrame, years: range | None = None) -> pd.DataFrame:
    """연도별 발생 건수와 피해면적 합계를 반환한다 (발생 없는 연도는 0).

    years 를 주면 그 범위 전체를 채운다 (필터 결과의 양끝 연도에 발생이 없어도 축 유지).
    """
    if years is None:
        years = range(int(df["year"].min()), int(df["year"].max()) + 1)
    out = (
        df.groupby("year")
        .agg(count=("year", "size"), damage_area_ha=("damage_area_ha", "sum"))
        .reindex(years, fill_value=0)
        .rename_axis("year")
        .reset_index()
    )
    return out


def region_counts(df: pd.DataFrame, by: str = "sido") -> pd.DataFrame:
    """지역(by: sido 또는 sigungu)별 발생 건수·피해면적·건수 비중(%)을 건수 내림차순으로 반환한다."""
    out = (
        df.assign(**{by: df[by].fillna("(미상)")})
        .groupby(by)
        .agg(count=(by, "size"), damage_area_ha=("damage_area_ha", "sum"))
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


# 2023년 경북→대구 편입. 좌표는 2013 경계 기준이라 옛 소속으로 찾는다.
SIGUNGU_ALIAS = {("대구", "군위"): ("경북", "군위")}


def _locate(sido: str, sigungu: str, known: set) -> tuple | None:
    """(시도, 시군구)를 좌표표의 키로 찾는다: 정확히 → 별칭 → 일반구의 상위 시."""
    for key in (
        (sido, sigungu),
        SIGUNGU_ALIAS.get((sido, sigungu)),
        (sido, sigungu.split()[0]),
    ):
        if key in known:
            return key
    return None


def region_points(df: pd.DataFrame, centroids: pd.DataFrame) -> pd.DataFrame:
    """시군구별 발생 건수·피해면적에 중심 좌표(lat, lon)를 붙인다.

    좌표를 찾지 못한 행과 시군구 결측 행은 제외되므로, 호출 측에서 건수 차이를 표시한다.
    """
    d = df.copy()
    # 세종은 시군구가 없어 읍면 이름이 들어오거나 비어 있다 → 결측 제거 전에 세종으로 통일
    d.loc[d["sido"] == "세종", "sigungu"] = "세종"
    d = d.dropna(subset=["sigungu"])
    agg = (
        d.groupby(["sido", "sigungu"])
        .agg(count=("sido", "size"), damage_area_ha=("damage_area_ha", "sum"))
        .reset_index()
    )
    known = set(zip(centroids["sido"], centroids["sigungu"]))
    keys = [_locate(s, g, known) for s, g in zip(agg["sido"], agg["sigungu"])]
    agg["sido"] = [k[0] if k else None for k in keys]
    agg["sigungu"] = [k[1] if k else None for k in keys]

    # 일반구가 상위 시로 대체되면 같은 좌표로 합쳐진다 (예: 청주 서원·청원 → 청주)
    out = (
        agg.dropna(subset=["sido"])
        .groupby(["sido", "sigungu"], as_index=False)
        .agg(count=("count", "sum"), damage_area_ha=("damage_area_ha", "sum"))
        .merge(centroids[["sido", "sigungu", "lat", "lon"]], on=["sido", "sigungu"])
    )
    out["region"] = out["sido"].where(
        out["sido"] == out["sigungu"], out["sido"] + " " + out["sigungu"]
    )
    return out.sort_values("count", ascending=False).reset_index(drop=True)[
        ["region", "sido", "sigungu", "lat", "lon", "count", "damage_area_ha"]
    ]
