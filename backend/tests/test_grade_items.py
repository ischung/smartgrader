"""
성적 항목(GradeItem) CRUD API 테스트
"""
from fastapi.testclient import TestClient
from main import app
from models.grade_items import GradeItemCreate, GradeItemUpdate

client = TestClient(app)


def test_list_items_without_token():
    response = client.get("/api/v1/courses/some-id/items")
    assert response.status_code == 403


def test_create_item_without_token():
    response = client.post("/api/v1/courses/some-id/items", json={
        "name": "중간고사", "item_type": "general", "weight": 30
    })
    assert response.status_code == 403


def test_delete_item_without_token():
    response = client.delete("/api/v1/courses/some-id/items/item-id")
    assert response.status_code == 403


def test_grade_item_create_model_valid():
    item = GradeItemCreate(name="중간고사", item_type="general", weight=30.0)
    assert item.name == "중간고사"
    assert item.item_type == "general"
    assert item.weight == 30.0


def test_grade_item_create_invalid_type():
    from pydantic import ValidationError
    try:
        GradeItemCreate(name="테스트", item_type="invalid")
        assert False, "ValidationError 발생해야 함"
    except ValidationError:
        pass


def test_grade_item_weight_out_of_range():
    from pydantic import ValidationError
    try:
        GradeItemCreate(name="테스트", item_type="general", weight=150.0)
        assert False, "ValidationError 발생해야 함"
    except ValidationError:
        pass


def test_grade_item_update_model_partial():
    update = GradeItemUpdate(name="수정된 이름")
    data = update.model_dump(exclude_unset=True)
    assert "name" in data
    assert "weight" not in data


def test_grade_item_attendance_type():
    item = GradeItemCreate(
        name="출석",
        item_type="attendance",
        weight=10.0,
        deduction_per_absence=0.5,
    )
    assert item.item_type == "attendance"
    assert item.deduction_per_absence == 0.5


def test_grade_item_attitude_type():
    item = GradeItemCreate(
        name="태도",
        item_type="attitude",
        weight=10.0,
    )
    assert item.item_type == "attitude"
    assert item.weight == 10.0
