from fastapi import FastAPI
from src.claude_api import create_diary

app = FastAPI()


@app.get("/")
def home():
    return {"message": "moimz-mvp API 서버 실행 중!"}


# 모임일기 생성 API
@app.post("/diaries")
async def create_diary_api(data: dict):
    transactions = data.get("card_transactions", [])  # 카드 결제 데이터
    diary_entry = await create_diary(transactions)
    return {"diary": diary_entry}
