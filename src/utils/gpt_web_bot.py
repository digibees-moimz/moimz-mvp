from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
import base64, os, time, requests, pyperclip, random


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
            model_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'GPT-4')]"))
            )
            model_button.click()

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
        # 텍스트 입력창 활성화
        input_box = self.wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[contenteditable='true']")
            )
        )
        ActionChains(self.driver).move_to_element(input_box).pause(
            random.uniform(0.5, 1.5)
        ).click().perform()
        
        time.sleep(random.uniform(3, 10))  # 붙여넣기 후 잠시 대기
        
        # 클립보드로 붙여넣기
        pyperclip.copy(prompt if prompt.strip() else ".")
        input_box.send_keys(Keys.COMMAND, "v")  # 또는 Keys.CONTROL for Windows
        
        time.sleep(random.uniform(2, 5))  # 붙여넣기 후 잠시 대기
        
        if image_paths:
            file_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
            )
            absolute_paths = "\n".join([os.path.abspath(p) for p in image_paths])
            file_input.send_keys(absolute_paths)
            time.sleep(random.uniform(5, 15))

        # 클립보드를 활용한 붙여넣기 (이모지 포함 가능)
        pyperclip.copy(prompt if prompt.strip() else ".")
        input_box.send_keys(Keys.COMMAND, "v")  # MacOS, Windows/Linux: Keys.CONTROL

        
        input_box.send_keys(Keys.ENTER)

    # '이미지 생성됨' 버튼이 뜰 때까지 대기
    def wait_for_image_complete_button(self, timeout=300):
        print("[~] '이미지 생성됨' 버튼 대기 중...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    if btn.text.strip() == "이미지 생성됨":
                        print("✅ '이미지 생성됨' 버튼 확인됨")
                        return True
            except Exception as e:
                print(f"❗ 버튼 확인 중 예외 발생: {e}")
            time.sleep(random.uniform(5, 15))

        print("⚠️ 버튼이 5분 내로 나타나지 않았습니다")
        return False

    # 이미지 생성 대기 및 WebElement 수집
    def wait_for_images(self, timeout=300):
        print("[~] 이미지 생성 중... 최대 300초 대기")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                imgs = self.driver.find_elements(
                    By.XPATH, "//img[@alt='생성된 이미지']"
                )
                if imgs:
                    print(f"[✔] 이미지 {len(imgs)}개 발견")
                    return imgs  # WebElement 리스트 그대로 반환
            except Exception as e:
                print(f"❗ 이미지 수집 중 예외 발생: {e}")
            time.sleep(random.uniform(5, 15))

        print("⚠️ 이미지 생성 시간 초과")
        return []

    def save_best_image(
        self, images, save_dir="src/images/diary/", prefix="best_image"
    ):
        os.makedirs(save_dir, exist_ok=True)

        for img in images:
            src = img.get_attribute("src")
            style = img.get_attribute("style") or ""

            if not src or "blur(" in style or "opacity: 0" in style:
                continue

            timestamp = int(time.time())  # 현재시간을 정수로 가져오기
            filename = os.path.join(save_dir, f"{prefix}_{timestamp}.png")

            try:
                if src.startswith("data:image"):
                    _, b64 = src.split(",", 1)
                    with open(filename, "wb") as f:
                        f.write(base64.b64decode(b64))
                    print(f"[✔] base64 이미지 저장 완료: {filename}")
                    return filename

                elif src.startswith("http"):
                    img_data = requests.get(src, timeout=5).content
                    with open(filename, "wb") as f:
                        f.write(img_data)
                    print(f"[✔] 이미지 저장 완료: {filename}")
                    return filename
            except Exception as e:
                print(f"❗ 이미지 저장 실패: {e}")

        print("⚠️ 저장할 수 있는 이미지가 없습니다.")
        return None
