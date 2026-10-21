from src.config import DEFAULT_ENDPOINT, normalize_endpoint


def test_normalize_endpoint_appends_operation():
    base = "https://apis.data.go.kr/1400000/forestStusService"
    assert normalize_endpoint(base) == f"{base}/getfirestatsservice"
    assert normalize_endpoint(base + "/") == f"{base}/getfirestatsservice"


def test_normalize_endpoint_keeps_full_url():
    assert normalize_endpoint(DEFAULT_ENDPOINT) == DEFAULT_ENDPOINT
