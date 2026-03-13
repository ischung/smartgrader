# SmartGrader

> 교수가 여러 과목·분반의 성적을 하나의 시스템에서 일괄 관리하고, 과목별 유연한 성적 항목·가중치 설정으로 총점과 학점을 정확하게 자동 산출하는 웹 애플리케이션

## 기술 스택

| 분류 | 기술 |
|------|------|
| Frontend | React 18 + Vite + TailwindCSS |
| Backend | Python + FastAPI |
| Database | Supabase (PostgreSQL) |
| 파일 스토리지 | Supabase Storage |
| 인증 | Supabase Auth |
| 배포 | Vercel (Frontend) + Render (Backend) |

## 프로젝트 구조

```
smartgrader/
├── frontend/          # React + Vite 프론트엔드
│   ├── src/
│   │   ├── pages/     # 페이지 컴포넌트 (admin, professor, student)
│   │   ├── components/# 공통 UI 컴포넌트
│   │   ├── router/    # 라우팅 및 역할 기반 접근 제어
│   │   ├── store/     # Zustand 상태 관리
│   │   └── utils/     # Supabase 클라이언트 등 유틸
│   └── package.json
├── backend/           # FastAPI 백엔드
│   ├── main.py        # FastAPI 앱 진입점
│   ├── routers/       # API 라우터
│   ├── services/      # 비즈니스 로직
│   ├── repositories/  # DB 접근 계층
│   ├── models/        # Pydantic 스키마
│   ├── utils/         # 파일 파싱, 계산 유틸
│   ├── migrations/    # DB 마이그레이션 SQL
│   └── requirements.txt
├── .env.example       # 환경변수 예시
└── README.md
```

## 로컬 개발 환경 설정

### 1. 환경변수 설정
```bash
cp .env.example frontend/.env
cp .env.example backend/.env
# 각 .env 파일에 Supabase 정보 입력
```

### 2. Frontend 실행
```bash
cd frontend
npm install
npm run dev
# http://localhost:3000
```

### 3. Backend 실행
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
# http://localhost:8000/docs (Swagger)
```

## 초기 계정

| 역할 | ID | 초기 비밀번호 |
|------|-----|--------------|
| 관리자 | 110509 | insang |
| 교수 | 등록 후 제공 | 등록 시 설정 |
| 학생 | 학번 | 학번 (최초 로그인 후 변경) |

---

## 배포 가이드 (Vercel + Render + Supabase)

> 아래 순서대로 진행합니다. **Supabase → Render → Vercel** 순서가 중요합니다.

---

### 0단계 — Supabase 프로젝트 준비

1. [supabase.com](https://supabase.com) → 로그인 → **New project** 생성
2. **Settings → API** 에서 아래 값을 복사해 둡니다:

   | 항목 | 위치 |
   |------|------|
   | Project URL | `https://xxxx.supabase.co` |
   | `anon` public key | `eyJ...` (긴 JWT) |
   | `service_role` key | `eyJ...` (긴 JWT, 절대 공개 금지) |

3. **Settings → Database → Connection string → URI (Session mode, 포트 5432)** 복사
   → GitHub Secret `SUPABASE_DB_URL`로 등록
   → main 브랜치에 push되면 GitHub Actions가 자동으로 DB 스키마를 적용합니다.

4. **DB 스키마 적용 확인**: Actions 탭 → "Deploy — Supabase DB Migrations" → 성공 확인

5. **관리자 계정 생성 (최초 1회)**:
   - Supabase 대시보드 → **Authentication → Users → Create new user**
   - Email: `admin@smartgrader.local`  /  Password: 원하는 값 입력 후 저장
   - → 트리거가 자동으로 `public.users`에 `login_id=110509, role=admin` 등록

6. **Storage 버킷**: Supabase → Storage → `grade-files` 버킷이 자동 생성되어 있는지 확인
   (없으면 New bucket → 이름: `grade-files`, Public: OFF)

---

### 1단계 — Render (Backend) 배포

> Vercel보다 **먼저** 배포해야 Vercel에서 API URL을 입력할 수 있습니다.

1. [render.com](https://render.com) → 로그인 → **New → Web Service**
2. **Connect a repository** → GitHub 계정 연결 → `smartgrader` 저장소 선택
3. 아래 항목을 설정합니다:

   | 항목 | 값 |
   |------|----|
   | **Name** | `smartgrader-api` (원하는 이름) |
   | **Root Directory** | `backend` |
   | **Runtime** | `Python 3` |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
   | **Instance Type** | Free |

4. **Environment Variables** 탭에서 아래 4개를 추가합니다:

   | 변수명 | 값 | 획득 경로 |
   |--------|----|-----------|
   | `SUPABASE_URL` | `https://xxxx.supabase.co` | Supabase → Settings → API → Project URL |
   | `SUPABASE_SERVICE_ROLE_KEY` | `eyJ...` | Supabase → Settings → API → service_role key |
   | `SUPABASE_ANON_KEY` | `eyJ...` | Supabase → Settings → API → anon key |
   | `ALLOWED_ORIGINS` | _(일단 `http://localhost:3000` 입력, Vercel URL 확인 후 수정)_ | — |

5. **Create Web Service** 클릭 → 배포 완료까지 약 2~5분 대기
6. 배포 완료 후 상단에 표시되는 URL 복사:
   예) `https://smartgrader-api.onrender.com`

7. **배포 확인**:
   ```
   https://smartgrader-api.onrender.com/health   → {"status": "ok"}
   https://smartgrader-api.onrender.com/docs     → Swagger UI
   ```

   > ⚠️ 처음 접속 시 "잠시 대기" 메시지가 나올 수 있습니다. Render 무료 플랜은 15분 비활성 후 슬립되며, 첫 요청 시 약 30초 소요됩니다.

---

### 2단계 — Vercel (Frontend) 배포

1. [vercel.com](https://vercel.com) → 로그인 → **Add New → Project**
2. **Import Git Repository** → GitHub 계정 연결 → `smartgrader` 저장소 선택
3. 아래 항목을 설정합니다:

   | 항목 | 값 |
   |------|----|
   | **Framework Preset** | Vite (자동 감지됨) |
   | **Root Directory** | `frontend` ← **반드시 변경** |
   | **Build Command** | `npm run build` (자동) |
   | **Output Directory** | `dist` (자동) |

4. **Environment Variables** 섹션에서 아래 3개를 추가합니다:

   | 변수명 | 값 | 획득 경로 |
   |--------|----|-----------|
   | `VITE_SUPABASE_URL` | `https://xxxx.supabase.co` | Supabase → Settings → API → Project URL |
   | `VITE_SUPABASE_ANON_KEY` | `eyJ...` | Supabase → Settings → API → anon key |
   | `VITE_API_URL` | `https://smartgrader-api.onrender.com` | 1단계에서 복사한 Render URL |

5. **Deploy** 클릭 → 배포 완료까지 약 1~2분 대기
6. 배포 완료 후 상단에 표시되는 URL 복사:
   예) `https://smartgrader-xxxx.vercel.app`

---

### 3단계 — CORS 설정 (Render 환경변수 업데이트)

Render에서 설정한 `ALLOWED_ORIGINS`를 실제 Vercel URL로 업데이트해야 합니다.

1. [render.com](https://render.com) → `smartgrader-api` 서비스 → **Environment**
2. `ALLOWED_ORIGINS` 값을 수정:

   ```
   https://smartgrader-xxxx.vercel.app,http://localhost:3000
   ```

   > `,`(콤마)로 여러 도메인을 구분합니다. 공백 없이 입력.

3. **Save Changes** → Render가 자동으로 서비스를 재배포합니다 (약 1분)

4. **CORS 동작 확인**:
   ```bash
   # 허용된 도메인 → 정상 응답
   curl -H "Origin: https://smartgrader-xxxx.vercel.app" \
        https://smartgrader-api.onrender.com/health
   # 기대값: {"status":"ok"}

   # 허용되지 않은 도메인 → CORS 오류
   curl -v -H "Origin: https://malicious.com" \
        https://smartgrader-api.onrender.com/health
   # 기대값: Access-Control-Allow-Origin 헤더 없음
   ```

---

### 배포 완료 체크리스트

- [ ] Supabase DB 스키마 적용 완료 (Actions → Deploy Migrations → success)
- [ ] Supabase `admin@smartgrader.local` 계정 생성 완료
- [ ] Render `/health` → `{"status": "ok"}` 응답
- [ ] Render `/docs` → Swagger UI 접근 가능
- [ ] Vercel URL → 로그인 화면 표시
- [ ] Vercel → Render API 호출 시 CORS 오류 없음
- [ ] 타 도메인 → Render API 직접 호출 시 CORS 오류 발생

---

## 문서

- [PRD](./smartgrader-prd.md)
- [TechSpec](./smartgrader-techspec.md)
- [Issues](./issues.md)
- [배포 가이드 (상세)](./docs/deployment.md)
