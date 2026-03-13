-- ============================================================
-- SmartGrader RLS 정책 참조 문서
-- 파일: rls_policies.sql
--
-- 이 파일은 이미 001_initial_schema.sql과 003_storage_rls.sql에
-- 포함된 RLS 정책을 역할별로 요약한 참조용 문서입니다.
-- 단독으로 실행하지 말고, 001 → 003 순서로 적용 후 확인용으로 사용하세요.
-- ============================================================

-- ────────────────────────────────────────────────────────────
-- 현재 적용된 RLS 정책 전체 조회 (확인용)
-- ────────────────────────────────────────────────────────────
SELECT
    schemaname,
    tablename,
    policyname,
    roles,
    cmd,
    qual AS using_expr,
    with_check
FROM pg_policies
WHERE schemaname IN ('public', 'storage')
ORDER BY schemaname, tablename, policyname;


-- ════════════════════════════════════════════════════════════
-- 역할별 접근 권한 요약
-- ════════════════════════════════════════════════════════════

-- ┌─────────────────────────────────────────────────────────┐
-- │ admin (관리자: login_id = '110509')                     │
-- ├─────────────────────────────────────────────────────────┤
-- │ users              → 전체 SELECT / INSERT / UPDATE / DELETE │
-- │ courses            → 전체 ALL                           │
-- │ grade_item_groups  → 전체 ALL                           │
-- │ grade_items        → 전체 ALL                           │
-- │ grade_files        → 전체 ALL                           │
-- │ student_scores     → 전체 ALL                           │
-- │ grade_results      → 전체 ALL                           │
-- │ grade_policies     → 전체 ALL                           │
-- │ storage.objects    → 전체 SELECT / DELETE               │
-- └─────────────────────────────────────────────────────────┘

-- ┌─────────────────────────────────────────────────────────┐
-- │ professor (교수)                                        │
-- ├─────────────────────────────────────────────────────────┤
-- │ users (본인)       → SELECT (본인 행만)                 │
-- │ courses            → 본인 professor_id 과목만 ALL       │
-- │ grade_item_groups  → 본인 담당 course_id만 ALL          │
-- │ grade_items        → 본인 담당 course_id만 ALL          │
-- │ grade_files        → 본인 담당 course_id만 ALL          │
-- │ student_scores     → 본인 담당 course_id만 ALL          │
-- │ grade_results      → 본인 담당 course_id만 ALL          │
-- │ grade_policies     → 본인 담당 course_id만 ALL          │
-- │ storage.objects    → 본인 과목 폴더만 INSERT/SELECT/DELETE │
-- └─────────────────────────────────────────────────────────┘

-- ┌─────────────────────────────────────────────────────────┐
-- │ student (학생: login_id = 학번)                         │
-- ├─────────────────────────────────────────────────────────┤
-- │ users (본인)       → SELECT (본인 행만)                 │
-- │ courses            → 본인이 점수를 가진 과목만 SELECT   │
-- │ grade_item_groups  → 본인 수강 과목만 SELECT            │
-- │ grade_items        → 본인 수강 과목만 SELECT            │
-- │ grade_files        → 접근 불가 (❌)                     │
-- │ student_scores     → 본인 student_id 행만 SELECT        │
-- │ grade_results      → 본인 student_id 행만 SELECT        │
-- │ grade_policies     → 본인 수강 과목만 SELECT            │
-- │ storage.objects    → 접근 불가 (❌ INSERT/SELECT/DELETE 모두) │
-- └─────────────────────────────────────────────────────────┘


-- ────────────────────────────────────────────────────────────
-- 정책 동작 검증 쿼리 (Supabase SQL Editor에서 실행)
-- ────────────────────────────────────────────────────────────

-- [검증 1] 학생이 타 학생 점수 조회 시 빈 결과 반환 확인
-- (실제 학생 UUID로 교체 후 실행)
/*
SET LOCAL request.jwt.claims = '{"sub":"<student_uuid>","role":"authenticated"}';
SELECT count(*) FROM public.student_scores;
-- 기대값: 본인 행 수 (타 학생 행은 0)
*/

-- [검증 2] 학생이 다른 학생의 grade_results 조회 시 빈 결과 확인
/*
SET LOCAL request.jwt.claims = '{"sub":"<student_uuid>","role":"authenticated"}';
SELECT count(*) FROM public.grade_results WHERE student_id != '<student_uuid>';
-- 기대값: 0
*/

-- [검증 3] 교수가 타 교수 과목 조회 시 빈 결과 확인
/*
SET LOCAL request.jwt.claims = '{"sub":"<professor_uuid>","role":"authenticated"}';
SELECT count(*) FROM public.courses WHERE professor_id != '<professor_uuid>';
-- 기대값: 0
*/
