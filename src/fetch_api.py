"""산림청 산불통계 OpenAPI 를 호출해 원본 데이터를 data/raw/ 에 CSV 로 저장한다.

사용법:
    python -m src.fetch_api --start-year 2015 --end-year 2024
"""

import argparse
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import requests

from src.config import ApiConfig, get_api_config

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# 활용가이드 v1.3 응답 메시지 명세 (16개 항목)
FIELDS = [
    "startyear", "startmonth", "startday", "starttime", "startdayofweek",
    "endyear", "endmonth", "endday", "endtime",
    "locsi", "locgungu", "locmenu", "locdong", "locbunji",
    "firecause", "damagearea",
]  # fmt: skip

ERROR_CODES = {
    "01": "어플리케이션 에러",
    "02": "데이터베이스 에러",
    "04": "HTTP 에러",
    "10": "잘못된 요청 파라미터",
    "11": "필수 요청 파라미터 없음",
    "12": "해당 오픈API 서비스가 없거나 폐기됨",
    "20": "서비스 접근 거부 (활용신청 승인 여부 확인)",
    "22": "서비스 요청 제한 횟수 초과",
    "30": "등록되지 않은 서비스키 (키 값 또는 승인 대기 여부 확인)",
    "31": "기한 만료된 서비스키",
    "99": "기타 에러",
}


class ApiError(RuntimeError):
    pass


def parse_response(xml_text: str) -> tuple[list[dict], int]:
    """XML 응답을 (행 목록, totalCount) 로 변환한다."""
    root = ET.fromstring(xml_text)

    # 인증키 오류 등은 공공데이터포털 게이트웨이가 다른 형식으로 응답한다
    gateway_code = root.findtext(".//returnReasonCode")
    if gateway_code:
        msg = root.findtext(".//returnAuthMsg") or root.findtext(".//errMsg")
        raise ApiError(f"[{gateway_code}] {ERROR_CODES.get(gateway_code, msg)} ({msg})")

    code = root.findtext("header/resultCode")
    if code == "03":  # NODATA_ERROR
        return [], 0
    if code != "00":
        msg = root.findtext("header/resultMsg")
        raise ApiError(f"[{code}] {ERROR_CODES.get(code, msg)} ({msg})")

    rows = [{f: item.findtext(f) for f in FIELDS} for item in root.iter("item")]
    total = int(root.findtext("body/totalCount") or 0)
    return rows, total


def fetch_period(cfg: ApiConfig, start: str, end: str) -> list[dict]:
    """기간(YYYYMMDD~YYYYMMDD)의 모든 페이지를 조회한다."""
    rows: list[dict] = []
    page = 1
    while True:
        params = {
            "ServiceKey": cfg.service_key,
            "numOfRows": cfg.num_of_rows,
            "pageNo": page,
            "searchStDt": start,
            "searchEdDt": end,
        }
        try:
            resp = requests.get(cfg.endpoint, params=params, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            # 예외 메시지의 URL에 인증키가 들어 있으므로 노출하지 않는다
            status = getattr(e.response, "status_code", None)
            raise ApiError(
                f"HTTP 요청 실패 (status={status}, endpoint={cfg.endpoint}, "
                f"기간={start}~{end}, pageNo={page})"
            ) from None
        page_rows, total = parse_response(resp.text)
        rows.extend(page_rows)
        if not page_rows or len(rows) >= total:
            return rows
        page += 1
        time.sleep(0.1)  # 초당 최대 30tps 제한 여유


def main() -> None:
    parser = argparse.ArgumentParser(description="산불통계 API 수집")
    parser.add_argument("--start-year", type=int, required=True)
    parser.add_argument("--end-year", type=int, required=True)
    parser.add_argument("--force", action="store_true", help="기존 파일 덮어쓰기")
    args = parser.parse_args()

    out = RAW_DIR / f"fire_stats_{args.start_year}_{args.end_year}.csv"
    if out.exists() and not args.force:
        print(f"이미 존재: {out} (다시 받으려면 --force)")
        return

    cfg = get_api_config()
    all_rows: list[dict] = []
    for year in range(args.start_year, args.end_year + 1):
        year_rows = fetch_period(cfg, f"{year}0101", f"{year}1231")
        print(f"{year}년: {len(year_rows):,}건")
        all_rows.extend(year_rows)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(all_rows, columns=FIELDS).to_csv(
        out, index=False, encoding="utf-8-sig"
    )
    print(f"저장 완료: {out} (총 {len(all_rows):,}건)")


if __name__ == "__main__":
    main()
