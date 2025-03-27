from fastapi import FastAPI
from src.utils.lifespan import lifespan
from src.apis.diary_api import router as diary_router
from src.apis.face_api import router as face_router
from src.apis.image_api import router as dalle_router

# lifespan 적용해서 FastAPI 앱 생성
app = FastAPI(lifespan=lifespan)

# API 라우터 등록
app.include_router(diary_router)  # 일기(내용, 그림) 생성 API
app.include_router(face_router)  # 얼굴 인식 API
app.include_router(dalle_router)  # 그림 생성 API


@app.get("/")
def home():
    return {"message": "moimz-mvp API 서버 실행 중!"}
