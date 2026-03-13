"""
교수 계정 CRUD API 테스트 (mock 기반)
"""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_list_professors_without_token():
    response = client.get("/api/v1/users/professors")
    assert response.status_code == 403


def test_create_professor_without_token():
    response = client.post("/api/v1/users/professors", json={
        "login_id": "prof01", "name": "홍길동", "password": "pass123"
    })
    assert response.status_code == 403


def test_delete_professor_without_token():
    response = client.delete("/api/v1/users/professors/some-uuid")
    assert response.status_code == 403


def test_update_professor_without_token():
    response = client.patch("/api/v1/users/professors/some-uuid", json={"name": "새이름"})
    assert response.status_code == 403


def test_create_professor_missing_fields():
    response = client.post("/api/v1/users/professors", json={})
    assert response.status_code == 403  # 인증이 스키마 검증보다 먼저
