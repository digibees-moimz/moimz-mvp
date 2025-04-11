import os
import requests
import base64
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from PIL import Image
from io import BytesIO
from datetime import datetime

router = APIRouter()

SD_API_URL="https://hndot0vjlg4f74-3000.proxy.runpod.net"


# 프롬프트만 받는 요청 스키마
class PromptRequest(BaseModel):
    prompt: str  # 오직 이것만 보냄!


# 타임스탬프 기반 파일명 생성 함수
def get_timestamp_filename(prefix: str = "moimz", extension: str = ".png") -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}{extension}"


@router.post("/sd/generate-image")
async def generate_image_from_sd(data: PromptRequest):
    print("[DEBUG] 🔄 generate_image_from_sd() 호출됨")
    print(f"[DEBUG] 프롬프트: {data.prompt}")

    payload = {
        "prompt": data.prompt,
        "steps": 25,                         # Sampling steps
        "sampler_index": "Euler a",          # Sampling method
        "enable_hr": True,                   # Hires.fix 활성화
        "hr_scale": 2,                       # Upscale by 2
        "denoising_strength": 0.7,           # Denoising strength
        "hr_upscaler": "Latent",             # Upscaler
        "width": 768,                        # 기본 생성 해상도 너비
        "height": 512,                       # 기본 생성 해상도 높이
    }

    try:
        response = requests.post(f"{SD_API_URL}/sdapi/v1/txt2img", json=payload)
        print("[DEBUG] ✅ Stable Diffusion API 응답 수신")
        response.raise_for_status()

        result = response.json()
        image_base64 = result["images"][0]

        save_dir = "images/generated"
        os.makedirs(save_dir, exist_ok=True)

        filename = get_timestamp_filename()
        full_path = os.path.join(save_dir, filename)

        print(f"[DEBUG] 저장 파일명: {filename}")

        image_data = base64.b64decode(image_base64)
        image = Image.open(BytesIO(image_data))
        image.save(full_path)

        return {
            "message": "이미지 생성 성공",
            "saved_path": filename
        }

    except Exception as e:
        print(f"[DEBUG] ❌ 예외 발생: {e}")
        raise HTTPException(status_code=500, detail=f"Stable Diffusion 호출 실패: {str(e)}")
