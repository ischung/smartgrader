# DB 마이그레이션 가이드

## 적용 순서

Supabase 대시보드 → **SQL Editor** 에서 아래 순서대로 실행합니다.

| 순서 | 파일 | 내용 |
|------|------|------|
| 1 | `001_initial_schema.sql` | 8개 테이블 + 인덱스 + DB RLS 정책 생성 |
| 2 | `002_seed_admin.sql` | 관리자 계정 초기 데이터 삽입 |
| 3 | `003_storage_rls.sql` | Storage 버킷 생성 + Storage RLS 정책 |

## 002_seed_admin.sql 적용 전 준비

1. Supabase 대시보드 → **Authentication → Users → Add user**
2. Email: `admin@smartgrader.local`, Password: `insang` 으로 계정 생성
3. 생성된 **UID** 복사
4. `002_seed_admin.sql` 파일의 `ADMIN_AUTH_UID` 값을 복사한 UID로 교체 후 실행

## 테이블 목록

| 테이블 | 설명 |
|--------|------|
| `users` | 사용자 (관리자/교수/학생), Supabase Auth UID와 연결 |
| `courses` | 교수 담당 과목 |
| `grade_item_groups` | 성적 항목 그룹 (과제, 프로젝트 등) |
| `grade_items` | 성적 항목 (중간고사, 과제1 등) |
| `grade_files` | 업로드된 원본·결과 파일 참조 |
| `student_scores` | 학생별 항목 원점수 |
| `grade_results` | 총점·학점 계산 결과 |
| `grade_policies` | 과목별 학점 구간 설정 |

## Supabase Storage 버킷 설정

`003_storage_rls.sql`이 자동으로 버킷을 생성합니다. 또는 대시보드에서 수동 생성:

1. Supabase 대시보드 → **Storage → New bucket**
2. 버킷명: `grade-files`
3. Public: **OFF** (비공개)

파일 경로 구조: `grade-files/{course_id}/{original|result}/{filename}`

## RLS 정책 요약

| 역할 | DB 테이블 | Storage |
|------|-----------|---------|
| admin | 전체 CRUD | 전체 조회·삭제 |
| professor | 본인 담당 과목 CRUD | 본인 과목 폴더 업로드·조회·삭제 |
| student | 본인 점수·결과 SELECT | 접근 불가 (403) |

> 상세 정책은 `rls_policies.sql` 참조
