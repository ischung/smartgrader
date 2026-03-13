"""
파일 업로드 API 테스트
"""
import io
import pandas as pd
from fastapi.testclient import TestClient
from main import app
from utils.file_parser import parse_grade_file, ALLOWED_EXTENSIONS, MAX_FILE_SIZE

client = TestClient(app)


def test_upload_without_token():
    response = client.post("/api/v1/courses/some-id/files/upload")
    assert response.status_code == 403


def test_allowed_extensions():
    assert ".xlsx" in ALLOWED_EXTENSIONS
    assert ".xls" in ALLOWED_EXTENSIONS
    assert ".csv" in ALLOWED_EXTENSIONS
    assert ".pdf" not in ALLOWED_EXTENSIONS


def test_max_file_size():
    assert MAX_FILE_SIZE == 10 * 1024 * 1024


def test_parse_csv():
    """CSV 파일 파싱 테스트"""
    csv_content = "과목명,교과코드,분반,학기,학번,점수\n소프트웨어공학,CS101,A,2026-1,20210001,85\n"
    result = parse_grade_file(csv_content.encode("utf-8-sig"), "test.csv")

    assert "소프트웨어공학" in result["columns"] or "과목명" in result["columns"]
    assert result["total_rows"] == 1
    assert len(result["preview"]) == 1


def test_parse_excel():
    """Excel 파일 파싱 테스트"""
    df = pd.DataFrame({
        "과목명": ["소프트웨어공학"],
        "교과코드": ["CS101"],
        "학번": ["20210001"],
        "점수": [85],
    })
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)

    result = parse_grade_file(buf.read(), "test.xlsx")
    assert result["total_rows"] == 1
    assert result["extracted"]["course_name"] == "소프트웨어공학"
    assert result["extracted"]["course_code"] == "CS101"


def test_extract_course_info():
    """과목 정보 자동 추출 테스트"""
    df = pd.DataFrame({
        "과목명": ["데이터베이스"],
        "교과코드": ["CS202"],
        "분반": ["B"],
        "학기": ["2026-2"],
    })
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)

    result = parse_grade_file(buf.read(), "test.xlsx")
    assert result["extracted"]["course_name"] == "데이터베이스"
    assert result["extracted"]["course_code"] == "CS202"
    assert result["extracted"]["section"] == "B"
    assert result["extracted"]["semester"] == "2026-2"
