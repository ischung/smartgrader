from fastapi import APIRouter, Depends, HTTPException, status
from models.grade_items import GradeItemCreate, GradeItemUpdate, GradeItemResponse
from utils.deps import require_role
from utils.supabase_client import get_admin_client

router = APIRouter()

professor_or_admin = require_role("professor")


def _get_course_or_404(admin, course_id: str, professor_id: str):
    """과목 소유권 확인 — 없으면 404"""
    result = (
        admin.table("courses")
        .select("id")
        .eq("id", course_id)
        .eq("professor_id", professor_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="과목을 찾을 수 없습니다.")


def _get_weight_sum(admin, course_id: str, exclude_item_id: str | None = None) -> float:
    """
    그룹에 속하지 않는 항목들의 가중치 합계를 반환한다.
    exclude_item_id를 지정하면 해당 항목은 합계에서 제외한다 (수정 시 사용).
    """
    query = (
        admin.table("grade_items")
        .select("weight")
        .eq("course_id", course_id)
        .is_("group_id", "null")
        .not_.is_("weight", "null")
    )
    if exclude_item_id:
        query = query.neq("id", exclude_item_id)
    result = query.execute()
    return sum(float(row["weight"]) for row in (result.data or []))


@router.get("/{course_id}/items", response_model=list[GradeItemResponse])
def list_grade_items(
    course_id: str,
    current_user: dict = Depends(professor_or_admin),
):
    admin = get_admin_client()
    _get_course_or_404(admin, course_id, current_user["id"])

    result = (
        admin.table("grade_items")
        .select("*")
        .eq("course_id", course_id)
        .order("display_order")
        .execute()
    )
    return result.data or []


@router.post("/{course_id}/items", response_model=GradeItemResponse, status_code=status.HTTP_201_CREATED)
def create_grade_item(
    course_id: str,
    body: GradeItemCreate,
    current_user: dict = Depends(professor_or_admin),
):
    admin = get_admin_client()
    _get_course_or_404(admin, course_id, current_user["id"])

    # 그룹 미소속 항목의 가중치 합계 검증
    if body.weight is not None and body.group_id is None:
        current_sum = _get_weight_sum(admin, course_id)
        if current_sum + body.weight > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"가중치 합계가 100%를 초과합니다. 현재 합계: {current_sum}%",
            )

    data = {
        "course_id": course_id,
        "name": body.name,
        "item_type": body.item_type,
        "display_order": body.display_order,
    }
    if body.weight is not None:
        data["weight"] = body.weight
    if body.group_id is not None:
        data["group_id"] = body.group_id
    if body.deduction_per_absence is not None:
        data["deduction_per_absence"] = body.deduction_per_absence

    result = admin.table("grade_items").insert(data).execute()
    return result.data[0]


@router.patch("/{course_id}/items/{item_id}", response_model=GradeItemResponse)
def update_grade_item(
    course_id: str,
    item_id: str,
    body: GradeItemUpdate,
    current_user: dict = Depends(professor_or_admin),
):
    admin = get_admin_client()
    _get_course_or_404(admin, course_id, current_user["id"])

    # 항목 존재 확인
    existing = (
        admin.table("grade_items")
        .select("*")
        .eq("id", item_id)
        .eq("course_id", course_id)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="성적 항목을 찾을 수 없습니다.")

    current_item = existing.data[0]
    new_group_id = body.group_id if body.group_id is not None else current_item.get("group_id")
    new_weight = body.weight if body.weight is not None else current_item.get("weight")

    # 가중치 합계 재검증 (그룹 미소속이고 weight 변경 시)
    if new_weight is not None and new_group_id is None:
        current_sum = _get_weight_sum(admin, course_id, exclude_item_id=item_id)
        if current_sum + new_weight > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"가중치 합계가 100%를 초과합니다. 현재 합계(이 항목 제외): {current_sum}%",
            )

    patch_data = {k: v for k, v in body.model_dump(exclude_unset=True).items()}
    if not patch_data:
        return current_item

    result = (
        admin.table("grade_items")
        .update(patch_data)
        .eq("id", item_id)
        .execute()
    )
    return result.data[0]


@router.delete("/{course_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_grade_item(
    course_id: str,
    item_id: str,
    current_user: dict = Depends(professor_or_admin),
):
    admin = get_admin_client()
    _get_course_or_404(admin, course_id, current_user["id"])

    existing = (
        admin.table("grade_items")
        .select("id")
        .eq("id", item_id)
        .eq("course_id", course_id)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="성적 항목을 찾을 수 없습니다.")

    admin.table("grade_items").delete().eq("id", item_id).execute()
