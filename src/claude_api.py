import os
import anthropic
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")  # 환경 변수 로드

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))


def load_prompt():
    with open("src/prompt_template.txt", "r", encoding="utf-8") as f:
        return f.read()


# 프롬프트 템플릿 로드
BASE_PROMPT = load_prompt()


async def create_diary(group_data, transactions):
    if not transactions:
        return "결제 내역이 없습니다."

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

    print("🟢 Claude API 응답:", response)
    return response.content
