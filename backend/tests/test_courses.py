"""
과목 CRUD API 테스트
"""
from fastapi.testclient import TestClient
from main import app
from models.courses import CourseCreate

client = TestClient(app)


def test_list_courses_without_token():
    response = client.get("/api/v1/courses")
    assert response.status_code == 403


def test_create_course_without_token():
    response = client.post("/api/v1/courses", json={
        "course_name": "소프트웨어공학", "course_code": "CS101",
        "semester": "2026-1"
    })
    assert response.status_code == 403


def test_delete_course_without_token():
    response = client.delete("/api/v1/courses/some-uuid")
    assert response.status_code == 403


def test_semester_valid():
    model = CourseCreate(course_name="테스트", course_code="CS101", semester="2026-1")
    assert model.semester == "2026-1"


def test_semester_valid_second():
    model = CourseCreate(course_name="테스트", course_code="CS101", semester="2026-2")
    assert model.semester == "2026-2"


def test_semester_invalid_format():
    from pydantic import ValidationError
    try:
        CourseCreate(course_name="테스트", course_code="CS101", semester="2026-3")
        assert False, "ValidationError 발생해야 함"
    except ValidationError:
        pass


def test_semester_invalid_no_dash():
    from pydantic import ValidationError
    try:
        CourseCreate(course_name="테스트", course_code="CS101", semester="20261")
        assert False, "ValidationError 발생해야 함"
    except ValidationError:
        pass
