from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc
import os


# 셀레니움 사용 시 로그인을 유지하기 위함
def get_driver(profile_name: str) -> uc.Chrome:
    options = uc.ChromeOptions()

    # 크롬 사용자 프로필 경로 지정
    profile_path = os.path.abspath(f"chrome_profiles/{profile_name}")
    os.makedirs(profile_path, exist_ok=True)
    options.add_argument(f"--user-data-dir={profile_path}")

    # 감지 우회 및 안정성 옵션
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")

    driver = uc.Chrome(options=options)
    return driver
