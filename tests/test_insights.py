import pandas as pd
import pytest

from src.analysis import hourly_pattern, kpi_summary, monthly_pattern
from src.charts import PRIMARY, SECONDARY, hourly_chart, monthly_chart
from src.insights import (
    _iga,
    hourly_insight,
    map_insight,
    monthly_insight,
    region_insight,
    trend_insight,
)


@pytest.fixture
def df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "year": [2020, 2020, 2021, 2021],
            "month": [3, 4, 3, 8],
            "start_at": pd.to_datetime(
                [
                    "2020-03-01 14:00",
                    "2020-04-01 13:10",
                    "2021-03-02 14:30",
                    "2021-08-01 02:00",
                ]
            ),
            "sido": ["경기", "경기", "경북", "경북"],
            "sigungu": ["양평", "가평", "울진", "울진"],
            "damage_area_ha": [1.0, 2.0, 300.0, 0.5],
            "duration_min": [60.0, 120.0, 600.0, None],
        }
    )


def test_hourly_pattern(df):
    out = hourly_pattern(df).set_index("hour")
    assert len(out) == 24
    assert out.loc[14, "count"] == 2
    assert out["share_pct"].sum() == pytest.approx(100)


def test_kpi_summary(df):
    k = kpi_summary(df)
    assert k["count"] == 4
    assert k["damage_area_ha"] == pytest.approx(303.5)
    assert k["top_damage_sido"] == "경북"
    assert k["median_duration_min"] == 120  # 결측 제외
    assert k["large_count"] == 1
    assert k["large_area_share_pct"] == pytest.approx(300 / 303.5 * 100)


def test_iga():
    assert _iga("경기") == "경기가"
    assert _iga("경북") == "경북이"
    assert _iga("울진") == "울진이"


def test_insights_text(df):
    assert trend_insight(df, range(2020, 2022)).startswith(
        "2021년 한 해 피해면적 300ha"
    )
    assert region_insight(df) == "건수 1위 경기(2건), 피해면적 1위 경북(300ha)"
    assert monthly_insight(df, range(2020, 2022)).startswith(
        "3~4월에 전체 산불의 75.0%"
    )
    assert hourly_insight(df) == "산불 75%는 11~16시에 시작, 14시가 피크(50.0%)"
    assert map_insight(df) == "100ha 이상 1건이 전체 피해면적의 98.8%"


def test_region_insight_single_sido_uses_sigungu(df):
    one = df[df["sido"] == "경북"]
    assert region_insight(one) == "울진이 건수(2건)와 피해면적(300ha) 모두 1위"


def test_insights_without_damage_or_large_fires(df):
    calm = df.assign(damage_area_ha=0.0)
    assert (
        trend_insight(calm, range(2020, 2022))
        == "선택한 기간에 기록된 피해면적이 없습니다."
    )
    assert map_insight(calm) == "100ha 이상 대형 산불은 없습니다"


def test_pattern_charts_highlight(df):
    m = monthly_chart(monthly_pattern(df, range(2020, 2022)))
    colors = list(m.data[0].marker.color)
    assert colors[2] == colors[3] == PRIMARY and colors[0] == SECONDARY  # 3·4월 강조
    h = hourly_chart(hourly_pattern(df))
    assert (
        h.data[0].marker.color[14] == PRIMARY and h.data[0].marker.color[2] == SECONDARY
    )
