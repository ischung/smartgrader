"""
학생 계정 자동 프로비저닝 유틸리티

파일에서 추출한 학번 목록으로 Supabase Auth + public.users 계정을 생성한다.
- 이미 존재하는 학번은 건너뜀 (중복 생성 방지)
- 이메일: 학번@smartgrader.local
- 초기 비밀번호: 학번
"""


def provision_students(student_ids: list[str], admin) -> dict:
    """
    학번 목록을 받아 없는 학생만 계정 생성 후 결과를 반환한다.

    Returns:
        {"created": [...], "skipped": [...], "failed": [...]}
    """
    created = []
    skipped = []
    failed = []

    # 기존 등록된 학번 일괄 조회
    if not student_ids:
        return {"created": created, "skipped": skipped, "failed": failed}

    existing_resp = admin.table("users").select("login_id").in_("login_id", student_ids).execute()
    existing_ids = {row["login_id"] for row in (existing_resp.data or [])}

    for sid in student_ids:
        if sid in existing_ids:
            skipped.append(sid)
            continue

        email = f"{sid}@smartgrader.local"
        try:
            result = admin.auth.admin.create_user({
                "email": email,
                "password": sid,
                "email_confirm": True,
            })
            auth_uid = result.user.id

            admin.table("users").insert({
                "id": auth_uid,
                "login_id": sid,
                "name": sid,
                "role": "student",
            }).execute()

            created.append(sid)
        except Exception:
            failed.append(sid)

    return {"created": created, "skipped": skipped, "failed": failed}
