"""산불 발생 현황 대시보드 (Streamlit 진입점).

실행: streamlit run app.py
"""

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.analysis import region_counts, region_points, yearly_counts
from src.charts import (
    region_map,
    sido_bar_chart,
    yearly_count_chart,
    yearly_damage_chart,
)
from src.load import load_centroids, load_processed

st.set_page_config(page_title="산불 발생 현황 대시보드", page_icon="🔥", layout="wide")


@st.cache_data
def get_fires() -> pd.DataFrame:
    return load_processed()


@st.cache_data
def get_centroids() -> pd.DataFrame:
    return load_centroids()


fires = get_fires()

# ── 사이드바 필터 ──
st.sidebar.header("필터")
min_year, max_year = int(fires["year"].min()), int(fires["year"].max())
year_range = st.sidebar.slider("기간(연도)", min_year, max_year, (min_year, max_year))
all_sido = sorted(fires["sido"].unique())
sido = st.sidebar.multiselect("시도", all_sido, placeholder="전체")

filtered_df = fires[fires["year"].between(*year_range)]
if sido:
    filtered_df = filtered_df[filtered_df["sido"].isin(sido)]

st.title("🔥 산불 발생 현황 대시보드")
st.caption(
    f"산림청 산불통계 OpenAPI · {year_range[0]}~{year_range[1]}년 · "
    f"{'전체 시도' if not sido else ', '.join(sido)} · {len(filtered_df):,}건"
)

if filtered_df.empty:
    st.warning("선택한 조건에 해당하는 산불이 없습니다.")
    st.stop()

tab_trend, tab_region, tab_month, tab_map = st.tabs(
    ["추이", "지역", "월별 패턴", "지도"]
)

with tab_trend:
    yearly = yearly_counts(filtered_df, range(year_range[0], year_range[1] + 1))
    left, right = st.columns(2)
    left.plotly_chart(yearly_count_chart(yearly), width="stretch")
    right.plotly_chart(yearly_damage_chart(yearly), width="stretch")

with tab_region:
    metric = st.radio(
        "기준",
        ["count", "damage_area_ha"],
        format_func={"count": "발생 건수", "damage_area_ha": "피해면적"}.get,
        horizontal=True,
    )
    if len(sido) == 1:  # 시도 하나면 막대 1개 대신 그 시도의 시군구별로
        fig = sido_bar_chart(
            region_counts(filtered_df, by="sigungu"),
            metric,
            by="sigungu",
            title=f"{sido[0]} 시군구별",
        )
    else:
        fig = sido_bar_chart(region_counts(filtered_df), metric)
    st.plotly_chart(fig, width="stretch")

with tab_month:
    st.info("4단계에서 월별·시간대별 패턴 차트를 추가합니다.")

with tab_map:
    points = region_points(filtered_df, get_centroids())
    st_folium(
        region_map(points), height=600, use_container_width=True, returned_objects=[]
    )
    st.caption(
        f"시군구 중심 좌표(통계청 2013 경계 기준)에 {points['count'].sum():,}건 표시 · "
        f"시군구 정보가 없는 {len(filtered_df) - points['count'].sum():,}건 제외. "
        "2013년 이후 신설된 구는 상위 시, 세종은 시 중심, 대구 군위는 2013년 소속(경북)에 표시."
    )
