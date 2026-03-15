"""
학점 범위 설정 및 학점 산출 API 테스트
"""
from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest
from main import app
from models.grade_policy import GradePolicyEntry, GradePolicyPut
from routers.grade_policy import _assign_grade

client = TestClient(app)


def test_get_policy_without_token():
    response = client.get("/api/v1/courses/some-id/policy")
    assert response.status_code == 403


def test_put_policy_without_token():
    response = client.put("/api/v1/courses/some-id/policy", json={"entries": []})
    assert response.status_code == 403


def test_calculate_grades_without_token():
    response = client.post("/api/v1/courses/some-id/grades/calculate")
    assert response.status_code == 403


def test_policy_entry_valid():
    entry = GradePolicyEntry(grade="A+", min_score=95.0, max_score=100.0)
    assert entry.grade == "A+"
    assert entry.min_score == 95.0


def test_policy_entry_invalid_grade():
    with pytest.raises(ValidationError):
        GradePolicyEntry(grade="Z", min_score=90.0, max_score=100.0)


def test_policy_entry_min_greater_than_max():
    with pytest.raises(ValidationError):
        GradePolicyEntry(grade="A+", min_score=100.0, max_score=80.0)


def test_policy_no_overlap():
    """겹치지 않는 구간 — 정상"""
    policy = GradePolicyPut(entries=[
        GradePolicyEntry(grade="A+", min_score=95.0, max_score=100.0),
        GradePolicyEntry(grade="A0", min_score=90.0, max_score=94.9),
        GradePolicyEntry(grade="F",  min_score=0.0,  max_score=59.9),
    ])
    assert len(policy.entries) == 3


def test_policy_overlap_raises():
    """겹치는 구간 — ValidationError"""
    with pytest.raises(ValidationError):
        GradePolicyPut(entries=[
            GradePolicyEntry(grade="A+", min_score=90.0, max_score=100.0),
            GradePolicyEntry(grade="A0", min_score=85.0, max_score=95.0),  # 겹침
        ])


# ── _assign_grade 단위 테스트 ─────────────────────────────────────

SAMPLE_POLICY = [
    GradePolicyEntry(grade="A+", min_score=95.0, max_score=100.0),
    GradePolicyEntry(grade="A0", min_score=90.0, max_score=94.9),
    GradePolicyEntry(grade="B+", min_score=85.0, max_score=89.9),
    GradePolicyEntry(grade="F",  min_score=0.0,  max_score=59.9),
]


def test_assign_grade_hit():
    assert _assign_grade(96.0, SAMPLE_POLICY) == "A+"
    assert _assign_grade(90.0, SAMPLE_POLICY) == "A0"
    assert _assign_grade(85.0, SAMPLE_POLICY) == "B+"


def test_assign_grade_no_match_returns_f():
    """정책 범위에 없으면 F"""
    assert _assign_grade(70.0, SAMPLE_POLICY) == "F"


def test_assign_grade_boundary():
    """경계값 포함 (min_score ≤ total ≤ max_score)"""
    assert _assign_grade(95.0, SAMPLE_POLICY) == "A+"
    assert _assign_grade(100.0, SAMPLE_POLICY) == "A+"
    assert _assign_grade(59.9, SAMPLE_POLICY) == "F"


def test_assign_grade_empty_policy():
    """정책이 없으면 항상 F"""
    assert _assign_grade(100.0, []) == "F"
