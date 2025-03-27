from fastapi import APIRouter, Request
from dotenv import load_dotenv
from pydantic import BaseModel
from selenium import webdriver
from src.utils.gpt_web_bot import GPTWebBot
from src.utils.prompt_utils import generate_diary_prompt
import os, anthropic, uuid

router = APIRouter()

# API 키 환경변수로 가져오기
load_dotenv(dotenv_path=".env")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))


class DiaryRequest(BaseModel):
    diary_text: str  # 일기 내용


def load_prompt():
    with open("src/prompts/prompt_template.txt", "r", encoding="utf-8") as f:
        return f.read()


async def generate_diary_content(group_data, transactions):
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


# 모임일기 내용 생성 API
@router.post("/groups/{groupId}/diaries")
async def create_diary_content(groupId: int, data: dict):
    group_data = data.get("group_data", {})  # 모임 정보
    transactions = data.get("card_transactions", [])  # 카드 결제 데이터

    diary_entry = await generate_diary_content(group_data, transactions)

    return {"groupId": groupId, "diary": diary_entry}


# 셀레니움 기반 모임일기 그림 생성 API
@router.post("/selenium/generate-image")
def generate_image_from_diary(req: DiaryRequest, request: Request):
    print(req.diary_text)

    # 1. main.py에서 저장해둔 bot 꺼내기
    bot = request.app.state.bot

    # 2. 학습 이미지 준비
    character_imgs = [
        "src/images/dandi.png",
        "src/images/ddockdi.png",
        "src/images/woodi.png",
    ]
    style_imgs = [
        "src/images/happy_bright_style_1.png",
        "src/images/happy_bright_style_2.png",
    ]

    # 3. 프롬프트 생성
    prompt = generate_diary_prompt(req.diary_text, character_imgs, style_imgs)

    # 4. 프롬프트 전송
    bot.send_prompt(prompt, character_imgs + style_imgs)

    # 5. 이미지 생성 기다리기 + 저장
    images = bot.wait_for_images()
    image_prefix = f"diary_{uuid.uuid4().hex[:8]}"
    bot.save_images(images, save_dir="images", prefix=image_prefix)

    return {
        "message": "이미지 생성 완료!",
        "image_count": len(images),
        "prefix": image_prefix,
    }
