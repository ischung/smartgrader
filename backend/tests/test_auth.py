"""
Auth API 테스트 — 실제 Supabase 없이 구조 검증
"""
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_login_missing_fields():
    """필드 누락 시 422 반환"""
    response = client.post("/api/v1/auth/login", json={})
    assert response.status_code == 422


def test_login_wrong_credentials():
    """잘못된 login_id → 401 반환"""
    mock_admin = MagicMock()
    mock_admin.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None

    with patch("routers.auth.get_admin_client", return_value=mock_admin):
        response = client.post("/api/v1/auth/login", json={"login_id": "wrong", "password": "wrong"})

    assert response.status_code == 401


def test_logout():
    """로그아웃 204 반환"""
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 204


def test_protected_without_token():
    """토큰 없이 보호된 API 호출 시 403 반환"""
    response = client.get("/api/v1/users/me")
    assert response.status_code in (401, 403, 404)


def test_change_password_without_token():
    """토큰 없이 비밀번호 변경 시 403 반환"""
    response = client.patch(
        "/api/v1/auth/password",
        json={"current_password": "old", "new_password": "new"},
    )
    assert response.status_code == 403


def test_change_password_missing_fields():
    """토큰 없이 필드 누락 시 403 반환 (인증이 스키마 검증보다 먼저)"""
    response = client.patch("/api/v1/auth/password", json={})
    assert response.status_code == 403
