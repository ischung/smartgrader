# 배포 가이드

## Frontend — Vercel

1. [vercel.com](https://vercel.com) → "Add New Project" → GitHub 저장소 연결
2. **Root Directory**: `frontend`
3. Framework: Vite (자동 감지)
4. 환경변수 설정 (Settings → Environment Variables):

| 변수명 | 값 |
|--------|----|
| `VITE_SUPABASE_URL` | Supabase 대시보드 → Settings → API → Project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase 대시보드 → Settings → API → anon public key |
| `VITE_API_URL` | Render 배포 URL (예: `https://smartgrader-api.onrender.com`) |

5. Deploy → 완료 후 배포 URL 복사 (다음 단계에서 사용)

---

## Backend — Render

1. [render.com](https://render.com) → "New Web Service" → GitHub 저장소 연결
2. **Root Directory**: `backend`
3. **Runtime**: Python 3
4. **Build Command**: `pip install -r requirements.txt`
5. **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. **Plan**: Free
7. 환경변수 설정 (Environment):

| 변수명 | 값 |
|--------|----|
| `SUPABASE_URL` | Supabase Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service_role key |
| `SUPABASE_ANON_KEY` | Supabase anon key |
| `ALLOWED_ORIGINS` | Vercel 배포 URL (예: `https://smartgrader.vercel.app`) |

8. Deploy → 완료 후 `/docs` (Swagger UI) 접근 확인

---

## CORS 설정 확인

Render 환경변수 `ALLOWED_ORIGINS`에 Vercel URL을 정확히 입력해야 합니다.

```
# 단일 도메인
ALLOWED_ORIGINS=https://smartgrader.vercel.app

# 여러 도메인 (콤마 구분, 개발 환경 포함)
ALLOWED_ORIGINS=https://smartgrader.vercel.app,http://localhost:3000
```

---

## Render 슬립 대응

Render 무료 플랜은 15분 비활성 후 슬립됩니다. 첫 요청 시 약 30초 대기가 발생하며, 프론트엔드에서 자동으로 "서버를 깨우는 중이에요..." 토스트를 표시합니다 (`src/utils/api.js`).

---

## 배포 후 검증

```bash
# Render API 헬스체크
curl https://smartgrader-api.onrender.com/health
# 기대값: {"status": "ok"}

# Swagger UI
open https://smartgrader-api.onrender.com/docs

# CORS 검증 (Vercel 도메인에서만 통과해야 함)
curl -H "Origin: https://malicious.com" https://smartgrader-api.onrender.com/health
# 기대값: CORS 오류
```
