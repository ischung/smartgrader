"""
총점 계산 순수 로직 (Pure functions — DB 호출 없음)

계산 규칙:
  general  (비그룹): raw_score × (weight / 100)
  attendance(비그룹): max(0, weight - deduction_per_absence × absence_count)
  attitude (비그룹): raw_score (직접 합산, 범위 0~weight)
  group 소속 항목:   그룹 내 raw_score 평균 × (group.weight / 100)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ItemInfo:
    id: str
    item_type: str          # 'general' | 'attendance' | 'attitude'
    weight: Optional[float] # 비그룹 항목만 설정 — 그룹 소속이면 None
    group_id: Optional[str]
    deduction_per_absence: float = 0.5


@dataclass
class GroupInfo:
    id: str
    weight: float


@dataclass
class ScoreCell:
    raw_score: Optional[float] = None
    absence_count: Optional[int] = None


def validate_weight_sum(items: list[ItemInfo], groups: list[GroupInfo]) -> bool:
    """
    비그룹 항목 weight 합 + 그룹 weight 합 = 100 인지 검증한다.
    부동소수점 허용 오차: ±0.01
    """
    non_grouped_sum = sum(i.weight for i in items if i.group_id is None and i.weight is not None)
    group_sum = sum(g.weight for g in groups)
    total = non_grouped_sum + group_sum
    return abs(total - 100.0) < 0.01


def calculate_student_total(
    student_scores: dict[str, ScoreCell],  # item_id → ScoreCell
    items: list[ItemInfo],
    groups: list[GroupInfo],
) -> float:
    """
    학생 1명의 총점을 계산한다.

    Args:
        student_scores: 항목별 점수 (미입력 항목은 포함되지 않을 수 있음)
        items: 과목의 전체 성적 항목 목록
        groups: 과목의 전체 그룹 목록

    Returns:
        총점 (float)
    """
    group_map = {g.id: g for g in groups}

    # 그룹별 소속 항목 묶기
    group_items: dict[str, list[ItemInfo]] = {g.id: [] for g in groups}
    non_group_items: list[ItemInfo] = []

    for item in items:
        if item.group_id and item.group_id in group_map:
            group_items[item.group_id].append(item)
        else:
            non_group_items.append(item)

    total = 0.0

    # 1. 비그룹 항목 계산
    for item in non_group_items:
        cell = student_scores.get(item.id)
        if item.item_type == "general":
            if cell and cell.raw_score is not None and item.weight is not None:
                total += cell.raw_score * (item.weight / 100.0)
        elif item.item_type == "attendance":
            if item.weight is not None:
                absence = cell.absence_count if (cell and cell.absence_count is not None) else 0
                total += max(0.0, item.weight - item.deduction_per_absence * absence)
        elif item.item_type == "attitude":
            if cell and cell.raw_score is not None:
                total += cell.raw_score

    # 2. 그룹 항목 계산 (그룹 내 raw_score 평균 × group.weight/100)
    for group in groups:
        g_items = group_items.get(group.id, [])
        raw_scores = []
        for item in g_items:
            cell = student_scores.get(item.id)
            if cell and cell.raw_score is not None:
                raw_scores.append(cell.raw_score)
        if raw_scores:
            avg = sum(raw_scores) / len(raw_scores)
            total += avg * (group.weight / 100.0)

    return round(total, 2)
