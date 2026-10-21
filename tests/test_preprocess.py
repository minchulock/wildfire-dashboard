import pandas as pd

from src.load import read_csv_auto
from src.preprocess import preprocess


def make_raw(**overrides) -> pd.DataFrame:
    row = {
        "startyear": "2022", "startmonth": "03", "startday": "04",
        "starttime": "11:17:00", "startdayofweek": "금요일",
        "endyear": "2022", "endmonth": "03", "endday": "04", "endtime": "13:17:00",
        "locsi": "경북", "locgungu": "울진", "locmenu": "북", "locdong": "두천",
        "locbunji": "산1", "firecause": "기타", "damagearea": "0.5",
    }  # fmt: skip
    row.update(overrides)
    return pd.DataFrame([row])


def test_basic_columns_and_types():
    df, report = preprocess(make_raw())
    r = df.iloc[0]
    assert (r.year, r.month, r.day) == (2022, 3, 4)
    assert r.duration_min == 120
    assert r.damage_area_ha == 0.5
    assert r.region == "경북 울진"
    assert report["최종 행 수"] == 1


def test_sido_normalize():
    df, _ = preprocess(make_raw(locsi="강원특별자치도", locgungu="고성"))
    assert df.iloc[0].sido == "강원"
    assert df.iloc[0].region == "강원 고성"


def test_invalid_duration_becomes_nan():
    negative = make_raw(starttime="22:05:00", endtime="00:00:00")
    typo_year = make_raw(endyear="2223")
    df, report = preprocess(pd.concat([negative, typo_year]))
    assert df["duration_min"].isna().all()
    assert report["진화시간 이상(음수·30일 초과 → 결측)"] == 2


def test_missing_sigungu_keeps_sido_region():
    df, _ = preprocess(make_raw(locgungu=None))
    assert df.iloc[0].region == "경북"


def test_read_csv_auto_cp949(tmp_path):
    path = tmp_path / "cp949.csv"
    path.write_bytes("시도,건수\n강원,3\n".encode("cp949"))
    assert read_csv_auto(path).iloc[0]["시도"] == "강원"
