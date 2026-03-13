-- ============================================================
-- SmartGrader 시드 데이터 — 관리자 계정 초기화
-- 파일: 002_seed_admin.sql
--
-- 적용 전 필수 작업:
--   1. Supabase 대시보드 → Authentication → Users → "Add user" 클릭
--   2. Email: admin@smartgrader.local, Password: insang (또는 원하는 비밀번호) 로 계정 생성
--   3. 생성된 UID를 아래 ADMIN_AUTH_UID에 붙여넣기
--
-- 적용 방법:
--   SQL Editor에서 ADMIN_AUTH_UID를 실제 값으로 교체 후 실행
-- ============================================================

-- ⚠️  아래 UUID를 실제 Supabase Auth UID로 교체하세요
DO $$
DECLARE
    ADMIN_AUTH_UID uuid := '00000000-0000-0000-0000-000000000000'; -- ← 여기에 실제 UID 입력
BEGIN
    INSERT INTO public.users (id, login_id, name, role)
    VALUES (ADMIN_AUTH_UID, '110509', '관리자', 'admin')
    ON CONFLICT (id) DO NOTHING;

    RAISE NOTICE '관리자 계정 등록 완료: login_id=110509, role=admin';
END $$;
