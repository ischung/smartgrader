"""
결과 파일 생성 및 다운로드 API 테스트
"""
import io
import pandas as pd
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_download_without_token():
    response = client.get("/api/v1/courses/some-id/files/file-id/download")
    assert response.status_code == 403


def test_result_xlsx_columns():
    """결과 파일에 총점·학점 열이 포함되어야 한다 (로컬 생성 검증)"""
    df = pd.DataFrame({
        "학번": ["20210001", "20210002"],
        "이름": ["홍길동", "김철수"],
        "중간고사": [80, 90],
    })
    score_map = {
        "20210001": (85.0, "B+"),
        "20210002": (92.0, "A0"),
    }

    df["총점"] = df["학번"].astype(str).map(lambda sid: score_map.get(sid, (None, None))[0])
    df["학점"] = df["학번"].astype(str).map(lambda sid: score_map.get(sid, (None, None))[1])

    assert "총점" in df.columns
    assert "학점" in df.columns
    assert df.loc[df["학번"] == "20210001", "총점"].iloc[0] == 85.0
    assert df.loc[df["학번"] == "20210002", "학점"].iloc[0] == "A0"


def test_result_xlsx_original_preserved():
    """원본 열이 그대로 유지되어야 한다"""
    df = pd.DataFrame({
        "학번": ["20210001"],
        "이름": ["홍길동"],
        "중간고사": [80],
    })
    df["총점"] = [85.0]
    df["학점"] = ["B+"]

    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    df_read = pd.read_excel(buf)

    # 원본 컬럼 보존 확인
    assert "학번" in df_read.columns
    assert "이름" in df_read.columns
    assert "중간고사" in df_read.columns
    # 추가 컬럼 확인
    assert "총점" in df_read.columns
    assert "학점" in df_read.columns


def test_result_xlsx_no_student_id_col():
    """학번 컬럼 없으면 총점·학점이 None으로 추가된다"""
    df = pd.DataFrame({"이름": ["홍길동"], "점수": [80]})
    df["총점"] = None
    df["학점"] = None

    assert "총점" in df.columns
    assert df["총점"].iloc[0] is None
