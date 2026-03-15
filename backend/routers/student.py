"""
학생 전용 API

GET /api/v1/student/courses          — 학기별 수강 과목 목록
GET /api/v1/student/courses/{id}/scores — 항목별 점수·기여점수·총점·학점
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from utils.deps import require_role
from utils.grade_calculator import ItemInfo, GroupInfo, ScoreCell
from utils.supabase_client import get_admin_client

router = APIRouter()

student_only = require_role("student")


# ── 기여 점수 계산 헬퍼 ───────────────────────────────────────────

def _compute_contributions(
    items: list[ItemInfo],
    groups: list[GroupInfo],
    scores: dict[str, ScoreCell],
) -> dict[str, Optional[float]]:
    """
    항목별 기여 점수를 반환한다.
    그룹 항목: raw_score_i / n_items × group_weight/100 (n=그룹 내 점수 입력 항목 수)
    비그룹 항목: 타입별 계산
    """
    group_map = {g.id: g for g in groups}

    # 그룹별 항목 묶기
    group_items: dict[str, list[ItemInfo]] = {g.id: [] for g in groups}
    for item in items:
        if item.group_id and item.group_id in group_map:
            group_items[item.group_id].append(item)

    # 그룹별 점수 입력 수
    group_scored_n: dict[str, int] = {}
    for gid, g_items in group_items.items():
        group_scored_n[gid] = sum(
            1 for i in g_items if scores.get(i.id) and scores[i.id].raw_score is not None
        )

    contributions: dict[str, Optional[float]] = {}
    for item in items:
        cell = scores.get(item.id)

        if item.group_id and item.group_id in group_map:
            # 그룹 소속 항목
            group = group_map[item.group_id]
            n = group_scored_n.get(item.group_id, 0)
            if n > 0 and cell and cell.raw_score is not None:
                contributions[item.id] = round(
                    cell.raw_score / n * (group.weight / 100.0), 2
                )
            else:
                contributions[item.id] = None
        else:
            # 비그룹 항목
            if item.item_type == "general":
                if cell and cell.raw_score is not None and item.weight is not None:
                    contributions[item.id] = round(
                        cell.raw_score * (item.weight / 100.0), 2
                    )
                else:
                    contributions[item.id] = None
            elif item.item_type == "attendance":
                if item.weight is not None:
                    absence = cell.absence_count if (cell and cell.absence_count is not None) else 0
                    contributions[item.id] = round(
                        max(0.0, item.weight - item.deduction_per_absence * absence), 2
                    )
                else:
                    contributions[item.id] = None
            elif item.item_type == "attitude":
                contributions[item.id] = (
                    round(cell.raw_score, 2) if cell and cell.raw_score is not None else None
                )

    return contributions


# ── 엔드포인트 ──────────────────────────────────────────────────

@router.get("/courses")
def list_student_courses(current_user: dict = Depends(student_only)):
    """학생의 수강 과목 목록을 학기별로 반환한다."""
    admin = get_admin_client()
    student_id = current_user["id"]

    # student_scores에서 수강 과목 ID 목록 추출
    scores_resp = (
        admin.table("student_scores")
        .select("course_id")
        .eq("student_id", student_id)
        .execute()
    )
    course_ids = list({r["course_id"] for r in (scores_resp.data or [])})
    if not course_ids:
        return {}

    # 과목 정보 로드
    courses_resp = (
        admin.table("courses")
        .select("id, course_name, course_code, section, semester")
        .in_("id", course_ids)
        .order("semester", desc=True)
        .execute()
    )
    courses = courses_resp.data or []

    # 총점·학점 정보 로드
    results_resp = (
        admin.table("grade_results")
        .select("course_id, total_score, grade")
        .in_("course_id", course_ids)
        .eq("student_id", student_id)
        .execute()
    )
    result_map = {r["course_id"]: r for r in (results_resp.data or [])}

    # 학기별 그룹화
    grouped: dict[str, list] = {}
    for c in courses:
        semester = c["semester"]
        result = result_map.get(c["id"])
        entry = {
            "id": c["id"],
            "course_name": c["course_name"],
            "course_code": c["course_code"],
            "section": c.get("section"),
            "total_score": float(result["total_score"]) if result and result.get("total_score") is not None else None,
            "grade": result["grade"] if result else None,
        }
        grouped.setdefault(semester, []).append(entry)

    return grouped


@router.get("/courses/{course_id}/scores")
def get_student_course_scores(
    course_id: str,
    current_user: dict = Depends(student_only),
):
    """항목별 점수·기여점수·총점·학점을 반환한다."""
    admin = get_admin_client()
    student_id = current_user["id"]

    # 수강 여부 확인 (본인 데이터만 접근)
    enroll_check = (
        admin.table("student_scores")
        .select("id")
        .eq("course_id", course_id)
        .eq("student_id", student_id)
        .limit(1)
        .execute()
    )
    if not enroll_check.data:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")

    # 성적 항목 로드
    items_resp = (
        admin.table("grade_items")
        .select("id, name, item_type, weight, group_id, deduction_per_absence")
        .eq("course_id", course_id)
        .order("display_order")
        .execute()
    )
    items_data = items_resp.data or []

    # 그룹 로드
    groups_resp = (
        admin.table("grade_item_groups")
        .select("id, name, weight")
        .eq("course_id", course_id)
        .execute()
    )
    groups_data = groups_resp.data or []

    # 학생 점수 로드
    scores_resp = (
        admin.table("student_scores")
        .select("grade_item_id, raw_score, absence_count")
        .eq("course_id", course_id)
        .eq("student_id", student_id)
        .execute()
    )
    score_map = {
        s["grade_item_id"]: ScoreCell(
            raw_score=s.get("raw_score"),
            absence_count=s.get("absence_count"),
        )
        for s in (scores_resp.data or [])
    }

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
    contributions = _compute_contributions(items, groups, score_map)

    # 결과 구성
    item_rows = []
    for item, item_data in zip(items, items_data):
        cell = score_map.get(item.id)
        group = next((g for g in groups_data if g["id"] == item.group_id), None)
        item_rows.append({
            "id": item.id,
            "name": item_data["name"],
            "item_type": item.item_type,
            "weight": item.weight,
            "group_id": item.group_id,
            "group_name": group["name"] if group else None,
            "group_weight": group["weight"] if group else None,
            "raw_score": cell.raw_score if cell else None,
            "absence_count": cell.absence_count if cell else None,
            "contribution": contributions.get(item.id),
        })

    # 총점·학점
    result_resp = (
        admin.table("grade_results")
        .select("total_score, grade")
        .eq("course_id", course_id)
        .eq("student_id", student_id)
        .execute()
    )
    grade_result = result_resp.data[0] if result_resp.data else None

    return {
        "course_id": course_id,
        "items": item_rows,
        "total_score": float(grade_result["total_score"]) if grade_result and grade_result.get("total_score") is not None else None,
        "grade": grade_result["grade"] if grade_result else None,
    }
