from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .supabase_client import get_admin_client

bearer = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
):
    """Bearer 토큰 검증 → {id, login_id, role} 반환"""
    token = credentials.credentials
    admin = get_admin_client()

    try:
        user_resp = admin.auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 토큰입니다.")

    if not user_resp or not user_resp.user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 토큰입니다.")

    uid = user_resp.user.id
    row = admin.table("users").select("login_id, name, role").eq("id", uid).single().execute()

    if not row.data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="사용자 정보를 찾을 수 없습니다.")

    return {"id": uid, **row.data}


def require_role(*roles: str):
    """역할 기반 접근 제어 팩토리"""
    def checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        return current_user
    return checker
