from fastapi import APIRouter, Depends, HTTPException, status
from models.users import ProfessorCreate, ProfessorUpdate, ProfessorResponse
from utils.deps import require_role
from utils.supabase_client import get_admin_client

router = APIRouter()

admin_only = require_role("admin")


@router.get("/professors", response_model=list[ProfessorResponse])
def list_professors(current_user: dict = Depends(admin_only)):
    admin = get_admin_client()
    result = admin.table("users").select("id, login_id, name, role").eq("role", "professor").execute()
    return result.data


@router.post("/professors", response_model=ProfessorResponse, status_code=status.HTTP_201_CREATED)
def create_professor(body: ProfessorCreate, current_user: dict = Depends(admin_only)):
    admin = get_admin_client()

    # 중복 login_id 확인
    existing = admin.table("users").select("id").eq("login_id", body.login_id).execute()
    if existing.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 사용 중인 아이디입니다.")

    # Supabase Auth 계정 생성
    email = f"{body.login_id}@smartgrader.local"
    try:
        auth_result = admin.auth.admin.create_user({
            "email": email,
            "password": body.password,
            "email_confirm": True,
        })
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="계정 생성에 실패했습니다.")

    uid = auth_result.user.id

    # public.users 삽입
    try:
        row = admin.table("users").insert({
            "id": uid,
            "login_id": body.login_id,
            "name": body.name,
            "role": "professor",
        }).execute()
    except Exception:
        # Auth 계정 롤백
        admin.auth.admin.delete_user(uid)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="사용자 정보 저장에 실패했습니다.")

    return row.data[0]


@router.patch("/professors/{professor_id}", response_model=ProfessorResponse)
def update_professor(
    professor_id: str,
    body: ProfessorUpdate,
    current_user: dict = Depends(admin_only),
):
    admin = get_admin_client()

    # 존재 여부 확인
    existing = admin.table("users").select("id").eq("id", professor_id).eq("role", "professor").execute()
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="교수를 찾을 수 없습니다.")

    # users 테이블 업데이트
    update_data = {}
    if body.name is not None:
        update_data["name"] = body.name

    if update_data:
        admin.table("users").update(update_data).eq("id", professor_id).execute()

    # Auth 비밀번호 업데이트
    if body.password is not None:
        admin.auth.admin.update_user_by_id(professor_id, {"password": body.password})

    result = admin.table("users").select("id, login_id, name, role").eq("id", professor_id).single().execute()
    return result.data


@router.delete("/professors/{professor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_professor(professor_id: str, current_user: dict = Depends(admin_only)):
    admin = get_admin_client()

    # 존재 여부 확인
    existing = admin.table("users").select("id").eq("id", professor_id).eq("role", "professor").execute()
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="교수를 찾을 수 없습니다.")

    # public.users 삭제 → CASCADE로 auth.users도 삭제됨
    admin.table("users").delete().eq("id", professor_id).execute()
    return
