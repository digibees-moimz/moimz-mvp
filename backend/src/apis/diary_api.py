import os

from fastapi import APIRouter, Request
from pydantic import BaseModel
import anthropic

from src.utils.prompt_utils import generate_diary_prompt
from src.utils.driver_utils import get_driver
from src.utils.gpt_web_bot import GPTWebBot

router = APIRouter()

# API 키 환경변수로 가져오기
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
@router.post("/groups/{groupId}")
async def create_diary_content(groupId: int, data: dict):
    group_data = data.get("group_data", {})  # 모임 정보
    transactions = data.get("card_transactions", [])  # 카드 결제 데이터

    diary_entry = await generate_diary_content(group_data, transactions)

    return {"groupId": groupId, "diary": diary_entry}


# 셀레니움 기반 모임일기 그림 생성 API
@router.post("/image/selenium")
def generate_image_from_diary(req: DiaryRequest, request: Request):
    print(req.diary_text)

    # 1. 드라이버 생성 (요청 시점에)
    profile_name = os.getenv("GPT_PROFILE_NAME", "default_profile")
    driver = get_driver(profile_name)
    bot = GPTWebBot(driver)

    try:
        bot.go_to_chatgpt()
        bot.wait_for_login()  # 로그인 유지되면 바로 패스됨

        # 2. 학습 이미지 준비
        character_imgs = [
            "src/images/woodi.png",
            "src/images/ddockdi.png",
            "src/images/dandi.png",
        ]
        style_imgs = [
            "src/images/style1.png",
        ]

        all_imgs = character_imgs + style_imgs
        path_map = bot.copy_with_smart_names(all_imgs)

        # 3. 프롬프트 생성 + 전송
        prompt = generate_diary_prompt(
            req.diary_text, character_imgs, style_imgs, path_map
        )
        bot.send_prompt(prompt, list(path_map.values()))

        # 4. 이미지 생성 대기 및 저장
        if bot.wait_for_image_complete_button():
            image_elements = bot.wait_for_images()
            saved_path = bot.save_best_image(image_elements, prefix="moim_diary")
            return {
                "message": "가장 잘된 이미지 저장 완료!" if saved_path else "저장 실패",
                "saved_path": saved_path,
            }
        else:
            return {"message": "이미지 생성이 완료되지 않았습니다.", "image_count": 0}

    finally:
        # 5. 드라이버 정리
        try:
            driver.quit()  # 예외가 발생하더라도 무조건 브라우저 종료
            print("드라이버 정상 종료")
        except Exception as e:
            print(f"드라이버 종료 중 오류: {e}")
