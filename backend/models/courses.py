import re
from typing import Optional
from pydantic import BaseModel, field_validator


SEMESTER_PATTERN = re.compile(r"^\d{4}-[12]$")


class CourseCreate(BaseModel):
    course_name: str
    course_code: str
    section: Optional[str] = None
    semester: str

    @field_validator("semester")
    @classmethod
    def validate_semester(cls, v: str) -> str:
        if not SEMESTER_PATTERN.match(v):
            raise ValueError("학기 형식은 YYYY-1 또는 YYYY-2 이어야 합니다.")
        return v


class CourseUpdate(BaseModel):
    course_name: Optional[str] = None
    course_code: Optional[str] = None
    section: Optional[str] = None
    semester: Optional[str] = None

    @field_validator("semester")
    @classmethod
    def validate_semester(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not SEMESTER_PATTERN.match(v):
            raise ValueError("학기 형식은 YYYY-1 또는 YYYY-2 이어야 합니다.")
        return v


class CourseResponse(BaseModel):
    id: str
    professor_id: str
    course_name: str
    course_code: str
    section: Optional[str]
    semester: str
