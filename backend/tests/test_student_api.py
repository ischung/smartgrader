"""
학생 수강 과목 목록 및 성적 조회 API 테스트
"""
from fastapi.testclient import TestClient
from main import app
from utils.grade_calculator import ItemInfo, GroupInfo, ScoreCell
from routers.student import _compute_contributions

client = TestClient(app)


def test_list_courses_without_token():
    response = client.get("/api/v1/student/courses")
    assert response.status_code == 403


def test_get_scores_without_token():
    response = client.get("/api/v1/student/courses/some-id/scores")
    assert response.status_code == 403


# ── _compute_contributions 단위 테스트 ───────────────────────────

def _make_items_groups():
    """이슈 #17 예시와 동일한 픽스처"""
    G1, G2 = "g-assign", "g-project"
    items = [
        ItemInfo(id="midterm",  item_type="general",    weight=25.0, group_id=None),
        ItemInfo(id="final",    item_type="general",    weight=30.0, group_id=None),
        ItemInfo(id="attend",   item_type="attendance", weight=10.0, group_id=None, deduction_per_absence=0.5),
        ItemInfo(id="attitude", item_type="attitude",   weight=5.0,  group_id=None),
        ItemInfo(id="hw1",      item_type="general",    weight=None, group_id=G1),
        ItemInfo(id="hw2",      item_type="general",    weight=None, group_id=G1),
        ItemInfo(id="hw3",      item_type="general",    weight=None, group_id=G1),
        ItemInfo(id="proj1",    item_type="general",    weight=None, group_id=G2),
        ItemInfo(id="proj2",    item_type="general",    weight=None, group_id=G2),
    ]
    groups = [
        GroupInfo(id=G1, weight=20.0),
        GroupInfo(id=G2, weight=10.0),
    ]
    return items, groups


def test_contribution_general():
    items, groups = _make_items_groups()
    scores = {"midterm": ScoreCell(raw_score=80.0)}
    c = _compute_contributions(items, groups, scores)
    assert c["midterm"] == 20.0   # 80 × 0.25


def test_contribution_attendance():
    items, groups = _make_items_groups()
    scores = {"attend": ScoreCell(absence_count=3)}
    c = _compute_contributions(items, groups, scores)
    assert c["attend"] == 8.5   # max(0, 10 - 0.5×3)


def test_contribution_attendance_clamp():
    items, groups = _make_items_groups()
    scores = {"attend": ScoreCell(absence_count=100)}
    c = _compute_contributions(items, groups, scores)
    assert c["attend"] == 0.0


def test_contribution_attitude():
    items, groups = _make_items_groups()
    scores = {"attitude": ScoreCell(raw_score=4.0)}
    c = _compute_contributions(items, groups, scores)
    assert c["attitude"] == 4.0


def test_contribution_group_items():
    """그룹 항목: raw_score / n × group_weight/100"""
    items, groups = _make_items_groups()
    scores = {
        "hw1": ScoreCell(raw_score=95.0),
        "hw2": ScoreCell(raw_score=85.0),
        "hw3": ScoreCell(raw_score=90.0),
    }
    c = _compute_contributions(items, groups, scores)
    # 각 항목 기여 = raw_score / 3 × 0.20
    assert c["hw1"] == round(95.0 / 3 * 0.20, 2)
    assert c["hw2"] == round(85.0 / 3 * 0.20, 2)
    assert c["hw3"] == round(90.0 / 3 * 0.20, 2)
    # 합산 = group_avg × 0.20 = 90 × 0.20 = 18.0
    assert round(c["hw1"] + c["hw2"] + c["hw3"], 2) == 18.0


def test_contribution_missing_score_is_none():
    items, groups = _make_items_groups()
    scores = {}
    c = _compute_contributions(items, groups, scores)
    assert c["midterm"] is None
    assert c["hw1"] is None


def test_contribution_attendance_no_score_defaults_full():
    """attendance 미입력 → 결석 0 → weight 전체"""
    items, groups = _make_items_groups()
    scores = {}
    c = _compute_contributions(items, groups, scores)
    assert c["attend"] == 10.0
