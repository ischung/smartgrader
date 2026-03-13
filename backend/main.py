import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, courses, files, users

load_dotenv()

app = FastAPI(
    title="SmartGrader API",
    description="성적 관리 시스템 API",
    version="0.1.0",
)

# CORS 설정 — Vercel 배포 도메인만 허용
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(courses.router, prefix="/api/v1/courses", tags=["Courses"])
app.include_router(files.router, prefix="/api/v1/courses", tags=["Files"])

# 이후 이슈에서 순차적으로 추가
# app.include_router(courses.router, prefix="/api/v1/courses", tags=["Courses"])
# app.include_router(student.router, prefix="/api/v1/student", tags=["Student"])


@app.get("/")
def root():
    return {"message": "SmartGrader API", "version": "0.1.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
