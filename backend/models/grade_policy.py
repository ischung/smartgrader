from typing import Optional
from pydantic import BaseModel, Field, model_validator


# 허용 학점 목록
VALID_GRADES = {"A+", "A0", "B+", "B0", "C+", "C0", "D+", "D0", "F"}


class GradePolicyEntry(BaseModel):
    grade: str = Field(..., description="A+, A0, B+, B0, C+, C0, D+, D0, F 중 하나")
    min_score: float = Field(..., ge=0, le=100)
    max_score: float = Field(..., ge=0, le=100)

    @model_validator(mode="after")
    def check_range(self):
        if self.min_score > self.max_score:
            raise ValueError("min_score는 max_score보다 클 수 없습니다.")
        if self.grade not in VALID_GRADES:
            raise ValueError(f"유효하지 않은 학점: {self.grade}. 허용: {VALID_GRADES}")
        return self


class GradePolicyPut(BaseModel):
    entries: list[GradePolicyEntry]

    @model_validator(mode="after")
    def check_no_overlap(self):
        sorted_entries = sorted(self.entries, key=lambda e: e.min_score)
        for i in range(len(sorted_entries) - 1):
            a = sorted_entries[i]
            b = sorted_entries[i + 1]
            if a.max_score >= b.min_score:
                raise ValueError(
                    f"학점 범위가 겹칩니다: {a.grade}({a.min_score}~{a.max_score}) "
                    f"와 {b.grade}({b.min_score}~{b.max_score})"
                )
        return self


class GradePolicyEntryResponse(BaseModel):
    id: str
    course_id: str
    grade: str
    min_score: float
    max_score: float


class GradeResultResponse(BaseModel):
    student_id: str
    login_id: Optional[str]
    name: Optional[str]
    total_score: float
    grade: Optional[str]
