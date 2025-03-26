from fastapi import FastAPI
from src.claude_api import create_diary
from src.face_api import router as face_router  # 얼굴 인식 API 추가
from src.image_api import router as dalle_router  # 그림 생성 API 추가

app = FastAPI()

# API 라우터 등록
app.include_router(face_router)  # 얼굴 인식 API
app.include_router(dalle_router)  # 그림 생성 API


@app.get("/")
def home():
    return {"message": "moimz-mvp API 서버 실행 중!"}


# 모임일기 생성 API
@app.post("/groups/{groupId}/diaries")
async def create_diary_api(groupId: int, data: dict):
    group_data = data.get("group_data", {})  # 모임 정보
    transactions = data.get("card_transactions", [])  # 카드 결제 데이터

    diary_entry = await create_diary(group_data, transactions)

    return {"groupId": groupId, "diary": diary_entry}
