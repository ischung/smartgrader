import io
import uuid
import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from utils.deps import require_role
from utils.file_parser import ALLOWED_EXTENSIONS, MAX_FILE_SIZE, parse_grade_file
from utils.student_provisioner import provision_students
from utils.supabase_client import get_admin_client

router = APIRouter()

professor_or_admin = require_role("professor")

STORAGE_BUCKET = "grade-files"


@router.post("/{course_id}/files/upload")
async def upload_grade_file(
    course_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(professor_or_admin),
):
    admin = get_admin_client()

    # 과목 소유권 확인
    course = admin.table("courses").select("id").eq("id", course_id).eq("professor_id", current_user["id"]).execute()
    if not course.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="과목을 찾을 수 없습니다.")

    # 파일 형식 검증
    filename = file.filename or ""
    ext = filename[filename.rfind("."):].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"허용된 파일 형식: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 파일 크기 검증
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="파일 크기는 10MB 이하이어야 합니다.")

    # 파일 파싱
    try:
        parsed = parse_grade_file(content, filename)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="파일 파싱에 실패했습니다. 형식을 확인해주세요.")

    # Supabase Storage 업로드
    storage_path = f"{course_id}/{uuid.uuid4()}{ext}"
    try:
        admin.storage.from_(STORAGE_BUCKET).upload(
            path=storage_path,
            file=content,
            file_options={"content-type": file.content_type or "application/octet-stream"},
        )
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="파일 저장에 실패했습니다.")

    # grade_files 테이블 기록
    admin.table("grade_files").insert({
        "course_id": course_id,
        "file_type": "original",
        "storage_path": storage_path,
    }).execute()

    # 학생 계정 자동 생성
    provisioning = provision_students(parsed["student_ids"], admin)

    return {
        "storage_path": storage_path,
        "filename": filename,
        "columns": parsed["columns"],
        "preview": parsed["preview"],
        "total_rows": parsed["total_rows"],
        "extracted": parsed["extracted"],
        "students": provisioning,
    }


@router.get("/{course_id}/files")
def list_grade_files(
    course_id: str,
    current_user: dict = Depends(professor_or_admin),
):
    """과목에 업로드된 파일 목록을 반환한다 (최신순)."""
    admin = get_admin_client()
    course = admin.table("courses").select("id").eq("id", course_id).eq("professor_id", current_user["id"]).execute()
    if not course.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="과목을 찾을 수 없습니다.")
    result = (
        admin.table("grade_files")
        .select("id, file_type, storage_path, created_at")
        .eq("course_id", course_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


@router.get("/{course_id}/files/{file_id}/download")
def download_result_file(
    course_id: str,
    file_id: str,
    current_user: dict = Depends(professor_or_admin),
):
    """
    원본 파일에 총점·학점 열을 추가한 결과 xlsx 파일을 반환한다.
    총점·학점 미계산 상태이면 400을 반환한다.
    """
    admin = get_admin_client()

    # 과목 소유권 확인
    course = admin.table("courses").select("id").eq("id", course_id).eq("professor_id", current_user["id"]).execute()
    if not course.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="과목을 찾을 수 없습니다.")

    # 파일 레코드 확인
    file_record = (
        admin.table("grade_files")
        .select("id, storage_path, file_type")
        .eq("id", file_id)
        .eq("course_id", course_id)
        .execute()
    )
    if not file_record.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="파일을 찾을 수 없습니다.")

    storage_path = file_record.data[0]["storage_path"]

    # 학점까지 계산된 결과 확인
    grade_results = (
        admin.table("grade_results")
        .select("student_id, total_score, grade")
        .eq("course_id", course_id)
        .execute()
    )
    if not grade_results.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="총점이 계산되지 않았습니다. 먼저 /scores/calculate를 실행하세요.",
        )
    if any(r.get("grade") is None for r in grade_results.data):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="학점이 계산되지 않았습니다. 먼저 /grades/calculate를 실행하세요.",
        )

    # 학번 → (총점, 학점) 매핑
    student_ids = [r["student_id"] for r in grade_results.data]
    users_resp = (
        admin.table("users")
        .select("id, login_id")
        .in_("id", student_ids)
        .execute()
    )
    login_map = {u["id"]: u["login_id"] for u in (users_resp.data or [])}
    score_map = {
        login_map[r["student_id"]]: (float(r["total_score"]), r["grade"])
        for r in grade_results.data
        if r["student_id"] in login_map
    }

    # 원본 파일 다운로드
    try:
        file_bytes = admin.storage.from_(STORAGE_BUCKET).download(storage_path)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="원본 파일을 불러올 수 없습니다.")

    # pandas로 파싱
    ext = storage_path[storage_path.rfind("."):].lower()
    if ext == ".csv":
        df = pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8-sig")
    else:
        df = pd.read_excel(io.BytesIO(file_bytes))

    # 학번 컬럼 찾기
    student_id_col = None
    for col in df.columns:
        if str(col).lower() in ["학번", "student_id", "studentid", "student_number", "학생번호"]:
            student_id_col = col
            break

    # 총점·학점 컬럼 추가
    if student_id_col:
        df["총점"] = df[student_id_col].astype(str).map(lambda sid: score_map.get(sid, (None, None))[0])
        df["학점"] = df[student_id_col].astype(str).map(lambda sid: score_map.get(sid, (None, None))[1])
    else:
        df["총점"] = None
        df["학점"] = None

    # xlsx 생성
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    result_bytes = buf.read()

    # 결과 파일 Storage 저장
    result_path = f"{course_id}/result_{uuid.uuid4()}.xlsx"
    try:
        admin.storage.from_(STORAGE_BUCKET).upload(
            path=result_path,
            file=result_bytes,
            file_options={"content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
        )
        admin.table("grade_files").insert({
            "course_id": course_id,
            "file_type": "result",
            "storage_path": result_path,
        }).execute()
    except Exception:
        pass  # 저장 실패해도 다운로드는 제공

    return StreamingResponse(
        io.BytesIO(result_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=result_{course_id}.xlsx"},
    )
