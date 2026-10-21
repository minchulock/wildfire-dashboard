"""환경 설정값(.env / Streamlit secrets)을 읽는다."""

import os
from dataclasses import dataclass
from urllib.parse import unquote

from dotenv import load_dotenv

load_dotenv()

OPERATION = "getfirestatsservice"
DEFAULT_ENDPOINT = f"http://apis.data.go.kr/1400000/forestStusService/{OPERATION}"


def normalize_endpoint(endpoint: str) -> str:
    """서비스 주소만 넣은 경우 상세기능명(getfirestatsservice)을 붙인다."""
    endpoint = endpoint.strip().rstrip("/")
    if not endpoint.endswith(OPERATION):
        endpoint = f"{endpoint}/{OPERATION}"
    return endpoint


@dataclass(frozen=True)
class ApiConfig:
    endpoint: str
    service_key: str
    num_of_rows: int


def get_api_config() -> ApiConfig:
    """산불통계 API 설정을 환경변수에서 읽어 반환한다."""
    key = os.getenv("FOREST_FIRE_SERVICE_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "FOREST_FIRE_SERVICE_KEY 가 비어 있습니다. .env.example 을 .env 로 복사한 뒤 인증키를 넣어주세요."
        )
    # Encoding 키가 들어와도 requests 가 다시 인코딩하므로 한 번 디코딩해 둔다
    if "%" in key:
        key = unquote(key)
    return ApiConfig(
        endpoint=normalize_endpoint(
            os.getenv("FOREST_FIRE_API_ENDPOINT") or DEFAULT_ENDPOINT
        ),
        service_key=key,
        num_of_rows=int(os.getenv("FOREST_FIRE_NUM_OF_ROWS", "99")),
    )
