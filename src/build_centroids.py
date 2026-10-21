"""통계청(KOSTAT) 2013 시군구 경계 GeoJSON에서 시군구 중심 좌표 CSV를 만든다.

출처: https://github.com/southkorea/southkorea-maps (kostat/2013/json/skorea_municipalities_geo_simple.json)

사용법:
    python -m src.build_centroids
"""

import json
import re
from collections import defaultdict
from pathlib import Path

import pandas as pd

from src.load import CENTROIDS_PATH, DATA_DIR

REF_DIR = DATA_DIR / "reference"
GEOJSON_PATH = REF_DIR / "skorea_municipalities_2013.geojson"

# KOSTAT 2013 행정구역코드 앞 2자리 → API 시도명
SIDO_CODE = {
    "11": "서울", "21": "부산", "22": "대구", "23": "인천", "24": "광주",
    "25": "대전", "26": "울산", "29": "세종", "31": "경기", "32": "강원",
    "33": "충북", "34": "충남", "35": "전북", "36": "전남", "37": "경북",
    "38": "경남", "39": "제주",
}  # fmt: skip


def short_name(name: str) -> tuple[str, str]:
    """'고양시덕양구' → ('고양 덕양', '고양'), '양평군' → ('양평', '양평')."""
    m = re.fullmatch(r"(.+?)시(.+)구", name)
    if m:  # 일반구가 있는 시
        return f"{m[1]} {m[2]}", m[1]
    base = re.sub(r"[시군구]$", "", name)
    return base, base


def _ring_centroid(ring: list) -> tuple[float, float, float]:
    """다각형 외곽선의 (면적, 경도 중심, 위도 중심)을 신발끈 공식으로 구한다."""
    a = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
        cross = x0 * y1 - x1 * y0
        a += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    a /= 2
    return abs(a), cx / (6 * a), cy / (6 * a)


def _polygons(geometry: dict) -> list:
    if geometry["type"] == "Polygon":
        return [geometry["coordinates"]]
    return geometry["coordinates"]


def _weighted(parts: list[tuple[float, float, float]]) -> tuple[float, float]:
    """(면적, 경도, 위도) 목록의 면적 가중 중심 (위도, 경도)."""
    total = sum(p[0] for p in parts)
    lon = sum(p[0] * p[1] for p in parts) / total
    lat = sum(p[0] * p[2] for p in parts) / total
    return lat, lon


def build_centroids(geojson: dict) -> pd.DataFrame:
    """시군구별 중심 좌표와, 일반구를 묶은 시(市) 단위 중심 좌표를 함께 만든다."""
    exact: dict[tuple, list] = defaultdict(list)
    city: dict[tuple, list] = defaultdict(list)
    for feature in geojson["features"]:
        props = feature["properties"]
        sido = SIDO_CODE[props["code"][:2]]
        parts = [_ring_centroid(poly[0]) for poly in _polygons(feature["geometry"])]
        full, city_name = short_name(props["name"])
        exact[(sido, full)].extend(parts)
        if full != city_name:
            city[(sido, city_name)].extend(parts)

    rows = [
        (sido, name, *_weighted(parts), "exact")
        for (sido, name), parts in exact.items()
    ]
    rows += [
        (sido, name, *_weighted(parts), "city")
        for (sido, name), parts in city.items()
        if (sido, name) not in exact
    ]
    return pd.DataFrame(rows, columns=["sido", "sigungu", "lat", "lon", "level"])


def main() -> None:
    geojson = json.loads(Path(GEOJSON_PATH).read_text(encoding="utf-8"))
    out = build_centroids(geojson).sort_values(["sido", "sigungu"])
    out.to_csv(CENTROIDS_PATH, index=False, encoding="utf-8-sig")
    print(f"저장 완료: {CENTROIDS_PATH} ({len(out)}개)")


if __name__ == "__main__":
    main()
