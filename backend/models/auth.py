from pydantic import BaseModel


class LoginRequest(BaseModel):
    login_id: str
    password: str


class LoginResponse(BaseModel):
    token: str
    role: str
    user: dict


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
