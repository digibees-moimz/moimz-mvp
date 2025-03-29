from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import os, time, requests, pyperclip, random, uuid, shutil
from PIL import Image


class GPTWebBot:
    def __init__(self, driver, wait_time: int = 30):
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

    # 프롬프트 전송 (이미지 업로드 + 프롬프트 분리 + 타이핑 전송)
    def send_prompt(
        self,
        prompt: str,
        upload_paths: list = None,
        temp_dir: str = "src/images/temp_uploads",
    ):
        # 텍스트 입력창 활성화
        input_box = self.wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[contenteditable='true']")
            )
        )

        ActionChains(self.driver).move_to_element(input_box).pause(
            random.uniform(0.5, 1.2)
        ).click().perform()

        # 참고 이미지 먼저 업로드
        if upload_paths:
            file_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
            )
            file_input.send_keys("\n".join(upload_paths))
            # 이미지 썸네일 등장 대기
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "img[src^='blob:']"))
            )

        # 프롬프트 분리: 설명 부분 + 일기 본문
        if "[일기 내용]" in prompt:
            pre, diary = prompt.split("[일기 내용]", 1)
            diary = "[일기 내용]" + diary  # 라벨 포함
        else:
            pre, diary = prompt, ""

        time.sleep(random.uniform(0.4, 0.6))

        # 🐌 붙여넣기 전 채팅창 스크롤 + 멈칫
        self.human_scroll(end=600)
        time.sleep(random.uniform(0.2, 0.4))

        # 일기 본문 클립보드로 붙여넣기
        pyperclip.copy(diary.strip() or ".")
        ActionChains(self.driver).move_to_element(input_box).click().perform()
        input_box.send_keys(Keys.COMMAND, "v")
        
        time.sleep(random.uniform(2.5, 3.5))
        input_box.send_keys(Keys.SHIFT, Keys.ENTER)

        # 설명 줄 단위로 타이핑
        for line in pre.strip().splitlines():
            self.human_type(input_box, line)
            input_box.send_keys(Keys.SHIFT, Keys.ENTER)
            time.sleep(random.uniform(0.2, 0.6))

        # 엔터로 전송
        time.sleep(random.uniform(1.5, 2.5))
        input_box.send_keys(Keys.ENTER)

        # 전송 후 임시 폴더 삭제
        if upload_paths and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"🧹 이미지 업로드 후 임시 폴더 삭제 완료: {temp_dir}")
            except Exception as e:
                print(f"⚠️ 임시 폴더 삭제 실패: {e}")

    # '이미지 생성됨' 버튼 감지
    def wait_for_image_complete_button(self, timeout=300):
        print("[~] '이미지 생성됨' 버튼 대기 중...")
        start_time = time.time()
        scrolled_for_starting = False

        while time.time() - start_time < timeout:
            try:
                self.human_scroll(end=600)
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    text = btn.text.strip()

                    if "시작하는 중" in text and not scrolled_for_starting:
                        self.human_scroll(end=1000)
                        print("🔄 이미지 생성 '시작하는 중' 발견! 스크롤 내리기")
                        scrolled_for_starting = True  # 이후엔 안 내리도록 설정
                        break

                    if text == "이미지 생성됨":
                        print("[✔] '이미지 생성됨' 버튼 확인됨")
                        return True
            except Exception as e:
                print(f"❗ 버튼 확인 중 예외 발생: {e}")
            time.sleep(random.uniform(4, 8))

        print("⚠️ 버튼이 5분 내로 나타나지 않았습니다")
        return False

    # 이미지 생성 대기
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
                    return imgs
            except Exception as e:
                print(f"❗ 이미지 수집 중 예외 발생: {e}")
            time.sleep(random.uniform(4, 8))

        print("⚠️ 이미지 생성 시간 초과")
        return []

    # 생성 이미지 저장
    def save_best_image(
        self, images, save_dir="src/images/diary/", prefix="best_image"
    ):
        os.makedirs(save_dir, exist_ok=True)

        for img in images:
            src = img.get_attribute("src")
            style = img.get_attribute("style") or ""

            if not src or "blur(" in style or "opacity: 0" in style:
                continue

            timestamp = int(time.time())
            filename = os.path.join(save_dir, f"{prefix}_{timestamp}.png")

            try:
                if src.startswith("http"):
                    img_data = requests.get(src, timeout=5).content
                    with open(filename, "wb") as f:
                        f.write(img_data)
                    print(f"[✔] 이미지 저장 완료: {filename}")
                    return filename
            except Exception as e:
                print(f"❗ 이미지 저장 실패: {e}")

        print("⚠️ 저장할 수 있는 이미지가 없습니다.")
        return None

    # 사람처럼 보이도록 적용한 함수들
    def human_type(self, element, text: str):
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.04, 0.18))  # 자연스러운 딜레이

    def human_scroll(self, end=1000, step=200):
        for i in range(0, end, step):
            self.driver.execute_script(f"window.scrollTo(0, {i});")
            time.sleep(random.uniform(0.3, 0.6))

    # 업로드할 이미지들 파일명에 랜덤 토큰 붙이고 저장
    def copy_with_smart_names(
        self, image_paths: list, temp_dir="src/images/temp_uploads"
    ) -> dict:
        # temp 디렉토리 초기화
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

        os.makedirs(temp_dir, exist_ok=True)

        mapping = {}

        for path in image_paths:
            try:
                base = os.path.basename(path)
                name, ext = os.path.splitext(base)
                rand = uuid.uuid4().hex[:6]
                new_name = f"{name}_{rand}{ext}"
                new_path = os.path.abspath(os.path.join(temp_dir, new_name))

                img = Image.open(path).convert("RGB")  # 색상 문제 방지
                img.save(new_path, format="PNG")  # 확실하게 PNG로 저장

                mapping[path] = new_path
            except Exception as e:
                print(f"❗ 이미지 복사 실패: {e}")

        return mapping
