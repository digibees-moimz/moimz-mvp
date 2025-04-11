from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.services.user.storage import load_faces_from_files


# 서버 시작/종료 시 실행되는 함수
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시, 저장된 벡터 파일들을 불러옴
    load_faces_from_files()
    print("서버 시작 - 셀레니움은 요청 시 동적으로 실행됩니다.")

    yield

    print("서버 종료")
