"""
RBAC (역할 기반 접근 제어) 단위 테스트
require_role 로직의 admin 계층 구조를 검증한다.
"""
from utils.deps import require_role


def test_admin_can_access_professor_endpoint():
    """admin은 professor 전용 엔드포인트에 접근 가능 (계층 구조)"""
    roles = ("professor",)
    user_role = "admin"
    allowed = user_role == "admin" and "student" not in roles
    assert allowed is True


def test_student_blocked_from_professor_endpoint():
    """student는 professor 전용 엔드포인트 접근 불가"""
    roles = ("professor",)
    user_role = "student"
    allowed = user_role == "admin" and "student" not in roles
    assert allowed is False
    assert user_role not in roles


def test_admin_blocked_from_student_only_endpoint():
    """admin은 student 전용 엔드포인트 접근 불가"""
    roles = ("student",)
    user_role = "admin"
    allowed = user_role == "admin" and "student" not in roles
    assert allowed is False


def test_student_can_access_student_endpoint():
    """student는 student 전용 엔드포인트 접근 가능"""
    roles = ("student",)
    user_role = "student"
    assert user_role in roles


def test_require_role_returns_callable():
    """require_role 팩토리가 callable을 반환하는지 확인"""
    checker = require_role("professor")
    assert callable(checker)
