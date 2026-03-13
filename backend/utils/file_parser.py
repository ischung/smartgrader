"""
성적 파일 파싱 유틸리티
xlsx / xls / csv → DataFrame → 미리보기 + 과목 정보 자동 추출
"""
import io
from typing import Optional
import pandas as pd

ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
PREVIEW_ROWS = 5


def parse_grade_file(content: bytes, filename: str) -> dict:
    """
    파일 파싱 후 반환:
    {
        "columns": [...],
        "preview": [[...], ...],   # 최대 5행
        "total_rows": int,
        "extracted": {             # 자동 추출 결과 (실패 시 None)
            "course_name": str | None,
            "course_code": str | None,
            "section": str | None,
            "semester": str | None,
        }
    }
    """
    ext = _get_extension(filename)

    if ext == ".csv":
        df = pd.read_csv(io.BytesIO(content), encoding="utf-8-sig")
    else:
        df = pd.read_excel(io.BytesIO(content))

    columns = df.columns.tolist()
    preview = df.head(PREVIEW_ROWS).fillna("").values.tolist()
    total_rows = len(df)

    extracted = _extract_course_info(df, columns)
    student_ids = extract_student_ids(df, columns)

    return {
        "columns": [str(c) for c in columns],
        "preview": [[str(v) for v in row] for row in preview],
        "total_rows": total_rows,
        "extracted": extracted,
        "student_ids": student_ids,
    }


def _get_extension(filename: str) -> str:
    idx = filename.rfind(".")
    if idx == -1:
        return ""
    return filename[idx:].lower()


def _extract_course_info(df: pd.DataFrame, columns: list) -> dict:
    """
    첫 번째 행 또는 헤더에서 과목 정보 추출 시도.
    컬럼명 키워드: 과목명, 교과코드, 분반, 학기
    """
    result: dict[str, Optional[str]] = {
        "course_name": None,
        "course_code": None,
        "section": None,
        "semester": None,
    }

    col_map = {
        "course_name": ["과목명", "course_name", "subject", "교과목명"],
        "course_code": ["교과코드", "course_code", "code", "교과번호"],
        "section": ["분반", "section", "class"],
        "semester": ["학기", "semester", "term"],
    }

    lower_cols = {str(c).lower(): str(c) for c in columns}

    for field, keywords in col_map.items():
        for kw in keywords:
            if kw.lower() in lower_cols:
                col = lower_cols[kw.lower()]
                if len(df) > 0:
                    val = df[col].iloc[0]
                    result[field] = str(val) if pd.notna(val) else None
                break

    return result


# 학번 컬럼 키워드
_STUDENT_ID_KEYWORDS = ["학번", "student_id", "studentid", "student_number", "학생번호"]


def extract_student_ids(df: "pd.DataFrame", columns: list) -> list[str]:
    """
    DataFrame에서 학번 컬럼을 찾아 고유 학번 목록을 반환한다.
    학번 컬럼을 찾지 못하면 빈 리스트를 반환한다.
    """
    lower_cols = {str(c).lower(): str(c) for c in columns}
    for kw in _STUDENT_ID_KEYWORDS:
        if kw.lower() in lower_cols:
            col = lower_cols[kw.lower()]
            ids = df[col].dropna().astype(str).str.strip()
            return list(ids[ids != ""].unique())
    return []
