from fastapi import APIRouter, Depends, HTTPException, status
from models.scores import ScorePatch, ScoreTableResponse, GradeItemInfo, StudentScoreRow, ScoreCell
from utils.deps import require_role
from utils.grade_calculator import (
    ItemInfo, GroupInfo, ScoreCell as CalcCell,
    validate_weight_sum, calculate_student_total,
)
from utils.supabase_client import get_admin_client

router = APIRouter()

professor_or_admin = require_role("professor")


def _get_course_or_403(admin, course_id: str, professor_id: str):
    """과목 소유권 확인 — 없으면 403 (AC 명시)"""
    result = (
        admin.table("courses")
        .select("id")
        .eq("id", course_id)
        .eq("professor_id", professor_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")


@router.get("/{course_id}/scores", response_model=ScoreTableResponse)
def get_scores(
    course_id: str,
    current_user: dict = Depends(professor_or_admin),
):
    admin = get_admin_client()
    _get_course_or_403(admin, course_id, current_user["id"])

    # 성적 항목 목록 (display_order 정렬)
    items_resp = (
        admin.table("grade_items")
        .select("id, name, item_type, weight, display_order")
        .eq("course_id", course_id)
        .order("display_order")
        .execute()
    )
    items = items_resp.data or []
    item_ids = [i["id"] for i in items]

    # 수강 학생 목록 (student_scores에 등록된 학번으로 확인)
    if item_ids:
        scores_resp = (
            admin.table("student_scores")
            .select("id, student_id, grade_item_id, raw_score, absence_count")
            .eq("course_id", course_id)
            .execute()
        )
        all_scores = scores_resp.data or []
    else:
        all_scores = []

    # 과목 수강 학생 UUID 목록
    student_ids = list({s["student_id"] for s in all_scores})

    students = []
    if student_ids:
        users_resp = (
            admin.table("users")
            .select("id, name, login_id")
            .in_("id", student_ids)
            .execute()
        )
        users = users_resp.data or []

        # 점수를 (student_id, grade_item_id) → cell 로 인덱싱
        score_index: dict[tuple, dict] = {}
        for s in all_scores:
            score_index[(s["student_id"], s["grade_item_id"])] = s

        for user in users:
            row_scores: dict[str, ScoreCell] = {}
            for item in items:
                cell = score_index.get((user["id"], item["id"]))
                if cell:
                    row_scores[item["id"]] = ScoreCell(
                        id=cell["id"],
                        raw_score=cell.get("raw_score"),
                        absence_count=cell.get("absence_count"),
                    )
                else:
                    row_scores[item["id"]] = ScoreCell()
            students.append(StudentScoreRow(
                id=user["id"],
                name=user["name"],
                login_id=user["login_id"],
                scores=row_scores,
            ))

    return ScoreTableResponse(
        items=[GradeItemInfo(**i) for i in items],
        students=students,
    )


@router.patch("/{course_id}/scores", status_code=status.HTTP_200_OK)
def upsert_score(
    course_id: str,
    body: ScorePatch,
    current_user: dict = Depends(professor_or_admin),
):
    admin = get_admin_client()
    _get_course_or_403(admin, course_id, current_user["id"])

    # 성적 항목 확인 (item_type, weight 검증용)
    item_resp = (
        admin.table("grade_items")
        .select("id, item_type, weight")
        .eq("id", body.grade_item_id)
        .eq("course_id", course_id)
        .execute()
    )
    if not item_resp.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="성적 항목을 찾을 수 없습니다.")

    item = item_resp.data[0]
    item_type = item["item_type"]

    # 타입별 검증
    if item_type == "attitude":
        if body.raw_score is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="attitude 항목은 raw_score가 필요합니다.",
            )
        max_score = float(item["weight"]) if item.get("weight") is not None else 100.0
        if body.raw_score > max_score:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"attitude 점수는 0~{max_score} 범위여야 합니다.",
            )
    elif item_type == "attendance":
        if body.raw_score is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="attendance 항목은 absence_count만 사용합니다.",
            )

    # 학생 존재 확인
    student_resp = (
        admin.table("users")
        .select("id")
        .eq("id", body.student_id)
        .eq("role", "student")
        .execute()
    )
    if not student_resp.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="학생을 찾을 수 없습니다.")

    upsert_data = {
        "course_id": course_id,
        "student_id": body.student_id,
        "grade_item_id": body.grade_item_id,
        "raw_score": body.raw_score,
        "absence_count": body.absence_count,
    }

    result = (
        admin.table("student_scores")
        .upsert(upsert_data, on_conflict="course_id,student_id,grade_item_id")
        .execute()
    )
    return result.data[0]


@router.post("/{course_id}/scores/calculate", status_code=status.HTTP_200_OK)
def calculate_scores(
    course_id: str,
    current_user: dict = Depends(professor_or_admin),
):
    """
    과목의 전체 학생 총점을 계산하여 grade_results 테이블에 저장한다.
    가중치 합계가 100%가 아니면 400을 반환한다.
    """
    admin = get_admin_client()
    _get_course_or_403(admin, course_id, current_user["id"])

    # 성적 항목 로드
    items_resp = (
        admin.table("grade_items")
        .select("id, item_type, weight, group_id, deduction_per_absence")
        .eq("course_id", course_id)
        .execute()
    )
    items_data = items_resp.data or []

    # 그룹 로드
    groups_resp = (
        admin.table("grade_item_groups")
        .select("id, weight")
        .eq("course_id", course_id)
        .execute()
    )
    groups_data = groups_resp.data or []

    items = [
        ItemInfo(
            id=i["id"],
            item_type=i["item_type"],
            weight=float(i["weight"]) if i.get("weight") is not None else None,
            group_id=i.get("group_id"),
            deduction_per_absence=float(i.get("deduction_per_absence") or 0.5),
        )
        for i in items_data
    ]
    groups = [GroupInfo(id=g["id"], weight=float(g["weight"])) for g in groups_data]

    # 가중치 합계 검증
    if not validate_weight_sum(items, groups):
        non_grouped = sum(i.weight for i in items if i.group_id is None and i.weight is not None)
        group_sum = sum(g.weight for g in groups)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"가중치 합계가 100%가 아닙니다. 현재: {non_grouped + group_sum:.2f}%",
        )

    # 점수 로드
    scores_resp = (
        admin.table("student_scores")
        .select("student_id, grade_item_id, raw_score, absence_count")
        .eq("course_id", course_id)
        .execute()
    )
    all_scores = scores_resp.data or []

    # 학생별 점수 인덱싱
    student_score_map: dict[str, dict[str, CalcCell]] = {}
    for row in all_scores:
        sid = row["student_id"]
        if sid not in student_score_map:
            student_score_map[sid] = {}
        student_score_map[sid][row["grade_item_id"]] = CalcCell(
            raw_score=row.get("raw_score"),
            absence_count=row.get("absence_count"),
        )

    # 학생 정보 로드
    student_ids = list(student_score_map.keys())
    if not student_ids:
        return []

    users_resp = (
        admin.table("users")
        .select("id, name, login_id")
        .in_("id", student_ids)
        .execute()
    )
    users = {u["id"]: u for u in (users_resp.data or [])}

    # 총점 계산 및 grade_results upsert
    results = []
    for sid, scores in student_score_map.items():
        total = calculate_student_total(scores, items, groups)
        admin.table("grade_results").upsert(
            {
                "course_id": course_id,
                "student_id": sid,
                "total_score": total,
                "grade": None,
            },
            on_conflict="course_id,student_id",
        ).execute()

        user = users.get(sid, {})
        results.append({
            "student_id": sid,
            "login_id": user.get("login_id"),
            "name": user.get("name"),
            "total_score": total,
        })

    return sorted(results, key=lambda r: r.get("login_id") or "")
