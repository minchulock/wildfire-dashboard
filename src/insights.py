"""대시보드 탭별 한 줄 인사이트 문구 (data-analyst 제안 문구를 필터 결과로 다시 계산).

문구 속 숫자는 모두 입력 df(필터 적용 결과)에서 계산한다. 고정 숫자를 쓰지 않는다.
"""

import pandas as pd

from src.analysis import (
    LARGE_FIRE_HA,
    hourly_pattern,
    kpi_summary,
    monthly_pattern,
    region_counts,
    yearly_counts,
)

PEAK_HOURS = range(11, 17)  # 11~16시


def _iga(word: str) -> str:
    """주격 조사: 받침이 있으면 '이', 없으면 '가' (경북이 / 경기가)."""
    code = ord(word[-1]) - 0xAC00
    return word + ("이" if 0 <= code <= 11171 and code % 28 else "가")


def trend_insight(df: pd.DataFrame, years: range) -> str:
    """[추이] 피해면적이 가장 컸던 연도와 그 해 건수."""
    yearly = yearly_counts(df, years).set_index("year")
    if yearly["damage_area_ha"].max() <= 0:
        return "선택한 기간에 기록된 피해면적이 없습니다."
    peak = yearly["damage_area_ha"].idxmax()
    row = yearly.loc[peak]
    share = row["damage_area_ha"] / yearly["damage_area_ha"].sum() * 100
    return (
        f"{peak}년 한 해 피해면적 {row['damage_area_ha']:,.0f}ha(기간 전체의 {share:.0f}%), "
        f"건수는 {int(row['count']):,}건"
    )


def region_insight(df: pd.DataFrame) -> str:
    """[지역] 건수 1위와 피해면적 1위 지역 (시도 1개면 시군구 기준, 다르면 대비)."""
    by = "sigungu" if df["sido"].nunique() == 1 else "sido"
    counts = region_counts(df, by=by)
    top_count = counts.iloc[0]
    top_area = counts.sort_values("damage_area_ha", ascending=False).iloc[0]
    if top_count[by] == top_area[by]:
        return (
            f"{_iga(top_count[by])} 건수({top_count['count']:,}건)와 "
            f"피해면적({top_area['damage_area_ha']:,.0f}ha) 모두 1위"
        )
    return (
        f"건수 1위 {top_count[by]}({top_count['count']:,}건), "
        f"피해면적 1위 {top_area[by]}({top_area['damage_area_ha']:,.0f}ha)"
    )


def monthly_insight(df: pd.DataFrame, years: range) -> str:
    """[월별 패턴] 3~4월 집중도와 2~5월 합계."""
    m = monthly_pattern(df, years).set_index("month")["share_pct"]
    return (
        f"3~4월에 전체 산불의 {m.loc[[3, 4]].sum():.1f}%가 집중됩니다 "
        f"(2~5월 합계 {m.loc[[2, 3, 4, 5]].sum():.1f}%)"
    )


def hourly_insight(df: pd.DataFrame) -> str:
    """[월별 패턴] 낮 시간대 집중도와 피크 시각."""
    h = hourly_pattern(df).set_index("hour")
    peak = int(h["count"].idxmax())
    return (
        f"산불 {h.loc[PEAK_HOURS, 'share_pct'].sum():.0f}%는 11~16시에 시작, "
        f"{peak}시가 피크({h.loc[peak, 'share_pct']:.1f}%)"
    )


def map_insight(df: pd.DataFrame) -> str:
    """[지도] 대형 산불이 피해면적에서 차지하는 비중."""
    k = kpi_summary(df)
    if k["large_count"] == 0:
        return f"{LARGE_FIRE_HA}ha 이상 대형 산불은 없습니다"
    return (
        f"{LARGE_FIRE_HA}ha 이상 {k['large_count']:,}건이 "
        f"전체 피해면적의 {k['large_area_share_pct']:.1f}%"
    )
