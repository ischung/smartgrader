from typing import Optional
from pydantic import BaseModel, Field


class ScorePatch(BaseModel):
    student_id: str
    grade_item_id: str
    raw_score: Optional[float] = Field(None, ge=0)
    absence_count: Optional[int] = Field(None, ge=0)


class ScoreCell(BaseModel):
    id: Optional[str] = None
    raw_score: Optional[float] = None
    absence_count: Optional[int] = None


class StudentScoreRow(BaseModel):
    id: str
    name: str
    login_id: str
    scores: dict[str, ScoreCell]  # grade_item_id → ScoreCell


class GradeItemInfo(BaseModel):
    id: str
    name: str
    item_type: str
    weight: Optional[float]
    display_order: int


class ScoreTableResponse(BaseModel):
    items: list[GradeItemInfo]
    students: list[StudentScoreRow]
