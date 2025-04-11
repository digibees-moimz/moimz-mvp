from dotenv import load_dotenv
from fastapi import FastAPI

# .env 로드
load_dotenv(dotenv_path=".env")

from src.utils.lifespan import lifespan
from src.apis.diary_api import router as diary_router
from src.apis.face_register_api import router as face_router
from src.apis.attendance_api import router as attendance_router
from src.apis.album_api import router as album_router
from src.apis.image_api import router as dalle_router

# lifespan 적용해서 FastAPI 앱 생성
app = FastAPI(lifespan=lifespan)

# API 라우터 등록
app.include_router(
    diary_router, prefix="/diary", tags=["Diary"]
)  # 일기(내용, 그림) 생성 API
app.include_router(face_router, prefix="/faces", tags=["Faces"])  # 얼굴 등록 API
app.include_router(
    attendance_router, prefix="/attendance", tags=["Attendance"]
)  # 출석체크 API
app.include_router(album_router, prefix="/album", tags=["Album"])  # 인물별 앨범 API
app.include_router(dalle_router, prefix="/diary", tags=["Diary"])  # 그림 생성 API


@app.get("/")
def home():
    return {"message": "moimz-mvp API 서버 실행 중!"}
