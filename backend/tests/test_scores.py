"""
점수 조회·수정·저장 API 테스트
"""
from fastapi.testclient import TestClient
from main import app
from models.scores import ScorePatch, ScoreCell

client = TestClient(app)


def test_get_scores_without_token():
    response = client.get("/api/v1/courses/some-id/scores")
    assert response.status_code == 403


def test_patch_scores_without_token():
    response = client.patch("/api/v1/courses/some-id/scores", json={
        "student_id": "uid", "grade_item_id": "item-id", "raw_score": 85
    })
    assert response.status_code == 403


def test_score_patch_model_valid():
    patch = ScorePatch(student_id="uid", grade_item_id="item", raw_score=85.0)
    assert patch.raw_score == 85.0
    assert patch.absence_count is None


def test_score_patch_raw_score_negative():
    from pydantic import ValidationError
    try:
        ScorePatch(student_id="uid", grade_item_id="item", raw_score=-1.0)
        assert False, "ValidationError 발생해야 함"
    except ValidationError:
        pass


def test_score_patch_absence_count_negative():
    from pydantic import ValidationError
    try:
        ScorePatch(student_id="uid", grade_item_id="item", absence_count=-1)
        assert False, "ValidationError 발생해야 함"
    except ValidationError:
        pass


def test_score_cell_empty():
    cell = ScoreCell()
    assert cell.raw_score is None
    assert cell.absence_count is None
    assert cell.id is None


def test_score_patch_attendance_model():
    """attendance는 absence_count만 사용"""
    patch = ScorePatch(student_id="uid", grade_item_id="item", absence_count=2)
    assert patch.absence_count == 2
    assert patch.raw_score is None


def test_score_patch_attitude_model():
    """attitude는 raw_score 사용"""
    patch = ScorePatch(student_id="uid", grade_item_id="item", raw_score=8.5)
    assert patch.raw_score == 8.5
