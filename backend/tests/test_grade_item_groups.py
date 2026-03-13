"""
성적 항목 그룹(GradeItemGroup) CRUD API 테스트
"""
from fastapi.testclient import TestClient
from main import app
from models.grade_item_groups import GradeItemGroupCreate, GradeItemGroupUpdate, ItemGroupAssign

client = TestClient(app)


def test_list_groups_without_token():
    response = client.get("/api/v1/courses/some-id/groups")
    assert response.status_code == 403


def test_create_group_without_token():
    response = client.post("/api/v1/courses/some-id/groups", json={"name": "과제", "weight": 30})
    assert response.status_code == 403


def test_assign_item_group_without_token():
    response = client.patch("/api/v1/courses/some-id/items/item-id/group", json={"group_id": None})
    assert response.status_code == 403


def test_group_create_model_valid():
    group = GradeItemGroupCreate(name="과제 그룹", weight=30.0)
    assert group.name == "과제 그룹"
    assert group.weight == 30.0


def test_group_weight_out_of_range():
    from pydantic import ValidationError
    try:
        GradeItemGroupCreate(name="그룹", weight=110.0)
        assert False, "ValidationError 발생해야 함"
    except ValidationError:
        pass


def test_group_weight_negative():
    from pydantic import ValidationError
    try:
        GradeItemGroupCreate(name="그룹", weight=-5.0)
        assert False, "ValidationError 발생해야 함"
    except ValidationError:
        pass


def test_group_update_partial():
    update = GradeItemGroupUpdate(name="수정된 그룹명")
    data = update.model_dump(exclude_unset=True)
    assert "name" in data
    assert "weight" not in data


def test_item_group_assign_none_is_valid():
    """group_id=None이면 그룹 해제"""
    assign = ItemGroupAssign(group_id=None)
    assert assign.group_id is None


def test_item_group_assign_with_id():
    assign = ItemGroupAssign(group_id="some-uuid")
    assert assign.group_id == "some-uuid"
