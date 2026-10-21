import pandas as pd
import pytest

from src.analysis import cause_share, monthly_pattern, region_counts, yearly_counts


@pytest.fixture
def df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "year": [2020, 2020, 2020, 2022],
            "month": [3, 3, 4, 3],
            "sido": ["경북", "강원", "경북", "경북"],
            "cause": ["기타", "입산자실화", "기타", "기타"],
            "damage_area_ha": [1.0, 2.0, 10.0, 0.5],
        }
    )


def test_yearly_counts_fills_missing_year(df):
    out = yearly_counts(df).set_index("year")
    assert out.loc[2020, "count"] == 3
    assert out.loc[2020, "damage_area_ha"] == 13.0
    assert out.loc[2021, "count"] == 0  # 발생 없는 연도도 포함


def test_region_counts_sorted(df):
    out = region_counts(df)
    assert out["count"].is_monotonic_decreasing
    assert list(out["sido"]) == ["경북", "강원"]
    assert out.set_index("sido").loc["경북", "damage_area_ha"] == 11.5
    assert out["share_pct"].sum() == pytest.approx(100)


def test_monthly_pattern_averages_over_all_years(df):
    out = monthly_pattern(df).set_index("month")
    assert len(out) == 12
    # 3월: 2020년 2건, 2021년 0건, 2022년 1건 → 평균 1.0
    assert out.loc[3, "avg_count"] == pytest.approx(1.0)
    assert out.loc[1, "avg_count"] == 0
    assert out["share_pct"].sum() == pytest.approx(100)


def test_cause_share(df):
    out = cause_share(df)
    assert out.iloc[0]["cause"] == "기타"
    assert out.iloc[0]["share_pct"] == pytest.approx(75)


def test_yearly_counts_keeps_given_range(df):
    out = yearly_counts(df, range(2018, 2025))
    assert list(out["year"]) == list(range(2018, 2025))
    assert out.set_index("year").loc[2024, "count"] == 0


def test_region_counts_by_sigungu_fills_missing():
    df = pd.DataFrame(
        {"sigungu": ["제주", None, "제주"], "damage_area_ha": [1.0, 2.0, 3.0]}
    )
    out = region_counts(df, by="sigungu").set_index("sigungu")
    assert out.loc["제주", "count"] == 2
    assert out.loc["(미상)", "count"] == 1
