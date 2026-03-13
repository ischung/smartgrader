from pydantic import BaseModel
from typing import Optional


class ProfessorCreate(BaseModel):
    login_id: str
    name: str
    password: str


class ProfessorUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None


class ProfessorResponse(BaseModel):
    id: str
    login_id: str
    name: str
    role: str
