from fastapi import APIRouter, Depends, HTTPException, status
from models.courses import CourseCreate, CourseUpdate, CourseResponse
from utils.deps import require_role
from utils.supabase_client import get_admin_client

router = APIRouter()

professor_or_admin = require_role("professor")


@router.get("", response_model=list[CourseResponse])
def list_courses(current_user: dict = Depends(professor_or_admin)):
    """본인 과목만 반환 (admin도 자기 professor_id 기준)"""
    admin = get_admin_client()
    result = admin.table("courses").select("*").eq("professor_id", current_user["id"]).execute()
    return result.data


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(body: CourseCreate, current_user: dict = Depends(professor_or_admin)):
    admin = get_admin_client()
    row = admin.table("courses").insert({
        "professor_id": current_user["id"],
        "course_name": body.course_name,
        "course_code": body.course_code,
        "section": body.section,
        "semester": body.semester,
    }).execute()
    return row.data[0]


@router.patch("/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: str,
    body: CourseUpdate,
    current_user: dict = Depends(professor_or_admin),
):
    admin = get_admin_client()

    # 본인 과목인지 확인
    existing = admin.table("courses").select("id").eq("id", course_id).eq("professor_id", current_user["id"]).execute()
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="과목을 찾을 수 없습니다.")

    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="변경할 내용이 없습니다.")

    result = admin.table("courses").update(update_data).eq("id", course_id).execute()
    return result.data[0]


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: str, current_user: dict = Depends(professor_or_admin)):
    admin = get_admin_client()

    # 본인 과목인지 확인
    existing = admin.table("courses").select("id").eq("id", course_id).eq("professor_id", current_user["id"]).execute()
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="과목을 찾을 수 없습니다.")

    # CASCADE로 관련 성적 데이터 함께 삭제
    admin.table("courses").delete().eq("id", course_id).execute()
    return
