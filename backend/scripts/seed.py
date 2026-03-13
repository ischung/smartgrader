"""
관리자 계정 시드 스크립트

실행 방법:
    cd backend
    python scripts/seed.py

동작:
    1. Supabase Auth에 admin@smartgrader.local 계정 생성 (PW: insang)
    2. DB 트리거(on_admin_user_created)가 자동으로 public.users에 삽입
       - login_id: 110509, name: 관리자, role: admin

이미 계정이 존재하면 건너뜁니다 (멱등성 보장).
"""

import os
import sys
from pathlib import Path

import dotenv

dotenv.load_dotenv(Path(__file__).parent.parent / ".env")

from supabase import create_client  # noqa: E402

ADMIN_EMAIL = "admin@smartgrader.local"
ADMIN_PASSWORD = "insang"


def main():
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not service_key:
        print("❌ 환경변수 SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY를 설정하세요.")
        sys.exit(1)

    client = create_client(url, service_key)

    # 이미 존재하는지 확인
    existing = client.table("users").select("id").eq("login_id", "110509").execute()
    if existing.data:
        print("✅ 관리자 계정이 이미 존재합니다. (login_id: 110509)")
        return

    # Supabase Auth에 계정 생성 → 트리거가 public.users 자동 삽입
    print("⏳ admin@smartgrader.local 계정 생성 중...")
    result = client.auth.admin.create_user({
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
        "email_confirm": True,
    })

    print("✅ 관리자 계정 생성 완료!")
    print("   Auth UID : " + result.user.id)
    print("   login_id : 110509")
    print("   role     : admin")
    print("   초기 PW  : " + ADMIN_PASSWORD)


if __name__ == "__main__":
    main()
