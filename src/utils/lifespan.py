from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.utils.driver_utils import get_driver
from src.utils.gpt_web_bot import GPTWebBot
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=".env")


# 서버 시작/종료 시 실행되는 함수
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("서버 시작 - 드라이버 실행")

    # 환경변수에서 계정명(로그인 세션, 쿠키, 설정 저장용) 읽기
    profile_name = os.getenv("GPT_PROFILE_NAME", "default_profile")

    # 드라이버 & bot 초기화
    driver = get_driver(profile_name)
    bot = GPTWebBot(driver)

    bot.go_to_chatgpt()
    bot.wait_for_login()  # 첫 실행만 수동 로그인 필요
    bot.select_gpt4o()

    # 드라이버 & bot 상태 공유
    app.state.driver = driver
    app.state.bot = bot

    # yield 앞: 서버 시작 시 실행됨(초기화 영역)
    yield
    # yield 뒤: 서버 종료 시 실행됨(정리 영역)

    # 종료
    print("서버 종료 - 드라이버 정리")
    try:
        driver.quit()  # 브라우저 닫기
        print("드라이버 정상 종료")
    except Exception as e:
        print(f"드라이버 종료 중 오류: {e}")
