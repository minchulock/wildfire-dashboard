import pytest

from src.fetch_api import ApiError, parse_response

# 활용가이드 v1.3 응답 예제 일부
SAMPLE_OK = """<response>
<header><resultCode>00</resultCode><resultMsg>NORMAL SERVICE.</resultMsg></header>
<body><items>
<item><damagearea>0.5</damagearea><endday>03</endday><endmonth>01</endmonth>
<endtime>16:20:00</endtime><endyear>2016</endyear><firecause>기타(직접입력)</firecause>
<locbunji>산27</locbunji><locdong>상청</locdong><locgungu>영양</locgungu><locmenu>청기</locmenu>
<locsi>경북</locsi><startday>03</startday><startdayofweek>일요일</startdayofweek>
<startmonth>01</startmonth><starttime>14:03:00</starttime><startyear>2016</startyear></item>
<item><damagearea>0.03</damagearea><locgungu>광주</locgungu><locsi>경기</locsi>
<startyear>2016</startyear><startmonth>01</startmonth></item>
</items><numOfRows>10</numOfRows><pageNo>1</pageNo><totalCount>361</totalCount></body>
</response>"""

SAMPLE_KEY_ERROR = """<OpenAPI_ServiceResponse><cmmMsgHeader>
<errMsg>SERVICE ERROR</errMsg><returnAuthMsg>SERVICE_KEY_IS_NOT_REGISTERED_ERROR</returnAuthMsg>
<returnReasonCode>30</returnReasonCode></cmmMsgHeader></OpenAPI_ServiceResponse>"""


def test_parse_ok():
    rows, total = parse_response(SAMPLE_OK)
    assert total == 361
    assert len(rows) == 2
    assert rows[0]["locsi"] == "경북"
    assert rows[1]["locdong"] is None  # 누락 항목은 None


def test_parse_nodata():
    rows, total = parse_response(
        "<response><header><resultCode>03</resultCode></header></response>"
    )
    assert rows == [] and total == 0


def test_parse_key_error():
    with pytest.raises(ApiError, match="등록되지 않은 서비스키"):
        parse_response(SAMPLE_KEY_ERROR)
