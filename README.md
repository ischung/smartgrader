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

## 문서

- [PRD](./smartgrader-prd.md)
- [TechSpec](./smartgrader-techspec.md)
- [Issues](./issues.md)
