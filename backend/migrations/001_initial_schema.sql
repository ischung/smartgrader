-- ============================================================
-- SmartGrader 초기 스키마 마이그레이션
-- 파일: 001_initial_schema.sql
-- 설명: 8개 테이블 생성 + RLS 정책 적용
--
-- 적용 방법:
--   Supabase 대시보드 → SQL Editor → 이 파일 내용 붙여넣기 → Run
-- ============================================================

-- ────────────────────────────────────────────────────────────
-- 0. ENUM 타입 정의
-- ────────────────────────────────────────────────────────────
CREATE TYPE user_role AS ENUM ('admin', 'professor', 'student');
CREATE TYPE item_type AS ENUM ('general', 'attendance', 'attitude');
CREATE TYPE file_type AS ENUM ('original', 'result');


-- ────────────────────────────────────────────────────────────
-- 1. users (사용자)
--    Supabase Auth의 auth.users와 1:1 연결
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.users (
    id          uuid        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    login_id    varchar(50) NOT NULL UNIQUE,
    name        varchar(100) NOT NULL,
    role        user_role   NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.users IS '시스템 사용자 (관리자/교수/학생). Supabase Auth UID와 동일한 PK 사용';
COMMENT ON COLUMN public.users.login_id IS '로그인 ID — 관리자: 110509, 학생: 학번, 교수: 교번';


-- ────────────────────────────────────────────────────────────
-- 2. courses (과목)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.courses (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    professor_id    uuid        NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    course_name     varchar(200) NOT NULL,
    course_code     varchar(50) NOT NULL,
    section         varchar(20),        -- 분반 없으면 NULL
    semester        varchar(20) NOT NULL, -- 예: '2026-1'
    created_at      timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.courses IS '교수가 담당하는 과목';
COMMENT ON COLUMN public.courses.section IS '분반. 없으면 NULL';


-- ────────────────────────────────────────────────────────────
-- 3. grade_item_groups (성적 항목 그룹)
--    여러 성적 항목을 하나의 그룹으로 묶어 그룹 단위 가중치 적용
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.grade_item_groups (
    id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id   uuid        NOT NULL REFERENCES public.courses(id) ON DELETE CASCADE,
    name        varchar(100) NOT NULL,      -- 예: '과제', '프로젝트'
    weight      numeric(5,2) NOT NULL CHECK (weight >= 0 AND weight <= 100)
);

COMMENT ON TABLE public.grade_item_groups IS '성적 항목 그룹 — 그룹 소속 항목들의 평균에 group.weight를 적용';


-- ────────────────────────────────────────────────────────────
-- 4. grade_items (성적 항목)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.grade_items (
    id                      uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id               uuid        NOT NULL REFERENCES public.courses(id) ON DELETE CASCADE,
    group_id                uuid        REFERENCES public.grade_item_groups(id) ON DELETE SET NULL,
    name                    varchar(100) NOT NULL,      -- 예: '중간고사', '과제1'
    weight                  numeric(5,2) CHECK (weight >= 0 AND weight <= 100),
                                                        -- 그룹 미소속 항목만 설정, 그룹 소속 시 NULL
    item_type               item_type   NOT NULL,
    deduction_per_absence   numeric(5,2) DEFAULT 0.5,  -- attendance 타입: 결석 1회당 차감점
    display_order           integer     NOT NULL DEFAULT 0
);

COMMENT ON TABLE public.grade_items IS '성적 항목 (중간고사, 과제, 출석 등)';
COMMENT ON COLUMN public.grade_items.weight IS '그룹 미소속 항목의 가중치(%). 그룹 소속 시 NULL';
COMMENT ON COLUMN public.grade_items.deduction_per_absence IS 'attendance 타입: 결석 1시수당 차감 점수 (기본 0.5)';


-- ────────────────────────────────────────────────────────────
-- 5. grade_files (성적 파일)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.grade_files (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id       uuid        NOT NULL REFERENCES public.courses(id) ON DELETE CASCADE,
    file_type       file_type   NOT NULL,
    storage_path    varchar(500) NOT NULL,  -- Supabase Storage 경로
    uploaded_at     timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.grade_files IS '원본 성적 파일(xlsx/xls/csv) 및 계산 결과 파일 참조';


-- ────────────────────────────────────────────────────────────
-- 6. student_scores (학생 원점수)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.student_scores (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id       uuid        NOT NULL REFERENCES public.courses(id) ON DELETE CASCADE,
    student_id      uuid        NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    grade_item_id   uuid        NOT NULL REFERENCES public.grade_items(id) ON DELETE CASCADE,
    raw_score       numeric(5,2),   -- general / attitude 항목 점수 (NULL 가능 — 미입력)
    absence_count   integer,        -- attendance 항목만 사용, 나머지 NULL
    UNIQUE (course_id, student_id, grade_item_id)
);

COMMENT ON TABLE public.student_scores IS '항목별 학생 원점수. attendance 항목은 absence_count만 사용';


-- ────────────────────────────────────────────────────────────
-- 7. grade_results (총점·학점 계산 결과)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.grade_results (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id       uuid        NOT NULL REFERENCES public.courses(id) ON DELETE CASCADE,
    student_id      uuid        NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    total_score     numeric(5,2) NOT NULL,
    grade           varchar(3),         -- 'A+', 'A0', ... 'F'. 학점 미계산 시 NULL
    calculated_at   timestamptz NOT NULL DEFAULT now(),
    UNIQUE (course_id, student_id)
);

COMMENT ON TABLE public.grade_results IS '총점 계산 결과 및 학점. 재계산 시 upsert로 덮어쓴다';


-- ────────────────────────────────────────────────────────────
-- 8. grade_policies (학점 범위 설정)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.grade_policies (
    id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id   uuid        NOT NULL REFERENCES public.courses(id) ON DELETE CASCADE,
    grade       varchar(3)  NOT NULL,   -- 'A+', 'A0', ... 'F'
    min_score   numeric(5,2) NOT NULL,
    max_score   numeric(5,2) NOT NULL,
    UNIQUE (course_id, grade)
);

COMMENT ON TABLE public.grade_policies IS '과목별 학점 구간 설정 (교수가 직접 설정)';


-- ────────────────────────────────────────────────────────────
-- 인덱스
-- ────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_courses_professor_id       ON public.courses(professor_id);
CREATE INDEX IF NOT EXISTS idx_grade_items_course_id      ON public.grade_items(course_id);
CREATE INDEX IF NOT EXISTS idx_grade_items_group_id       ON public.grade_items(group_id);
CREATE INDEX IF NOT EXISTS idx_student_scores_course_id   ON public.student_scores(course_id);
CREATE INDEX IF NOT EXISTS idx_student_scores_student_id  ON public.student_scores(student_id);
CREATE INDEX IF NOT EXISTS idx_grade_results_course_id    ON public.grade_results(course_id);
CREATE INDEX IF NOT EXISTS idx_grade_results_student_id   ON public.grade_results(student_id);


-- ────────────────────────────────────────────────────────────
-- Row Level Security (RLS) 활성화
-- ────────────────────────────────────────────────────────────
ALTER TABLE public.users              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.courses            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.grade_item_groups  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.grade_items        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.grade_files        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_scores     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.grade_results      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.grade_policies     ENABLE ROW LEVEL SECURITY;


-- ────────────────────────────────────────────────────────────
-- RLS 헬퍼 함수: 현재 사용자 role 조회
-- ────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.current_user_role()
RETURNS user_role
LANGUAGE sql STABLE SECURITY DEFINER
AS $$
    SELECT role FROM public.users WHERE id = auth.uid();
$$;


-- ────────────────────────────────────────────────────────────
-- RLS 정책
-- ────────────────────────────────────────────────────────────

-- users
CREATE POLICY "users: 본인 조회"
    ON public.users FOR SELECT
    USING (id = auth.uid());

CREATE POLICY "users: admin 전체 조회"
    ON public.users FOR SELECT
    USING (public.current_user_role() = 'admin');

CREATE POLICY "users: admin 등록"
    ON public.users FOR INSERT
    WITH CHECK (public.current_user_role() = 'admin');

CREATE POLICY "users: admin 수정"
    ON public.users FOR UPDATE
    USING (public.current_user_role() = 'admin');

CREATE POLICY "users: admin 삭제"
    ON public.users FOR DELETE
    USING (public.current_user_role() = 'admin');

-- courses: 교수는 본인 과목만, 학생은 본인이 점수를 가진 과목만, admin은 전체
CREATE POLICY "courses: 교수 본인 과목 CRUD"
    ON public.courses FOR ALL
    USING (professor_id = auth.uid());

CREATE POLICY "courses: admin 전체"
    ON public.courses FOR ALL
    USING (public.current_user_role() = 'admin');

CREATE POLICY "courses: 학생 수강 과목 조회"
    ON public.courses FOR SELECT
    USING (
        public.current_user_role() = 'student'
        AND id IN (
            SELECT course_id FROM public.student_scores WHERE student_id = auth.uid()
        )
    );

-- grade_item_groups, grade_items, grade_files, grade_policies:
-- 교수는 본인 과목의 데이터만 접근
CREATE POLICY "grade_item_groups: 교수 본인 과목"
    ON public.grade_item_groups FOR ALL
    USING (
        course_id IN (SELECT id FROM public.courses WHERE professor_id = auth.uid())
        OR public.current_user_role() = 'admin'
    );

CREATE POLICY "grade_item_groups: 학생 조회"
    ON public.grade_item_groups FOR SELECT
    USING (
        public.current_user_role() = 'student'
        AND course_id IN (
            SELECT course_id FROM public.student_scores WHERE student_id = auth.uid()
        )
    );

CREATE POLICY "grade_items: 교수 본인 과목"
    ON public.grade_items FOR ALL
    USING (
        course_id IN (SELECT id FROM public.courses WHERE professor_id = auth.uid())
        OR public.current_user_role() = 'admin'
    );

CREATE POLICY "grade_items: 학생 조회"
    ON public.grade_items FOR SELECT
    USING (
        public.current_user_role() = 'student'
        AND course_id IN (
            SELECT course_id FROM public.student_scores WHERE student_id = auth.uid()
        )
    );

CREATE POLICY "grade_files: 교수 본인 과목"
    ON public.grade_files FOR ALL
    USING (
        course_id IN (SELECT id FROM public.courses WHERE professor_id = auth.uid())
        OR public.current_user_role() = 'admin'
    );

CREATE POLICY "grade_policies: 교수 본인 과목"
    ON public.grade_policies FOR ALL
    USING (
        course_id IN (SELECT id FROM public.courses WHERE professor_id = auth.uid())
        OR public.current_user_role() = 'admin'
    );

CREATE POLICY "grade_policies: 학생 조회"
    ON public.grade_policies FOR SELECT
    USING (
        public.current_user_role() = 'student'
        AND course_id IN (
            SELECT course_id FROM public.student_scores WHERE student_id = auth.uid()
        )
    );

-- student_scores: 교수는 본인 과목 전체 조회·수정, 학생은 본인 점수만 조회
CREATE POLICY "student_scores: 교수 본인 과목"
    ON public.student_scores FOR ALL
    USING (
        course_id IN (SELECT id FROM public.courses WHERE professor_id = auth.uid())
        OR public.current_user_role() = 'admin'
    );

CREATE POLICY "student_scores: 학생 본인만 조회"
    ON public.student_scores FOR SELECT
    USING (
        public.current_user_role() = 'student'
        AND student_id = auth.uid()
    );

-- grade_results: 교수는 본인 과목 전체, 학생은 본인만 조회
CREATE POLICY "grade_results: 교수 본인 과목"
    ON public.grade_results FOR ALL
    USING (
        course_id IN (SELECT id FROM public.courses WHERE professor_id = auth.uid())
        OR public.current_user_role() = 'admin'
    );

CREATE POLICY "grade_results: 학생 본인만 조회"
    ON public.grade_results FOR SELECT
    USING (
        public.current_user_role() = 'student'
        AND student_id = auth.uid()
    );
