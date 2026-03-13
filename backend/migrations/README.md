# DB 마이그레이션 가이드

> **자동화 완료:** `supabase/migrations/`에 SQL 파일을 추가하고 main에 merge하면 GitHub Actions가 자동으로 Supabase DB에 적용합니다.

---

## 자동화 흐름

```
개발자: supabase/migrations/ 에 SQL 추가 → main merge
  └─▶ GitHub Actions: deploy-migrations.yml 트리거
        └─▶ supabase db push --db-url $SUPABASE_DB_URL
              └─▶ 새 파일만 적용 (이미 적용된 파일은 자동 스킵)
```

---

## 최초 1회 설정 (GitHub Secret 등록)

| Secret 이름 | 값 획득 경로 |
|-------------|------------|
| `SUPABASE_DB_URL` | Supabase 대시보드 → Settings → Database → **Connection string → URI 탭 → Session mode (포트 5432)** |

등록 경로: GitHub → Repository → **Settings → Secrets and variables → Actions → New repository secret**

---

## 새 마이그레이션 추가 방법

1. `supabase/migrations/` 에 파일 생성
2. 파일명 형식: `YYYYMMDDHHmmss_설명.sql`
   예: `20260401000000_add_semester_column.sql`
3. 내용은 반드시 **멱등성** 보장 (`IF NOT EXISTS`, `ON CONFLICT DO NOTHING`, `DROP ... IF EXISTS`)
4. PR → main merge → Actions 탭에서 배포 확인

---

## 마이그레이션 파일 목록

### `supabase/migrations/` (자동 배포 대상)

| 파일 | 설명 |
|------|------|
| `20260313000000_initial_schema.sql` | 8개 테이블 + 인덱스 + DB RLS 정책 |
| `20260313000001_seed_admin.sql` | 관리자 자동 등록 트리거 |
| `20260313000002_storage_rls.sql` | Storage 버킷 + Storage RLS 정책 |

### `backend/migrations/` (참조용 원본)

| 파일 | 설명 |
|------|------|
| `001_initial_schema.sql` | 원본 스키마 (참조용) |
| `002_seed_admin.sql` | 원본 시드 (참조용 — 트리거 방식으로 대체됨) |
| `003_storage_rls.sql` | 원본 Storage RLS (참조용) |
| `rls_policies.sql` | RLS 정책 역할별 요약 + 검증 쿼리 |

---

## 관리자 계정 초기화 (최초 1회)

마이그레이션 자동 적용 후:

1. Supabase 대시보드 → **Authentication → Users → "Create new user"**
2. Email: `admin@smartgrader.local`, Password: 원하는 비밀번호
3. 저장 즉시 트리거가 실행되어 `public.users`에 `login_id=110509, role=admin` 자동 등록

---

## 검증 쿼리 (Supabase SQL Editor)

```sql
-- 마이그레이션 이력 확인 (3개 행 기대)
SELECT version, inserted_at
FROM supabase_migrations.schema_migrations
ORDER BY inserted_at;

-- 테이블 8개 생성 확인
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' ORDER BY table_name;

-- 관리자 트리거 확인
SELECT trigger_name FROM information_schema.triggers
WHERE trigger_name = 'on_admin_user_created';

-- 관리자 계정 생성 후 확인
SELECT id, login_id, name, role FROM public.users WHERE role = 'admin';
```
