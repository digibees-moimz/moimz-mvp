import os
import requests
import base64
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from PIL import Image
from io import BytesIO
from datetime import datetime

from src.services.sd.moim_service import generate_prompt_from_scores 

router = APIRouter()

SD_API_URL="https://9js2jbl47724of-3000.proxy.runpod.net"


# 프롬프트만 받는 요청 스키마
class PromptRequest(BaseModel):
    prompt: str  # 오직 이것만 보냄!


# 타임스탬프 기반 파일명 생성 함수
def get_timestamp_filename(prefix: str = "moimz", extension: str = ".png") -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}{extension}"


@router.post("/generate-image/from-moim/{moim_id}")
async def generate_image_from_moim(moim_id: int):
    print(f"[DEBUG] 🧠 generate_image_from_moim() - moim_id: {moim_id}")

    try:
        # 1. 프롬프트 생성
        result = generate_prompt_from_scores(moim_id)
        prompt = result["prompt"]
        print(f"[DEBUG] 생성된 프롬프트: {prompt}")

        # 2. Stable Diffusion 호출
        payload = {
            "prompt": prompt,
            "steps": 25,
            "sampler_index": "Euler a",
            "enable_hr": True,
            "hr_scale": 2,
            "denoising_strength": 0.7,
            "hr_upscaler": "Latent",
            "width": 512,
            "height": 768,
        }

        response = requests.post(f"{SD_API_URL}/sdapi/v1/txt2img", json=payload)
        print("[DEBUG] ✅ Stable Diffusion API 응답 수신")
        response.raise_for_status()

        image_base64 = response.json()["images"][0]

        # 3. 이미지 저장
        save_dir = "images/generated"
        os.makedirs(save_dir, exist_ok=True)

        filename = get_timestamp_filename()
        full_path = os.path.join(save_dir, filename)
        image_data = base64.b64decode(image_base64)

        Image.open(BytesIO(image_data)).save(full_path)

        return {
            "message": "모임 기반 이미지 생성 성공",
            "moim_id": moim_id,
            "category": result["category"],
            "level": result["level"],
            "prompt": prompt,
            "saved_path": filename
        }

    except Exception as e:
        print(f"[DEBUG] ❌ 예외 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))