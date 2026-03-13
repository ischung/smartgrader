# Issues — SmartGrader

> **원본 TechSpec**: smartgrader-techspec.md
> **생성일**: 2026-03-13
> **총 이슈 수**: 26개
> **총 예상 소요**: 27일

---

## #1 [Setup] 프로젝트 초기화 (React + Vite + FastAPI)

**레이블**: Setup
**예상 소요**: 0.5일
**의존성**: 없음

### 설명

프론트엔드(React + Vite + TailwindCSS)와 백엔드(FastAPI) 기본 구조를 세팅한다.

- Frontend: `npm create vite@latest` → React 선택, TailwindCSS 설치, React Router, Zustand 설치
- Backend: FastAPI 프로젝트 구조 생성 (`routers/`, `services/`, `repositories/`, `models/`, `utils/`)
- 루트에 `frontend/`, `backend/` 디렉토리로 분리
- `.env.example` 파일 작성 (Supabase URL, Anon Key 등)
- `README.md` 초안 작성

### 수락 기준 (Acceptance Criteria)

- [ ] `frontend/` 에서 `npm run dev` 실행 시 React 앱이 브라우저에서 정상 동작한다
- [ ] `backend/` 에서 `uvicorn main:app` 실행 시 FastAPI Swagger 문서(`/docs`)에 접근 가능하다
- [ ] TailwindCSS가 적용된 샘플 컴포넌트가 렌더링된다
- [ ] `.env.example` 파일이 존재한다

### 참고

- TechSpec 섹션: §2, §3
- 관련 이슈: 없음

---

## #2 [Setup] Supabase 프로젝트 생성 및 DB 테이블 스키마 적용

**레이블**: Setup
**예상 소요**: 1일
**의존성**: 없음

### 설명

Supabase 프로젝트를 생성하고 TechSpec 데이터 모델에 따라 전체 DB 스키마를 적용한다.

생성할 테이블:
- `users` (role: admin/professor/student)
- `courses` (course_name, course_code, section, semester)
- `grade_item_groups` (name, weight)
- `grade_items` (name, weight, item_type, group_id, deduction_per_absence)
- `grade_files` (file_type: original/result, storage_path)
- `student_scores` (raw_score, absence_count)
- `grade_results` (total_score, grade)
- `grade_policies` (grade, min_score, max_score)

### 수락 기준 (Acceptance Criteria)

- [ ] Supabase 대시보드에서 8개 테이블이 모두 생성되어 있다
- [ ] 외래키(FK) 관계가 ERD와 일치한다
- [ ] numeric 필드는 `numeric(5,2)` 정밀도로 설정되어 있다
- [ ] SQL 마이그레이션 파일이 `backend/migrations/` 에 저장되어 있다

### 참고

- TechSpec 섹션: §4
- 관련 이슈: 없음

---

## #3 [Setup] Supabase Storage 버킷 및 RLS 정책 설정

**레이블**: Setup
**예상 소요**: 0.5일
**의존성**: Depends on #2

### 설명

파일 저장을 위한 Supabase Storage 버킷을 생성하고, 테이블별 Row Level Security(RLS) 정책을 적용한다.

- Storage 버킷: `grade-files` (원본·결과 파일 통합 관리, file_type으로 구분)
- RLS 정책:
  - `student_scores`: student는 본인 student_id 행만 SELECT 가능
  - `grade_results`: student는 본인 student_id 행만 SELECT 가능
  - `grade_files`: professor만 INSERT/DELETE 가능
  - `users`: admin만 professor 계정 INSERT/UPDATE/DELETE 가능

### 수락 기준 (Acceptance Criteria)

- [ ] `grade-files` 버킷이 생성되어 있다
- [ ] 학생 계정으로 타 학생 점수 데이터 SELECT 시 빈 결과가 반환된다
- [ ] 학생 계정으로 파일 업로드 시도 시 403이 반환된다
- [ ] RLS 정책 SQL이 `backend/migrations/rls_policies.sql` 에 저장되어 있다

### 참고

- TechSpec 섹션: §5-1 보안 정책
- 관련 이슈: #2

---

## #4 [Infra] GitHub Actions CI/CD 파이프라인 구성

**레이블**: Infra
**예상 소요**: 1일
**의존성**: Depends on #1

### 설명

GitHub Actions를 이용해 lint → test → build 자동화 파이프라인을 구성한다.

- Frontend: ESLint → Vite build
- Backend: ruff lint → pytest
- PR 생성 시 자동 실행, main 브랜치 머지 시 배포 트리거

### 수락 기준 (Acceptance Criteria)

- [ ] PR 생성 시 Frontend lint + build가 자동 실행된다
- [ ] PR 생성 시 Backend lint + test가 자동 실행된다
- [ ] main 브랜치 머지 시 Vercel·Render 배포가 자동 트리거된다
- [ ] `.github/workflows/ci.yml` 파일이 존재한다

### 참고

- TechSpec 섹션: §2-3
- 관련 이슈: #1

---

## #5 [Infra] Vercel(Frontend) + Render(Backend) 배포 연동

**레이블**: Infra
**예상 소요**: 1일
**의존성**: Depends on #1, #4

### 설명

Vercel과 Render에 각각 프론트엔드·백엔드를 배포하고 연동을 확인한다.

- Vercel: GitHub 연동, `frontend/` 디렉토리 빌드 설정
- Render: FastAPI Docker 또는 Python 환경 설정, 환경변수 등록
- CORS 설정: Vercel 배포 도메인만 허용
- Render 슬립 대응: 첫 요청 시 "서버를 깨우는 중이에요..." Toast 표시 로직

### 수락 기준 (Acceptance Criteria)

- [ ] Vercel URL로 React 앱에 접근 가능하다
- [ ] Render URL의 `/docs` (Swagger)에 접근 가능하다
- [ ] Vercel → Render API 호출이 CORS 오류 없이 동작한다
- [ ] 타 도메인에서 Render API 직접 호출 시 CORS 오류가 발생한다

### 참고

- TechSpec 섹션: §2-3, §6-6
- 관련 이슈: #1, #4

---

## #6 [DB] 관리자 계정 시드 데이터 삽입

**레이블**: DB
**예상 소요**: 0.5일
**의존성**: Depends on #2, #3

### 설명

초기 관리자 계정을 Supabase Auth + users 테이블에 삽입한다.

- Supabase Auth에 관리자 계정 생성 (login_id: 110509, 초기 PW: insang)
- `users` 테이블에 role: 'admin' 으로 레코드 삽입
- 시드 스크립트를 `backend/scripts/seed.py` 로 관리

### 수락 기준 (Acceptance Criteria)

- [ ] ID: 110509 / PW: insang 으로 로그인이 성공한다
- [ ] 로그인 후 반환되는 role이 'admin' 이다
- [ ] `backend/scripts/seed.py` 실행으로 시드 데이터가 재삽입 가능하다

### 참고

- TechSpec 섹션: §5-1
- 관련 이슈: #2, #3

---

## #7 [Backend] Supabase Auth 연동 및 역할별 로그인·로그아웃 API

**레이블**: Backend
**예상 소요**: 1일
**의존성**: Depends on #2, #3, #6

### 설명

Supabase Auth를 연동하여 로그인·로그아웃 API를 구현한다. 로그인 성공 시 사용자 role을 함께 반환한다.

- `POST /api/v1/auth/login`: login_id + password → Supabase Auth 인증 → role 반환
- `POST /api/v1/auth/logout`: 세션 종료
- Auth 미들웨어: Bearer 토큰 검증, role 추출, 의존성 주입

### 수락 기준 (Acceptance Criteria)

- [ ] 올바른 ID/PW로 로그인 시 200 + role 반환된다
- [ ] 잘못된 ID/PW로 로그인 시 401이 반환된다
- [ ] 토큰 없이 보호된 API 호출 시 401이 반환된다
- [ ] 권한 없는 role로 API 호출 시 403이 반환된다

### 참고

- TechSpec 섹션: §5-2
- 관련 이슈: #6

---

## #8 [Backend] 비밀번호 변경 API

**레이블**: Backend
**예상 소요**: 0.5일
**의존성**: Depends on #7

### 설명

모든 역할(admin/professor/student)이 본인 비밀번호를 변경할 수 있는 API를 구현한다.

- `PATCH /api/v1/auth/password`: 현재 PW 확인 → 새 PW로 Supabase Auth 업데이트

### 수락 기준 (Acceptance Criteria)

- [ ] 현재 PW가 맞으면 새 PW로 변경된다
- [ ] 변경 후 새 PW로 로그인이 성공한다
- [ ] 현재 PW가 틀리면 400이 반환된다

### 참고

- TechSpec 섹션: §5-2
- 관련 이슈: #7

---

## #9 [Backend] CORS 및 RBAC 미들웨어 구현

**레이블**: Backend
**예상 소요**: 0.5일
**의존성**: Depends on #7

### 설명

FastAPI에 CORS 미들웨어와 역할 기반 접근 제어(RBAC) 의존성을 구현한다.

- CORS: Vercel 배포 도메인만 허용
- RBAC: 각 라우터에 `require_role("admin")` 등의 의존성 주입
- 역할 계층: admin은 professor 기능도 수행 가능

### 수락 기준 (Acceptance Criteria)

- [ ] 허용된 도메인에서 API 호출 시 CORS 헤더가 정상 반환된다
- [ ] 허용되지 않은 도메인에서 API 호출 시 CORS 오류가 발생한다
- [ ] admin 계정으로 professor 전용 API 호출 시 정상 동작한다
- [ ] student 계정으로 professor 전용 API 호출 시 403이 반환된다

### 참고

- TechSpec 섹션: §5-1 보안 정책
- 관련 이슈: #7

---

## #10 [Backend] 교수 계정 CRUD API (관리자 전용)

**레이블**: Backend
**예상 소요**: 1일
**의존성**: Depends on #7, #9

### 설명

관리자가 교수 계정을 등록·조회·수정·삭제할 수 있는 API를 구현한다.

- `GET /api/v1/users/professors`: 교수 목록 조회
- `POST /api/v1/users/professors`: Supabase Auth + users 테이블에 교수 계정 생성
- `PATCH /api/v1/users/professors/{id}`: 이름, 비밀번호 수정
- `DELETE /api/v1/users/professors/{id}`: Supabase Auth + users 테이블에서 삭제

### 수락 기준 (Acceptance Criteria)

- [ ] 교수 등록 시 Supabase Auth와 users 테이블 모두에 레코드가 생성된다
- [ ] 중복 login_id로 등록 시 400이 반환된다
- [ ] 교수 삭제 시 관련 과목 데이터 처리 정책이 명확하다 (soft delete 또는 cascade)
- [ ] admin 외 role로 호출 시 403이 반환된다

### 참고

- TechSpec 섹션: §5-3
- 관련 이슈: #7, #9

---

## #11 [Backend] 과목 등록·조회·수정·삭제 API

**레이블**: Backend
**예상 소요**: 1일
**의존성**: Depends on #7, #9

### 설명

교수가 담당 과목을 관리할 수 있는 API를 구현한다.

- `GET /api/v1/courses`: 로그인한 교수의 담당 과목 목록
- `POST /api/v1/courses`: 과목 등록 (course_name, course_code, section, semester)
- `PATCH /api/v1/courses/{id}`: 과목 정보 수정
- `DELETE /api/v1/courses/{id}`: 과목 삭제
- 학기 형식 검증: YYYY-1 또는 YYYY-2만 허용

### 수락 기준 (Acceptance Criteria)

- [ ] 교수 A의 과목이 교수 B에게 노출되지 않는다
- [ ] 동일 교과코드 + 다른 분반은 별개의 과목으로 저장된다
- [ ] 학기 형식이 올바르지 않으면 400이 반환된다
- [ ] 과목 삭제 시 관련 성적 데이터도 함께 삭제된다

### 참고

- TechSpec 섹션: §5-4
- 관련 이슈: #7, #9

---

## #12 [Backend] 성적 파일 업로드 및 과목 정보 자동 추출 API

**레이블**: Backend
**예상 소요**: 2일
**의존성**: Depends on #11

### 설명

교수가 xlsx/xls/csv 파일을 업로드하면, 파일을 파싱하여 과목 정보를 자동 추출하고 미리보기 데이터를 반환한다.

- `POST /api/v1/courses/{id}/files/upload`
- 파일 형식 검증: .xlsx, .xls, .csv만 허용 (최대 10MB)
- pandas로 파일 파싱, 과목명·교과코드·분반·학기 자동 추출 시도
- 추출 실패 시 `auto_extracted: false` 반환 → 교수가 수동 입력
- Supabase Storage의 `grade-files` 버킷에 원본 파일 저장
- `grade_files` 테이블에 file_type: 'original' 로 레코드 저장

### 수락 기준 (Acceptance Criteria)

- [ ] .xlsx 파일 업로드 시 파싱된 미리보기 데이터가 반환된다
- [ ] 허용되지 않는 파일 형식 업로드 시 400이 반환된다
- [ ] 10MB 초과 파일 업로드 시 413이 반환된다
- [ ] 과목 정보 자동 추출 성공/실패 여부가 응답에 포함된다
- [ ] Supabase Storage에 원본 파일이 저장된다

### 참고

- TechSpec 섹션: §5-5, §6-5
- 관련 이슈: #11

---

## #13 [Backend] 성적 파일 업로드 시 학생 계정 자동 생성

**레이블**: Backend
**예상 소요**: 1일
**의존성**: Depends on #12

### 설명

파일 파싱 후 학생 목록에서 학번을 추출하여 계정을 자동 생성한다.

- 파일의 학번 컬럼에서 학생 목록 추출
- 기존에 없는 학번만 Supabase Auth + users 테이블에 생성 (초기 PW = 학번)
- role: 'student', login_id = 학번
- 이미 존재하는 학번은 건너뜀 (중복 생성 방지)
- 생성된 학생 점수 레코드를 `student_scores` 테이블에 초기화

### 수락 기준 (Acceptance Criteria)

- [ ] 파일 업로드 후 학번으로 로그인이 가능하다
- [ ] 초기 비밀번호는 학번과 동일하다
- [ ] 동일 학번이 이미 존재하면 계정이 중복 생성되지 않는다
- [ ] 여러 과목에 동일 학생이 있어도 계정은 1개만 생성된다

### 참고

- TechSpec 섹션: §5-1
- 관련 이슈: #12

---

## #14 [Backend] 성적 항목(GradeItem) CRUD API

**레이블**: Backend
**예상 소요**: 1일
**의존성**: Depends on #11

### 설명

교수가 과목별 성적 항목을 추가·수정·삭제할 수 있는 API를 구현한다.

- `GET /api/v1/courses/{id}/items`: 항목 목록 (display_order 순)
- `POST /api/v1/courses/{id}/items`: 항목 추가 (item_type: general/attendance/attitude)
- `PATCH /api/v1/courses/{id}/items/{item_id}`: 이름·가중치·순서 수정
- `DELETE /api/v1/courses/{id}/items/{item_id}`: 항목 삭제
- 가중치 합계 검증: 개별 항목 가중치 + 그룹 가중치 합계가 100%인지 확인

### 수락 기준 (Acceptance Criteria)

- [ ] 항목 추가·수정·삭제가 정상 동작한다
- [ ] 가중치 합계가 100%를 초과하면 400이 반환된다
- [ ] attitude 항목 추가 시 raw_score의 허용 범위(0~weight)가 저장된다
- [ ] display_order로 정렬된 항목 목록이 반환된다

### 참고

- TechSpec 섹션: §5-6
- 관련 이슈: #11

---

## #15 [Backend] 성적 항목 그룹(GradeItemGroup) CRUD API

**레이블**: Backend
**예상 소요**: 1일
**의존성**: Depends on #14

### 설명

교수가 성적 항목을 그룹으로 묶고 그룹 가중치를 설정할 수 있는 API를 구현한다.

- `GET /api/v1/courses/{id}/groups`: 그룹 목록 + 소속 항목 조회
- `POST /api/v1/courses/{id}/groups`: 그룹 생성 (name, weight)
- `PATCH /api/v1/courses/{id}/groups/{group_id}`: 그룹명·가중치 수정
- `DELETE /api/v1/courses/{id}/groups/{group_id}`: 그룹 삭제 (소속 항목은 그룹 해제)
- `PATCH /api/v1/courses/{id}/items/{item_id}/group`: 항목을 그룹에 추가/해제
- 그룹 소속 항목의 개별 weight는 NULL로 설정

### 수락 기준 (Acceptance Criteria)

- [ ] 그룹 생성 후 항목을 그룹에 추가하면 해당 항목의 weight가 NULL이 된다
- [ ] 그룹 삭제 시 소속 항목이 그룹 해제(group_id = NULL)된다
- [ ] 가중치 합계 검증 시 그룹 가중치가 포함된다

### 참고

- TechSpec 섹션: §5-7
- 관련 이슈: #14

---

## #16 [Backend] 점수 조회·수정·저장 API

**레이블**: Backend
**예상 소요**: 1일
**의존성**: Depends on #13, #14

### 설명

교수가 학생별 점수를 조회하고 수정·저장할 수 있는 API를 구현한다.

- `GET /api/v1/courses/{id}/scores`: 전체 학생 × 전체 항목 점수 테이블
- `PATCH /api/v1/courses/{id}/scores`: 특정 학생·항목의 점수 수정·저장
- attitude 항목: raw_score 범위 검증 (0 ≤ raw_score ≤ weight)
- attendance 항목: absence_count 저장 (raw_score 없음)

### 수락 기준 (Acceptance Criteria)

- [ ] 전체 학생 점수 테이블이 항목 순서대로 반환된다
- [ ] 특정 셀 값 수정 후 저장 시 DB에 반영된다
- [ ] attitude 점수가 범위를 벗어나면 400이 반환된다
- [ ] 교수 본인 과목이 아닌 경우 403이 반환된다

### 참고

- TechSpec 섹션: §5-8
- 관련 이슈: #13, #14

---

## #17 [Core Logic] 총점 계산 로직 구현

**레이블**: Core Logic
**예상 소요**: 2일
**의존성**: Depends on #15, #16

### 설명

`grade_calculator.py`에 유형별 총점 계산 로직을 구현하고 API로 노출한다.

- `POST /api/v1/courses/{id}/scores/calculate`
- 계산 규칙:
  - general: `raw_score × (weight / 100)`
  - group: `그룹 내 항목 평균 × (group.weight / 100)`
  - attendance: `max(0, weight - (0.5 × absence_count))` → 직접 합산
  - attitude: `raw_score` → 직접 합산
- 결과를 `grade_results` 테이블에 total_score로 저장

### 수락 기준 (Acceptance Criteria)

- [ ] general 항목 계산이 `raw_score × (weight/100)` 공식과 일치한다
- [ ] group 항목 계산이 `그룹 평균 × (group_weight/100)` 공식과 일치한다
- [ ] attendance 계산 결과가 음수일 경우 0으로 처리된다
- [ ] attitude 점수가 total에 직접 합산된다
- [ ] 가중치 합계가 100%가 아닌 경우 계산이 실행되지 않는다
- [ ] 계산 결과가 `grade_results` 테이블에 저장된다

### 참고

- TechSpec 섹션: §6-5
- 관련 이슈: #15, #16

---

## #18 [Core Logic] 학점 범위 설정 및 학점 산출 API

**레이블**: Core Logic
**예상 소요**: 1일
**의존성**: Depends on #17

### 설명

교수가 학점 범위를 설정하고, 총점 기준으로 학점을 자동 산출하는 API를 구현한다.

- `GET /api/v1/courses/{id}/policy`: 학점 범위 조회
- `PUT /api/v1/courses/{id}/policy`: 학점 범위 저장 (A+~F, 9개 구간)
- `POST /api/v1/courses/{id}/grades/calculate`: 총점 기준 학점 산출
- 범위 검증: 구간이 겹치거나 비어있으면 400
- 결과를 `grade_results` 테이블의 grade 컬럼에 저장

### 수락 기준 (Acceptance Criteria)

- [ ] 학점 범위 구간이 겹치면 400이 반환된다
- [ ] 총점 계산 전 학점 계산 시도 시 400이 반환된다
- [ ] 총점이 어느 범위에도 해당하지 않으면 'F'가 반환된다
- [ ] 계산 결과가 `grade_results.grade`에 저장된다

### 참고

- TechSpec 섹션: §5-9, §6-5
- 관련 이슈: #17

---

## #19 [Core Logic] 결과 파일 생성 및 다운로드 API

**레이블**: Core Logic
**예상 소요**: 1일
**의존성**: Depends on #18

### 설명

원본 파일의 모든 열 + 총점 열 + 학점 열을 합친 결과 파일을 생성하고 다운로드할 수 있도록 한다.

- `GET /api/v1/courses/{id}/files/{file_id}/download`: 파일 다운로드
- openpyxl로 원본 데이터 + 총점 + 학점 열 추가 → .xlsx 생성
- 결과 파일을 Supabase Storage에 file_type: 'result' 로 저장
- 원본 파일은 변경하지 않고 보존
- UI에서 원본/결과 파일 구분 배지 표시용 file_type 반환

### 수락 기준 (Acceptance Criteria)

- [ ] 다운로드된 파일에 원본의 모든 열이 포함된다
- [ ] 총점 열과 학점 열이 추가되어 있다
- [ ] 원본 파일이 변경되지 않고 보존된다
- [ ] 총점·학점 미계산 상태에서 결과 파일 다운로드 시도 시 400이 반환된다

### 참고

- TechSpec 섹션: §5-5, §6-5
- 관련 이슈: #18

---

## #20 [Backend] 학생 수강 과목 목록 및 성적 조회 API

**레이블**: Backend
**예상 소요**: 1일
**의존성**: Depends on #17, #18

### 설명

학생이 본인의 수강 과목 목록과 과목별 성적을 조회할 수 있는 API를 구현한다.

- `GET /api/v1/student/courses`: 학기별 수강 과목 목록
- `GET /api/v1/student/courses/{id}/scores`: 항목별 점수·기여점수·총점·학점 조회
- 미산출 항목은 `null` 반환
- RLS로 본인 데이터만 접근 가능

### 수락 기준 (Acceptance Criteria)

- [ ] 학생 A가 학생 B의 성적을 조회할 수 없다
- [ ] 학기별로 그룹화된 과목 목록이 반환된다
- [ ] 총점·학점 미산출 시 해당 필드가 null로 반환된다
- [ ] 각 항목의 기여 점수(contribution)가 포함된다

### 참고

- TechSpec 섹션: §5-10
- 관련 이슈: #17, #18

---

## #21 [Frontend] 로그인 페이지 및 역할별 라우팅 구현

**레이블**: Frontend
**예상 소요**: 1일
**의존성**: Depends on #7

### 설명

로그인 페이지와 역할별 접근 제어 라우팅을 구현한다.

- `LoginPage.jsx`: ID/PW 입력 폼, 로그인 요청, 역할별 대시보드 리다이렉트
- `PrivateRoute.jsx`: 비인증 접근 시 `/login` 리다이렉트, 역할 불일치 시 403 페이지
- Zustand에 인증 상태(user, role, token) 저장
- Render 슬립 대응: 첫 API 호출 시 "서버를 깨우는 중이에요..." Toast 표시

### 수락 기준 (Acceptance Criteria)

- [ ] 관리자 로그인 시 `/admin` 으로 이동한다
- [ ] 교수 로그인 시 `/professor` 로 이동한다
- [ ] 학생 로그인 시 `/student` 로 이동한다
- [ ] 비인증 상태로 보호된 페이지 접근 시 `/login` 으로 리다이렉트된다
- [ ] 로그인 실패 시 "앗, 아이디 또는 비밀번호가 올바르지 않아요." Toast가 표시된다

### 참고

- TechSpec 섹션: §6-2
- 관련 이슈: #7

---

## #22 [Frontend] 관리자 대시보드 및 교수 계정 관리 화면

**레이블**: Frontend
**예상 소요**: 1일
**의존성**: Depends on #10, #21

### 설명

관리자 대시보드와 교수 계정 CRUD 화면을 구현한다.

- `AdminDashboard.jsx`: 주요 기능 카드 (교수 관리, 전체 과목 현황)
- `ProfessorManagePage.jsx`: 교수 목록 테이블, 등록/수정/삭제 기능
- 삭제 시 `ConfirmDialog` 표시
- 등록·수정은 `Modal` 폼으로 처리

### 수락 기준 (Acceptance Criteria)

- [ ] 교수 목록이 테이블로 표시된다
- [ ] 교수 등록 모달에서 이름·ID·초기 비밀번호를 입력할 수 있다
- [ ] 삭제 시 확인 다이얼로그가 표시된다
- [ ] 작업 완료 시 Toast 알림이 표시된다

### 참고

- TechSpec 섹션: §6-1, §6-2
- 관련 이슈: #10, #21

---

## #23 [Frontend] 교수 대시보드 및 과목 목록·업로드 화면

**레이블**: Frontend
**예상 소요**: 1일
**의존성**: Depends on #11, #12, #21

### 설명

교수 대시보드, 과목 목록, 성적 파일 업로드 화면을 구현한다.

- `ProfessorDashboard.jsx`: 내 과목 수·미완료 성적 건수·학생 수 카드
- `CourseListPage.jsx`: 담당 과목 목록 (학기별 필터)
- `GradeUploadPage.jsx`:
  - 드래그앤드롭 파일 업로드 (`FileUploader.jsx`)
  - 업로드 후 과목 정보 확인/수정 모달
  - 업로드 성공 시 성적 미리보기 테이블 표시

### 수락 기준 (Acceptance Criteria)

- [ ] 파일 드래그앤드롭으로 업로드가 가능하다
- [ ] 업로드 중 스피너가 표시된다
- [ ] 과목 정보 자동 추출 성공 시 모달에 추출된 값이 자동 입력된다
- [ ] 미리보기 테이블에 업로드된 학생 데이터가 표시된다
- [ ] 허용되지 않는 파일 형식 선택 시 "앗, xlsx, xls, csv 파일만 업로드할 수 있어요." Toast가 표시된다

### 참고

- TechSpec 섹션: §6-1, §6-3
- 관련 이슈: #11, #12, #21

---

## #24 [Frontend] 성적 항목·가중치·그룹 설정 화면

**레이블**: Frontend
**예상 소요**: 2일
**의존성**: Depends on #14, #15, #23

### 설명

교수가 성적 항목과 가중치, 그룹을 설정할 수 있는 화면을 구현한다.

- `GradeItemPage.jsx` + `WeightEditor.jsx`
- 항목 추가·수정·삭제 (인라인 편집)
- 그룹 생성 및 항목 드래그 또는 체크박스로 그룹에 추가
- 가중치 실시간 합계 표시:
  - < 100%: 노란색 경고
  - = 100%: 초록색 체크
  - > 100%: 빨간색 + 총점 계산 버튼 비활성화
- 그룹 소속 항목은 가중치 입력창 비활성화

### 수락 기준 (Acceptance Criteria)

- [ ] 항목 추가·수정·삭제가 UI에서 즉시 반영된다
- [ ] 그룹 생성 후 항목을 그룹에 추가할 수 있다
- [ ] 가중치 합계가 실시간으로 표시된다
- [ ] 합계가 100%가 아니면 총점 계산 버튼이 비활성화된다
- [ ] 그룹 소속 항목의 가중치 입력창이 비활성화된다

### 참고

- TechSpec 섹션: §6-1, §7-4
- 관련 이슈: #14, #15, #23

---

## #25 [Frontend] 성적 조회·수정·총점·학점 계산·다운로드 화면

**레이블**: Frontend
**예상 소요**: 2일
**의존성**: Depends on #16, #17, #18, #19, #24

### 설명

교수가 성적을 조회·수정하고 총점·학점을 계산하며 결과 파일을 다운로드할 수 있는 화면을 구현한다.

- `GradeManagePage.jsx`: 학생×항목 성적 테이블, 셀 클릭 시 인라인 편집
- `GradeCalculatePage.jsx`: 총점 계산 버튼 → 총점 열 추가, 학점 계산 버튼 → 학점 열 추가
- `GradePolicyPage.jsx`: 학점 범위(A+~F) 설정 UI
- 총점 열: `bg-blue-50` 배경 강조
- 학점 열: `bg-blue-50` 배경 강조
- 원본/결과 파일 구분 배지 표시
- 결과 파일 다운로드 버튼

### 수락 기준 (Acceptance Criteria)

- [ ] 셀 클릭 시 인라인 input으로 전환되어 수정 가능하다
- [ ] 총점 계산 후 총점 열이 테이블에 추가된다
- [ ] 학점 계산 후 학점 열이 테이블에 추가된다
- [ ] 결과 파일 다운로드 시 .xlsx 파일이 저장된다
- [ ] 원본/결과 파일이 UI에서 구분 표시된다

### 참고

- TechSpec 섹션: §6-1, §6-3
- 관련 이슈: #16, #17, #18, #19, #24

---

## #26 [Frontend] 학생 대시보드 및 성적 조회 화면

**레이블**: Frontend
**예상 소요**: 1일
**의존성**: Depends on #20, #21

### 설명

학생이 본인의 수강 과목 목록과 과목별 성적을 조회할 수 있는 화면을 구현한다.

- `StudentDashboard.jsx`: 수강 과목 수·최근 학점 카드
- `StudentGradePage.jsx`:
  - 학기별 과목 목록
  - 과목 선택 시 항목별 점수·기여점수·총점·학점 조회
  - 미산출 항목은 "미산출" 배지로 표시
  - 다른 학생 데이터 접근 불가 (RLS 보장)

### 수락 기준 (Acceptance Criteria)

- [ ] 학기별로 그룹화된 수강 과목 목록이 표시된다
- [ ] 과목 선택 시 항목별 점수와 기여점수가 표시된다
- [ ] 총점·학점 미산출 항목에 "미산출" 배지가 표시된다
- [ ] 학생 본인 외 데이터가 노출되지 않는다

### 참고

- TechSpec 섹션: §6-1, §6-2
- 관련 이슈: #20, #21
