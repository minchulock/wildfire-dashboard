"""src/analysis.py 집계 결과를 받아 plotly/folium 차트를 만든다 (차트 함수 안에서 집계하지 않음)."""

import math

import folium
import pandas as pd
import plotly.graph_objects as go

PRIMARY = "#D9480F"
SECONDARY = "#868E96"
TEMPLATE = "plotly_white"
MAP_CENTER = [36.5, 127.8]


def _layout(
    fig: go.Figure, title: str, x_title: str, y_title: str, hovermode: str = "x unified"
) -> go.Figure:
    fig.update_layout(
        title=title,
        template=TEMPLATE,
        xaxis_title=x_title,
        yaxis_title=y_title,
        showlegend=False,  # 단일 시리즈: 제목이 시리즈 이름을 대신한다
        hovermode=hovermode,
        margin={"l": 10, "r": 10, "t": 60, "b": 10},
    )
    return fig


def _count_axis(max_value: float) -> dict:
    """건수 축은 정수 눈금만 쓴다 (값이 작을 때 0.5 눈금이 '1, 1'로 반복되는 것 방지)."""
    axis = {"tickformat": ",d", "rangemode": "tozero"}
    if max_value < 10:
        axis["dtick"] = 1
    return axis


def yearly_count_chart(yearly: pd.DataFrame) -> go.Figure:
    """연도별 발생 건수 라인 차트 (입력: yearly_counts 결과)."""
    fig = go.Figure(
        go.Scatter(
            x=yearly["year"],
            y=yearly["count"],
            mode="lines+markers",
            line={"color": PRIMARY, "width": 2},
            marker={"size": 8},
            hovertemplate="%{x}년: %{y:,}건<extra></extra>",
        )
    )
    fig.update_xaxes(dtick=1)
    fig.update_yaxes(**_count_axis(yearly["count"].max()))
    return _layout(fig, "연도별 산불 발생 건수", "연도", "발생 건수(건)")


def yearly_damage_chart(yearly: pd.DataFrame) -> go.Figure:
    """연도별 피해면적 막대 차트, 최대 연도만 값 표시 (입력: yearly_counts 결과)."""
    top = yearly["damage_area_ha"].max()
    peak = yearly["damage_area_ha"].idxmax() if top > 0 else None
    labels = [
        f"{v:,.0f}ha" if i == peak else "" for i, v in yearly["damage_area_ha"].items()
    ]
    fig = go.Figure(
        go.Bar(
            x=yearly["year"],
            y=yearly["damage_area_ha"],
            marker_color=PRIMARY,
            text=labels,
            textposition="outside",
            hovertemplate="%{x}년: %{y:,.1f}ha<extra></extra>",
        )
    )
    fig.update_traces(cliponaxis=False, textfont_size=12, constraintext="none")
    fig.update_xaxes(dtick=1)
    # 최대값 라벨이 잘려 작게 줄어들지 않도록 위쪽 여백 확보 (전부 0이면 자동 범위)
    fig.update_yaxes(tickformat=",.0f", range=[0, top * 1.15] if top > 0 else None)
    return _layout(fig, "연도별 산불 피해면적", "연도", "피해면적(ha)")


SIDO_METRICS = {
    "count": ("발생 건수", "건"),
    "damage_area_ha": ("피해면적", "ha"),
}


def sido_bar_chart(
    region: pd.DataFrame, metric: str = "count", by: str = "sido", title: str = "시도별"
) -> go.Figure:
    """지역별 가로 막대 차트, 값 내림차순 (입력: region_counts 결과, by 는 같은 컬럼)."""
    name, unit = SIDO_METRICS[metric]
    data = region.sort_values(metric, ascending=False)
    fig = go.Figure(
        go.Bar(
            x=data[metric],
            y=data[by],
            orientation="h",
            marker_color=PRIMARY,
            customdata=data[["count", "damage_area_ha"]],
            hovertemplate=(
                "%{y}<br>발생 %{customdata[0]:,}건 · 피해면적 %{customdata[1]:,.1f}ha"
                "<extra></extra>"
            ),
        )
    )
    fig.update_yaxes(autorange="reversed")  # 1위가 맨 위
    if metric == "count":
        fig.update_xaxes(**_count_axis(data[metric].max()))
    else:
        fig.update_xaxes(tickformat=",.0f")  # 소수 1자리는 hover 에만
    fig.update_layout(height=max(360, 28 * len(data)))
    return _layout(
        fig, f"{title} 산불 {name}", f"{name}({unit})", "", hovermode="closest"
    )


def _view(points: pd.DataFrame) -> tuple[list[float], int]:
    """버블이 모두 보이는 지도 중심과 줌을 계산한다 (예: 제주만 선택해도 제주로 이동).

    folium fit_bounds 는 브라우저에서 지도 크기로 계산하는데, Streamlit 탭이 숨겨진 채
    그려지면 크기가 0이라 최대로 확대된다. 그래서 파이썬에서 직접 계산한다.
    """
    lat_min, lat_max = points["lat"].min(), points["lat"].max()
    lon_min, lon_max = points["lon"].min(), points["lon"].max()
    center = [(lat_min + lat_max) / 2, (lon_min + lon_max) / 2]
    span = max(lat_max - lat_min, lon_max - lon_min, 0.01)
    # 줌 n 에서 지도 높이 600px 은 약 360/2^n 도. 전국(약 5도) → 7, 최대 10
    zoom = min(10, max(6, int(math.log2(360 / span))))
    return center, zoom


def region_map(points: pd.DataFrame, max_radius: int = 14) -> folium.Map:
    """시군구 중심 좌표에 발생 건수 버블을 그린 지도 (입력: region_points 결과).

    버블 반지름은 건수의 제곱근에 비례한다 (면적이 건수에 비례).
    """
    if points.empty:
        return folium.Map(location=MAP_CENTER, zoom_start=7, tiles="OpenStreetMap")
    center, zoom = _view(points)
    m = folium.Map(location=center, zoom_start=zoom, tiles="OpenStreetMap")
    scale = max_radius / math.sqrt(points["count"].max())
    for row in points.sort_values("count", ascending=False).itertuples():
        folium.CircleMarker(
            location=[row.lat, row.lon],
            radius=max(2, math.sqrt(row.count) * scale),
            color="white",
            weight=1,
            fill=True,
            fill_color=PRIMARY,
            fill_opacity=0.6,
            tooltip=f"{row.region}: {row.count:,}건 · {row.damage_area_ha:,.1f}ha",
        ).add_to(m)
    return m
