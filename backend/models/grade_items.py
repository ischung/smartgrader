from typing import Optional
from pydantic import BaseModel, Field


class GradeItemCreate(BaseModel):
    name: str = Field(..., max_length=100)
    item_type: str = Field(..., pattern="^(general|attendance|attitude)$")
    weight: Optional[float] = Field(None, ge=0, le=100)
    group_id: Optional[str] = None
    deduction_per_absence: Optional[float] = Field(None, ge=0)
    display_order: int = 0


class GradeItemUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    item_type: Optional[str] = Field(None, pattern="^(general|attendance|attitude)$")
    weight: Optional[float] = Field(None, ge=0, le=100)
    group_id: Optional[str] = None
    deduction_per_absence: Optional[float] = Field(None, ge=0)
    display_order: Optional[int] = None


class GradeItemResponse(BaseModel):
    id: str
    course_id: str
    group_id: Optional[str]
    name: str
    item_type: str
    weight: Optional[float]
    deduction_per_absence: Optional[float]
    display_order: int
