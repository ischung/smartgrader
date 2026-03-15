"""
총점 계산 로직 단위 테스트 — DB 없이 순수 함수 테스트
이슈 #17 예시 데이터로 86.00점 검증 포함
"""
from utils.grade_calculator import (
    ItemInfo, GroupInfo, ScoreCell,
    validate_weight_sum, calculate_student_total,
)


# ── 이슈 #17 예시 픽스처 ──────────────────────────────────────────
#
# 중간고사 (general, 25%): 80 × 0.25 = 20.00
# 기말고사 (general, 30%): 90 × 0.30 = 27.00
# 출석    (attendance, 10%, 결석 3회): max(0, 10 - 0.5×3) = 8.50
# 태도    (attitude, 5%): 4점 (직접 합산)
# 과제 그룹 (group, 20%, 항목 3개: 95/85/90): avg=90 × 0.20 = 18.00
# 프로젝트 그룹 (group, 10%, 항목 2개: 100/70): avg=85 × 0.10 = 8.50
# 총점 = 86.00
# ─────────────────────────────────────────────────────────────────

GROUP_ASSIGN_ID = "g-assign"
GROUP_PROJECT_ID = "g-project"

ITEMS = [
    ItemInfo(id="midterm", item_type="general",    weight=25.0, group_id=None),
    ItemInfo(id="final",   item_type="general",    weight=30.0, group_id=None),
    ItemInfo(id="attend",  item_type="attendance", weight=10.0, group_id=None, deduction_per_absence=0.5),
    ItemInfo(id="attitude",item_type="attitude",   weight=5.0,  group_id=None),
    ItemInfo(id="hw1",     item_type="general",    weight=None, group_id=GROUP_ASSIGN_ID),
    ItemInfo(id="hw2",     item_type="general",    weight=None, group_id=GROUP_ASSIGN_ID),
    ItemInfo(id="hw3",     item_type="general",    weight=None, group_id=GROUP_ASSIGN_ID),
    ItemInfo(id="proj1",   item_type="general",    weight=None, group_id=GROUP_PROJECT_ID),
    ItemInfo(id="proj2",   item_type="general",    weight=None, group_id=GROUP_PROJECT_ID),
]

GROUPS = [
    GroupInfo(id=GROUP_ASSIGN_ID,  weight=20.0),
    GroupInfo(id=GROUP_PROJECT_ID, weight=10.0),
]

SCORES: dict[str, ScoreCell] = {
    "midterm":  ScoreCell(raw_score=80.0),
    "final":    ScoreCell(raw_score=90.0),
    "attend":   ScoreCell(absence_count=3),
    "attitude": ScoreCell(raw_score=4.0),
    "hw1":      ScoreCell(raw_score=95.0),
    "hw2":      ScoreCell(raw_score=85.0),
    "hw3":      ScoreCell(raw_score=90.0),
    "proj1":    ScoreCell(raw_score=100.0),
    "proj2":    ScoreCell(raw_score=70.0),
}


def test_weight_sum_valid():
    """비그룹 항목 합(25+30+10+5=70) + 그룹 합(20+10=30) = 100"""
    assert validate_weight_sum(ITEMS, GROUPS) is True


def test_weight_sum_invalid():
    items = [ItemInfo(id="x", item_type="general", weight=50.0, group_id=None)]
    groups = [GroupInfo(id="g", weight=30.0)]
    assert validate_weight_sum(items, groups) is False


def test_weight_sum_no_groups():
    items = [
        ItemInfo(id="a", item_type="general", weight=60.0, group_id=None),
        ItemInfo(id="b", item_type="general", weight=40.0, group_id=None),
    ]
    assert validate_weight_sum(items, []) is True


def test_example_total_86():
    """이슈 #17 예시: 총점 86.00점"""
    total = calculate_student_total(SCORES, ITEMS, GROUPS)
    assert total == 86.00


def test_general_calculation():
    """general: raw_score × weight/100"""
    items = [ItemInfo(id="m", item_type="general", weight=100.0, group_id=None)]
    scores = {"m": ScoreCell(raw_score=75.0)}
    total = calculate_student_total(scores, items, [])
    assert total == 75.00


def test_attendance_no_absence():
    """attendance: 결석 0회 → weight 그대로"""
    items = [ItemInfo(id="a", item_type="attendance", weight=10.0, group_id=None)]
    scores = {"a": ScoreCell(absence_count=0)}
    total = calculate_student_total(scores, items, [])
    assert total == 10.00


def test_attendance_clamp_to_zero():
    """attendance: 결석 과다 → 음수가 되면 0으로 처리"""
    items = [ItemInfo(id="a", item_type="attendance", weight=5.0, group_id=None, deduction_per_absence=1.0)]
    scores = {"a": ScoreCell(absence_count=10)}
    total = calculate_student_total(scores, items, [])
    assert total == 0.00


def test_attitude_direct_sum():
    """attitude: raw_score 직접 합산 (× weight 없음)"""
    items = [ItemInfo(id="t", item_type="attitude", weight=10.0, group_id=None)]
    scores = {"t": ScoreCell(raw_score=7.5)}
    total = calculate_student_total(scores, items, [])
    assert total == 7.50


def test_group_average():
    """group: 그룹 내 평균 × group.weight/100"""
    items = [
        ItemInfo(id="i1", item_type="general", weight=None, group_id="g"),
        ItemInfo(id="i2", item_type="general", weight=None, group_id="g"),
    ]
    groups = [GroupInfo(id="g", weight=50.0)]
    scores = {
        "i1": ScoreCell(raw_score=80.0),
        "i2": ScoreCell(raw_score=100.0),
    }
    total = calculate_student_total(scores, items, groups)
    assert total == 45.00  # avg=90, 90×0.5=45


def test_missing_score_treated_as_zero_for_general():
    """general 점수 미입력 시 해당 항목 기여 0"""
    items = [
        ItemInfo(id="a", item_type="general", weight=50.0, group_id=None),
        ItemInfo(id="b", item_type="general", weight=50.0, group_id=None),
    ]
    scores = {"a": ScoreCell(raw_score=80.0)}  # b 미입력
    total = calculate_student_total(scores, items, [])
    assert total == 40.00  # a만 기여


def test_attendance_missing_absence_defaults_to_zero():
    """attendance 항목: absence_count 미입력 시 0으로 처리"""
    items = [ItemInfo(id="a", item_type="attendance", weight=10.0, group_id=None)]
    scores = {}  # 미입력
    total = calculate_student_total(scores, items, [])
    assert total == 10.00  # 결석 0회로 간주
