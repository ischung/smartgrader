from fastapi import APIRouter, Depends, HTTPException, status
from models.auth import LoginRequest, LoginResponse, PasswordChangeRequest
from utils.deps import get_current_user
from utils.supabase_client import get_admin_client, get_anon_client

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    admin = get_admin_client()

    # 1. login_id → public.users에서 UUID + role 조회
    row = admin.table("users").select("id, login_id, name, role").eq("login_id", body.login_id).single().execute()
    if not row.data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="아이디 또는 비밀번호가 올바르지 않아요.")

    user_data = row.data

    # 2. UUID → auth.users에서 email 조회
    auth_user = admin.auth.admin.get_user_by_id(user_data["id"])
    if not auth_user or not auth_user.user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="아이디 또는 비밀번호가 올바르지 않아요.")

    email = auth_user.user.email

    # 3. email + password로 Supabase Auth 로그인
    anon = get_anon_client()
    try:
        session = anon.auth.sign_in_with_password({"email": email, "password": body.password})
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="아이디 또는 비밀번호가 올바르지 않아요.")

    if not session or not session.session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="아이디 또는 비밀번호가 올바르지 않아요.")

    return LoginResponse(
        token=session.session.access_token,
        role=user_data["role"],
        user={
            "id": user_data["id"],
            "login_id": user_data["login_id"],
            "name": user_data["name"],
        },
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout():
    # 클라이언트 측 토큰 삭제로 충분 (Supabase JWT는 stateless)
    return


@router.patch("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    body: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user),
):
    admin = get_admin_client()
    anon = get_anon_client()

    # 1. 현재 PW 확인 — 실제로 로그인 시도
    auth_user = admin.auth.admin.get_user_by_id(current_user["id"])
    if not auth_user or not auth_user.user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="사용자 정보를 찾을 수 없습니다.")

    email = auth_user.user.email
    try:
        anon.auth.sign_in_with_password({"email": email, "password": body.current_password})
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="현재 비밀번호가 올바르지 않아요.")

    # 2. 새 PW로 업데이트
    try:
        admin.auth.admin.update_user_by_id(current_user["id"], {"password": body.new_password})
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="비밀번호 변경에 실패했습니다.")

    return
