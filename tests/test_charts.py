import folium
import pandas as pd
import plotly.graph_objects as go
import pytest

from src.analysis import region_points
from src.build_centroids import build_centroids, short_name
from src.charts import (
    region_map,
    sido_bar_chart,
    yearly_count_chart,
    yearly_damage_chart,
)

YEARLY = pd.DataFrame(
    {
        "year": [2020, 2021, 2022],
        "count": [10, 5, 8],
        "damage_area_ha": [1.0, 50.0, 2.0],
    }
)
REGION = pd.DataFrame(
    {
        "sido": ["경북", "경기", "강원"],
        "count": [3, 9, 5],
        "damage_area_ha": [90.0, 1.0, 40.0],
    }
)


def test_yearly_charts():
    fig = yearly_count_chart(YEARLY)
    assert isinstance(fig, go.Figure) and len(fig.data) == 1
    fig = yearly_damage_chart(YEARLY)
    assert list(fig.data[0].text) == ["", "50ha", ""]  # 최대 연도만 라벨


def test_sido_bar_sorted_desc():
    fig = sido_bar_chart(REGION)
    assert fig.data[0].orientation == "h"
    assert list(fig.data[0].y) == ["경기", "강원", "경북"]
    fig = sido_bar_chart(REGION, metric="damage_area_ha")
    assert list(fig.data[0].y) == ["경북", "강원", "경기"]


def test_short_name():
    assert short_name("고양시덕양구") == ("고양 덕양", "고양")
    assert short_name("양평군") == ("양평", "양평")
    assert short_name("북구") == ("북", "북")


def test_build_centroids_square():
    square = [
        [[127.0, 36.0], [128.0, 36.0], [128.0, 37.0], [127.0, 37.0], [127.0, 36.0]]
    ]
    geo = {
        "features": [
            {
                "properties": {"code": "31380", "name": "양평군"},
                "geometry": {"type": "Polygon", "coordinates": square},
            }
        ]
    }
    row = build_centroids(geo).iloc[0]
    assert (row.sido, row.sigungu) == ("경기", "양평")
    assert (round(row.lat, 6), round(row.lon, 6)) == (36.5, 127.5)


def test_region_points_fallbacks():
    centroids = pd.DataFrame(
        {
            "sido": ["경기", "충북", "세종", "경북"],
            "sigungu": ["양평", "청주", "세종", "군위"],
            "lat": [37.5, 36.6, 36.5, 36.2],
            "lon": [127.5, 127.5, 127.3, 128.7],
        }
    )
    df = pd.DataFrame(
        {
            "sido": ["경기", "충북", "충북", "세종", "대구", "경기"],
            "sigungu": ["양평", "청주 서원", "청주 청원", "금남", "군위", None],
            "damage_area_ha": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        }
    )
    p = region_points(df, centroids).set_index("region")
    assert p.loc["충북 청주", "count"] == 2  # 2013 경계에 없는 일반구 → 상위 시
    assert p.loc["세종", "count"] == 1  # 세종 읍면 → 세종
    assert p.loc["경북 군위", "count"] == 1  # 대구 군위 → 2013 경북 군위
    assert p["count"].sum() == 5  # 시군구 결측 1건 제외


def test_region_map_returns_folium():
    points = pd.DataFrame(
        {
            "region": ["경기 양평"],
            "lat": [37.5],
            "lon": [127.5],
            "count": [4],
            "damage_area_ha": [1.0],
        }
    )
    assert isinstance(region_map(points), folium.Map)
    assert isinstance(region_map(points.iloc[0:0]), folium.Map)


def test_sido_bar_hover_per_bar():
    assert sido_bar_chart(REGION).layout.hovermode == "closest"


def test_region_points_sejong_missing_sigungu():
    centroids = pd.DataFrame(
        {"sido": ["세종"], "sigungu": ["세종"], "lat": [36.5], "lon": [127.3]}
    )
    df = pd.DataFrame(
        {
            "sido": ["세종", "세종"],
            "sigungu": [None, "금남"],
            "damage_area_ha": [1.0, 2.0],
        }
    )
    assert region_points(df, centroids).loc[0, "count"] == 2  # 결측도 세종에 표시


def test_small_counts_use_integer_ticks():
    small = YEARLY.assign(count=[2, 0, 1])
    yaxis = yearly_count_chart(small).layout.yaxis
    assert (yaxis.dtick, yaxis.tickformat) == (1, ",d")
    xaxis = sido_bar_chart(REGION).layout.xaxis
    assert xaxis.dtick == 1
    assert (
        sido_bar_chart(REGION, metric="damage_area_ha").layout.xaxis.tickformat
        == ",.0f"
    )


def test_damage_chart_all_zero():
    fig = yearly_damage_chart(YEARLY.assign(damage_area_ha=0.0))
    assert set(fig.data[0].text) == {""}
    assert fig.layout.yaxis.range is None


def test_sido_bar_by_sigungu_title():
    data = pd.DataFrame(
        {"sigungu": ["제주", "서귀포"], "count": [2, 1], "damage_area_ha": [1.0, 2.0]}
    )
    fig = sido_bar_chart(data, by="sigungu", title="제주 시군구별")
    assert list(fig.data[0].y) == ["제주", "서귀포"]
    assert fig.layout.title.text == "제주 시군구별 산불 발생 건수"


def test_region_map_zooms_to_points():
    one = pd.DataFrame(
        {
            "region": ["제주"],
            "lat": [33.4],
            "lon": [126.5],
            "count": [3],
            "damage_area_ha": [1.0],
        }
    )
    assert region_map(one).location == [33.4, 126.5]


def test_region_map_view_fits_points():
    two = pd.DataFrame(
        {
            "region": ["제주", "제주 서귀포"],
            "lat": [33.45, 33.30],
            "lon": [126.55, 126.60],
            "count": [1, 2],
            "damage_area_ha": [0.1, 0.2],
        }
    )
    m = region_map(two)
    assert m.location == pytest.approx([33.375, 126.575])
    assert m.options["zoom"] == 10  # 가까운 두 곳 → 최대 줌 10에서 멈춤
    nation = two.assign(lat=[33.3, 38.3], lon=[126.2, 130.8])
    assert region_map(nation).options["zoom"] == 6
