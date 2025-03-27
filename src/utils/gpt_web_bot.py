from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import base64, os, time


class GPTWebBot:
    def __init__(self, driver: webdriver.Chrome, wait_time: int = 30):
        self.driver = driver
        self.wait = WebDriverWait(driver, wait_time)

    # GPT 로그인 접속
    def go_to_chatgpt(self):
        print("[+] ChatGPT 페이지 접속 중...")
        self.driver.get("https://chat.openai.com/")

    # 수동 로그인
    def wait_for_login(self):
        print("🔑 ChatGPT에 로그인한 후 Enter를 누르세요...")
        input()

    # GPT-4o 모델 선택
    def select_gpt4o(self):
        print("[+] GPT-4o 모델 선택 시도 중...")
        try:
            # GPT 버튼 열기
            model_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'GPT-4')]"))
            )
            model_button.click()

            # GPT-4o 선택
            gpt4o_option = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//span[contains(text(), 'GPT-4o')]")
                )
            )
            gpt4o_option.click()
            print("[✔] GPT-4o 선택 완료")
        except:
            print("⚠️ 모델 선택 생략 (이미 선택됐을 수 있음)")

    # 프롬프트 전송
    def send_prompt(self, prompt: str, image_paths: list = None):
        if image_paths:
            for image_path in image_paths:
                file_input = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                )
                file_input.send_keys(os.path.abspath(image_path))
                time.sleep(1.5)

        time.sleep(3)  # textarea가 완전히 활성화될 때까지 대기

        input_box = self.wait.until(
            EC.presence_of_element_located((By.TAG_NAME, "textarea"))
        )
        input_box.send_keys(prompt)
        input_box.send_keys("\n")

    # base64 형식으로 로딩된 이미지가 생길 때까지 기다림
    def wait_for_images(self, timeout=300):
        print(f"[~] 이미지 생성 중... 최대 {timeout}초 대기")
        try:
            wait = WebDriverWait(self.driver, timeout)
            images = wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//img[contains(@src, 'data:image')]")
                )
            )
            print(f"[✔] 이미지 {len(images)}개 로딩 완료")
            return images
        except TimeoutException:
            print("⚠️ 이미지 생성 시간 초과 (5분 내에 이미지가 생성되지 않았습니다)")
            return []

    # base64 이미지를 디코딩해서 파일로 저장
    def save_images(self, images, save_dir="images/dairy/", prefix="image"):
        os.makedirs(save_dir, exist_ok=True)
        count = 0
        for i, img in enumerate(images):
            src = img.get_attribute("src")  # <img> 태그의 base64 URL 읽기
            if src.startswith("data:image"):  # base64 이미지만 저장
                _, b64 = src.split(",", 1)
                filename = os.path.join(save_dir, f"{prefix}_{i+1}.png")
                with open(filename, "wb") as f:
                    f.write(base64.b64decode(b64))
                count += 1
        print(f"[✔] 이미지 {count}개 저장 완료")
