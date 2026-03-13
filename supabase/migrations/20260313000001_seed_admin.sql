-- ============================================================
-- SmartGrader 관리자 계정 자동 등록 트리거
-- 파일: 20260313000001_seed_admin.sql
--
-- 기존 002_seed_admin.sql 방식(수동 UUID 입력)을 자동화 방식으로 변경.
-- auth.users 테이블에 특정 이메일로 계정을 생성하면
-- 자동으로 public.users에 admin 역할로 등록됩니다.
--
-- 관리자 계정 생성 방법 (최초 1회):
--   Supabase 대시보드 → Authentication → Users → "Create new user"
--   Email: admin@smartgrader.local
--   Password: 원하는 비밀번호 입력 → 저장
--   → 트리거가 즉시 public.users에 login_id=110509, role=admin 으로 등록
-- ============================================================

-- ────────────────────────────────────────────────────────────
-- 트리거 함수: auth.users INSERT 시 admin 이메일이면 public.users에 자동 등록
-- ────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.handle_admin_user_creation()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    IF NEW.email = 'admin@smartgrader.local' THEN
        INSERT INTO public.users (id, login_id, name, role)
        VALUES (NEW.id, '110509', '관리자', 'admin')
        ON CONFLICT (id) DO NOTHING;

        RAISE LOG 'SmartGrader: admin 계정 자동 등록 완료 (uid=%, email=%)', NEW.id, NEW.email;
    END IF;
    RETURN NEW;
END;
$$;

-- ────────────────────────────────────────────────────────────
-- 트리거 등록 (멱등성: DROP IF EXISTS 후 재생성)
-- ────────────────────────────────────────────────────────────
DROP TRIGGER IF EXISTS on_admin_user_created ON auth.users;

CREATE TRIGGER on_admin_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_admin_user_creation();

COMMENT ON FUNCTION public.handle_admin_user_creation() IS
    'admin@smartgrader.local 이메일로 Supabase Auth 계정 생성 시 public.users에 admin 역할 자동 등록';
