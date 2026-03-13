from fastapi import APIRouter, Depends, HTTPException, status
from models.grade_item_groups import GradeItemGroupCreate, GradeItemGroupUpdate, GradeItemGroupResponse, ItemGroupAssign
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


def _get_total_weight(admin, course_id: str, exclude_group_id: str | None = None) -> float:
    """
    과목의 전체 가중치 합계를 반환한다.
    전체 가중치 = 비그룹 항목 weight 합 + 그룹 weight 합
    exclude_group_id: 이 그룹은 합계에서 제외 (수정 시)
    """
    # 비그룹 항목 weight 합
    items_resp = (
        admin.table("grade_items")
        .select("weight")
        .eq("course_id", course_id)
        .is_("group_id", "null")
        .not_.is_("weight", "null")
        .execute()
    )
    items_sum = sum(float(r["weight"]) for r in (items_resp.data or []))

    # 그룹 weight 합
    groups_query = admin.table("grade_item_groups").select("weight").eq("course_id", course_id)
    if exclude_group_id:
        groups_query = groups_query.neq("id", exclude_group_id)
    groups_resp = groups_query.execute()
    groups_sum = sum(float(r["weight"]) for r in (groups_resp.data or []))

    return items_sum + groups_sum


@router.get("/{course_id}/groups", response_model=list[GradeItemGroupResponse])
def list_groups(
    course_id: str,
    current_user: dict = Depends(professor_or_admin),
):
    admin = get_admin_client()
    _get_course_or_404(admin, course_id, current_user["id"])

    result = admin.table("grade_item_groups").select("*").eq("course_id", course_id).execute()
    return result.data or []


@router.post("/{course_id}/groups", response_model=GradeItemGroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    course_id: str,
    body: GradeItemGroupCreate,
    current_user: dict = Depends(professor_or_admin),
):
    admin = get_admin_client()
    _get_course_or_404(admin, course_id, current_user["id"])

    total = _get_total_weight(admin, course_id)
    if total + body.weight > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"가중치 합계가 100%를 초과합니다. 현재 합계: {total}%",
        )

    result = admin.table("grade_item_groups").insert({
        "course_id": course_id,
        "name": body.name,
        "weight": body.weight,
    }).execute()
    return result.data[0]


@router.patch("/{course_id}/groups/{group_id}", response_model=GradeItemGroupResponse)
def update_group(
    course_id: str,
    group_id: str,
    body: GradeItemGroupUpdate,
    current_user: dict = Depends(professor_or_admin),
):
    admin = get_admin_client()
    _get_course_or_404(admin, course_id, current_user["id"])

    existing = (
        admin.table("grade_item_groups")
        .select("*")
        .eq("id", group_id)
        .eq("course_id", course_id)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="그룹을 찾을 수 없습니다.")

    patch_data = body.model_dump(exclude_unset=True)

    if "weight" in patch_data:
        total = _get_total_weight(admin, course_id, exclude_group_id=group_id)
        if total + patch_data["weight"] > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"가중치 합계가 100%를 초과합니다. 현재 합계(이 그룹 제외): {total}%",
            )

    if not patch_data:
        return existing.data[0]

    result = (
        admin.table("grade_item_groups")
        .update(patch_data)
        .eq("id", group_id)
        .execute()
    )
    return result.data[0]


@router.delete("/{course_id}/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    course_id: str,
    group_id: str,
    current_user: dict = Depends(professor_or_admin),
):
    admin = get_admin_client()
    _get_course_or_404(admin, course_id, current_user["id"])

    existing = (
        admin.table("grade_item_groups")
        .select("id")
        .eq("id", group_id)
        .eq("course_id", course_id)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="그룹을 찾을 수 없습니다.")

    # DB ON DELETE SET NULL이 자동으로 소속 항목의 group_id를 NULL로 설정
    admin.table("grade_item_groups").delete().eq("id", group_id).execute()


@router.patch("/{course_id}/items/{item_id}/group", status_code=status.HTTP_200_OK)
def assign_item_to_group(
    course_id: str,
    item_id: str,
    body: ItemGroupAssign,
    current_user: dict = Depends(professor_or_admin),
):
    """
    항목을 그룹에 추가하거나 그룹에서 해제한다.
    그룹에 추가 시 해당 항목의 weight는 NULL로 설정된다.
    """
    admin = get_admin_client()
    _get_course_or_404(admin, course_id, current_user["id"])

    existing = (
        admin.table("grade_items")
        .select("*")
        .eq("id", item_id)
        .eq("course_id", course_id)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="성적 항목을 찾을 수 없습니다.")

    if body.group_id is not None:
        # 그룹 존재 확인
        group = (
            admin.table("grade_item_groups")
            .select("id")
            .eq("id", body.group_id)
            .eq("course_id", course_id)
            .execute()
        )
        if not group.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="그룹을 찾을 수 없습니다.")
        # 그룹 소속 항목은 weight = NULL
        patch = {"group_id": body.group_id, "weight": None}
    else:
        # 그룹 해제
        patch = {"group_id": None}

    result = admin.table("grade_items").update(patch).eq("id", item_id).execute()
    return result.data[0]
