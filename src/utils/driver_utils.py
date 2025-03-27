from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os


# 셀레니움 사용 시 로그인을 유지하기 위함
def get_driver(profile_name: str) -> webdriver.Chrome:
    options = Options()

    # 크롬 사용자 프로필 경로 지정
    profile_path = os.path.abspath(f"chrome_profiles/{profile_name}")
    os.makedirs(profile_path, exist_ok=True)

    # 봇 탐지 우회
    options.add_argument("--disable-blink-features=AutomationControlled")

    # 해당 계정만을 위한 로그인 세션, 쿠키, 설정을 따로 저장
    options.add_argument(f"--user-data-dir={profile_path}")

    # 안정성 향상 옵션
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")

    driver = webdriver.Chrome(options=options)
    return driver
