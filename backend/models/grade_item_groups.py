from typing import Optional
from pydantic import BaseModel, Field


class GradeItemGroupCreate(BaseModel):
    name: str = Field(..., max_length=100)
    weight: float = Field(..., ge=0, le=100)


class GradeItemGroupUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    weight: Optional[float] = Field(None, ge=0, le=100)


class GradeItemGroupResponse(BaseModel):
    id: str
    course_id: str
    name: str
    weight: float


class ItemGroupAssign(BaseModel):
    group_id: Optional[str] = None  # None이면 그룹 해제
