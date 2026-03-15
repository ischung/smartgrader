from fastapi import APIRouter, Depends, HTTPException, status
from models.grade_policy import (
    GradePolicyEntry, GradePolicyPut,
    GradePolicyEntryResponse, GradeResultResponse,
)
from utils.deps import require_role
from utils.supabase_client import get_admin_client

router = APIRouter()

professor_or_admin = require_role("professor")


def _get_course_or_404(admin, course_id: str, professor_id: str):
    result = (
        admin.table("courses")
        .select("id")
        .eq("id", course_id)
        .eq("professor_id", professor_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="과목을 찾을 수 없습니다.")


def _assign_grade(total_score: float, entries: list[GradePolicyEntry]) -> str:
    """총점이 속하는 학점 구간을 반환한다. 해당 없으면 'F'."""
    for entry in entries:
        if entry.min_score <= total_score <= entry.max_score:
            return entry.grade
    return "F"


@router.get("/{course_id}/policy", response_model=list[GradePolicyEntryResponse])
def get_policy(
    course_id: str,
    current_user: dict = Depends(professor_or_admin),
):
    admin = get_admin_client()
    _get_course_or_404(admin, course_id, current_user["id"])

    result = (
        admin.table("grade_policies")
        .select("*")
        .eq("course_id", course_id)
        .order("min_score", desc=True)
        .execute()
    )
    return result.data or []


@router.put("/{course_id}/policy", response_model=list[GradePolicyEntryResponse])
def set_policy(
    course_id: str,
    body: GradePolicyPut,
    current_user: dict = Depends(professor_or_admin),
):
    """
    학점 범위 전체를 교체한다 (기존 데이터 삭제 후 새로 저장).
    Pydantic 모델에서 이미 겹침 검증을 완료한 상태로 진입한다.
    """
    admin = get_admin_client()
    _get_course_or_404(admin, course_id, current_user["id"])

    # 기존 정책 전체 삭제 후 재등록
    admin.table("grade_policies").delete().eq("course_id", course_id).execute()

    rows = [
        {
            "course_id": course_id,
            "grade": e.grade,
            "min_score": e.min_score,
            "max_score": e.max_score,
        }
        for e in body.entries
    ]
    result = admin.table("grade_policies").insert(rows).execute()
    return result.data or []


@router.post("/{course_id}/grades/calculate", response_model=list[GradeResultResponse])
def calculate_grades(
    course_id: str,
    current_user: dict = Depends(professor_or_admin),
):
    """
    grade_results의 total_score를 학점 정책에 적용하여 grade를 산출한다.
    총점 미계산(grade_results 없음) 또는 정책 미설정 시 400을 반환한다.
    """
    admin = get_admin_client()
    _get_course_or_404(admin, course_id, current_user["id"])

    # 총점 계산 여부 확인
    results_resp = (
        admin.table("grade_results")
        .select("id, student_id, total_score")
        .eq("course_id", course_id)
        .execute()
    )
    grade_results = results_resp.data or []
    if not grade_results:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="총점이 계산되지 않았습니다. 먼저 /scores/calculate를 실행하세요.",
        )

    # 학점 정책 로드
    policy_resp = (
        admin.table("grade_policies")
        .select("grade, min_score, max_score")
        .eq("course_id", course_id)
        .execute()
    )
    policy_data = policy_resp.data or []
    if not policy_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="학점 정책이 설정되지 않았습니다. 먼저 PUT /policy를 실행하세요.",
        )

    policy_entries = [
        GradePolicyEntry(grade=p["grade"], min_score=p["min_score"], max_score=p["max_score"])
        for p in policy_data
    ]

    # 학생 정보 로드
    student_ids = [r["student_id"] for r in grade_results]
    users_resp = (
        admin.table("users")
        .select("id, name, login_id")
        .in_("id", student_ids)
        .execute()
    )
    user_map = {u["id"]: u for u in (users_resp.data or [])}

    # 학점 산출 및 저장
    response = []
    for gr in grade_results:
        sid = gr["student_id"]
        total = float(gr["total_score"])
        grade = _assign_grade(total, policy_entries)

        admin.table("grade_results").update({"grade": grade}).eq("id", gr["id"]).execute()

        user = user_map.get(sid, {})
        response.append(GradeResultResponse(
            student_id=sid,
            login_id=user.get("login_id"),
            name=user.get("name"),
            total_score=total,
            grade=grade,
        ))

    return sorted(response, key=lambda r: r.login_id or "")
