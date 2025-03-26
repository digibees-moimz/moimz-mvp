import os
import anthropic
from fastapi import APIRouter
from dotenv import load_dotenv

router = APIRouter()

# API 키 환경변수로 가져오기
load_dotenv(dotenv_path=".env")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))


def load_prompt():
    with open("src/prompts/prompt_template.txt", "r", encoding="utf-8") as f:
        return f.read()


async def create_diary(group_data, transactions):
    if not transactions:
        return "결제 내역이 없습니다."

    BASE_PROMPT = load_prompt()
    prompt = BASE_PROMPT + "\n\n"

    # 모임 데이터 추가
    prompt += f"모임 이름: {group_data.get('appoint_name', '미정')}\n"
    prompt += f"모임 날짜: {group_data.get('date', '미정')}\n"
    prompt += f"모임 장소: {group_data.get('location', '미정')}\n"
    prompt += f"참석 인원: {group_data.get('actual_attendees', 0)}명 / 예상 인원: {group_data.get('expected_attendees', 0)}명\n"
    prompt += f"참석자: {', '.join(group_data.get('attendees', []))}\n"
    prompt += f"불참자: {', '.join(set(group_data.get('group_member', [])) - set(group_data.get('attendees', [])))}\n\n"

    # 카드 결제 데이터
    for tx in transactions:
        prompt += f"- {tx['merchant_name']} ({tx['merchant_category']})에서 {tx['amount']}원 결제 ({tx['transaction_date']}), 위치: {tx.get('location', '미정')}\n"

    prompt += "\n이 결제 내역 데이터를 기반으로 재미있는 모임 일기를 생성해줘!"

    # Claude API 호출
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=1500,
        # temperature=0.7,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content


# 모임일기 생성 API
@router.post("/groups/{groupId}/diaries")
async def create_diary_api(groupId: int, data: dict):
    group_data = data.get("group_data", {})  # 모임 정보
    transactions = data.get("card_transactions", [])  # 카드 결제 데이터

    diary_entry = await create_diary(group_data, transactions)

    return {"groupId": groupId, "diary": diary_entry}
