-- ============================================================
-- SmartGrader Storage 버킷 & RLS 정책
-- 파일: 003_storage_rls.sql
--
-- 적용 전 준비:
--   Supabase 대시보드 → Storage → New bucket
--   이름: grade-files, Public: OFF (비공개)
--
-- 적용 방법:
--   SQL Editor에서 실행 (001_initial_schema.sql 이후에 실행)
-- ============================================================

-- ────────────────────────────────────────────────────────────
-- Storage 버킷 생성
-- (대시보드 UI로 생성했다면 이 구문은 건너뛰어도 됨)
-- ────────────────────────────────────────────────────────────
INSERT INTO storage.buckets (id, name, public)
VALUES ('grade-files', 'grade-files', false)
ON CONFLICT (id) DO NOTHING;


-- ────────────────────────────────────────────────────────────
-- Storage objects RLS 정책
-- storage.objects 테이블 기준으로 정책을 설정한다.
-- 경로 구조: grade-files/{course_id}/{file_type}/{filename}
-- ────────────────────────────────────────────────────────────

-- 교수: 본인 담당 과목 폴더에만 업로드 가능
CREATE POLICY "storage: 교수 본인 과목 업로드"
    ON storage.objects FOR INSERT
    WITH CHECK (
        bucket_id = 'grade-files'
        AND public.current_user_role() = 'professor'
        AND (storage.foldername(name))[1]::uuid IN (
            SELECT id FROM public.courses
            WHERE professor_id = auth.uid()
        )
    );

-- 교수: 본인 담당 과목 파일 조회
CREATE POLICY "storage: 교수 본인 과목 조회"
    ON storage.objects FOR SELECT
    USING (
        bucket_id = 'grade-files'
        AND (
            public.current_user_role() = 'admin'
            OR (
                public.current_user_role() = 'professor'
                AND (storage.foldername(name))[1]::uuid IN (
                    SELECT id FROM public.courses
                    WHERE professor_id = auth.uid()
                )
            )
        )
    );

-- 교수: 본인 담당 과목 파일 삭제
CREATE POLICY "storage: 교수 본인 과목 삭제"
    ON storage.objects FOR DELETE
    USING (
        bucket_id = 'grade-files'
        AND (
            public.current_user_role() = 'admin'
            OR (
                public.current_user_role() = 'professor'
                AND (storage.foldername(name))[1]::uuid IN (
                    SELECT id FROM public.courses
                    WHERE professor_id = auth.uid()
                )
            )
        )
    );

-- 학생: 파일 업로드 불가 (명시적 차단)
-- → 위 정책에 student role이 없으므로 INSERT는 자동 차단됨
-- → SELECT도 허용 정책 없으므로 자동 차단됨
-- (아래는 명시적 문서화를 위한 주석)
-- STUDENT CANNOT: INSERT, UPDATE, DELETE on storage.objects
-- STUDENT CANNOT: SELECT on storage.objects (본인 점수는 student_scores 테이블로만 조회)


-- ────────────────────────────────────────────────────────────
-- DB RLS 정책 검증용 쿼리 (실행 후 확인용, 실제 데이터에 적용 X)
-- SQL Editor에서 개별 실행하여 정책 동작 확인
-- ────────────────────────────────────────────────────────────

/*
-- ① 학생 세션에서 타 학생 점수 조회 테스트 (빈 결과 반환 확인)
-- SET request.jwt.claims = '{"sub": "<student_uuid>", "role": "authenticated"}';
-- SELECT * FROM public.student_scores WHERE student_id != '<student_uuid>';
-- → 결과: 0 rows (RLS 차단)

-- ② 학생 세션에서 파일 업로드 테스트 (403 확인)
-- supabase.storage.from('grade-files').upload('test.xlsx', file)
-- → 결과: 403 Forbidden (Storage RLS 차단)

-- ③ 교수 세션에서 타 교수 과목 조회 테스트 (빈 결과 반환 확인)
-- SET request.jwt.claims = '{"sub": "<professor_uuid>", "role": "authenticated"}';
-- SELECT * FROM public.courses WHERE professor_id != '<professor_uuid>';
-- → 결과: 0 rows (RLS 차단)
*/
