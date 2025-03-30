import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.utils.driver_utils import get_driver
from src.utils.gpt_web_bot import GPTWebBot


# 서버 시작/종료 시 실행되는 함수
@asynccontextmanager
async def lifespan(app: FastAPI):
    # yield 앞: 서버 시작 전에 실행(초기화 영역)
    print("서버 시작 - 드라이버 실행")

    # .env에서 사용자 프로필명 불러오기 (세션 유지용)
    profile_name = os.getenv("GPT_PROFILE_NAME", "default_profile")

    # 드라이버 + GPT WebBot 초기화
    driver = get_driver(profile_name)
    bot = GPTWebBot(driver)

    try:

        bot.go_to_chatgpt()
        bot.wait_for_login()  # 최초 실행만 수동 로그인 필요
        # bot.select_gpt4o()  # 원하면 자동 선택도 가능

        # 앱 전역 상태에 저장
        app.state.driver = driver
        app.state.bot = bot

        yield

    # yield 뒤: 서버 종료할 때 실행(정리 영역)
    finally:
        print("서버 종료 - 드라이버 정리")
        try:
            driver.quit()  # 예외가 발생하더라도 무조건 브라우저 종료
            print("드라이버 정상 종료")
        except Exception as e:
            print(f"드라이버 종료 중 오류: {e}")
