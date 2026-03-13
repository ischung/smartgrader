import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
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
        "file_type": "upload",
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
