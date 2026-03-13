-- ============================================================
-- SmartGrader Storage 버킷 & RLS 정책
-- 파일: 20260313000002_storage_rls.sql
-- (003_storage_rls.sql에서 멱등성 보강 후 이동)
-- ============================================================

-- ────────────────────────────────────────────────────────────
-- Storage 버킷 생성 (멱등성: ON CONFLICT DO NOTHING)
-- ────────────────────────────────────────────────────────────
INSERT INTO storage.buckets (id, name, public)
VALUES ('grade-files', 'grade-files', false)
ON CONFLICT (id) DO NOTHING;


-- ────────────────────────────────────────────────────────────
-- 기존 Storage RLS 정책 삭제 (멱등성 보장 — 재실행 시 오류 방지)
-- ────────────────────────────────────────────────────────────
DROP POLICY IF EXISTS "storage: 교수 본인 과목 업로드" ON storage.objects;
DROP POLICY IF EXISTS "storage: 교수 본인 과목 조회"   ON storage.objects;
DROP POLICY IF EXISTS "storage: 교수 본인 과목 삭제"   ON storage.objects;


-- ────────────────────────────────────────────────────────────
-- Storage objects RLS 정책
-- 경로 구조: grade-files/{course_id}/{original|result}/{filename}
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

-- 교수 + admin: 본인 담당 과목 파일 조회
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

-- 교수 + admin: 본인 담당 과목 파일 삭제
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

-- 학생: 파일 접근 불가
-- → 허용 정책이 없으므로 INSERT / SELECT / DELETE 모두 자동 차단 (403)
