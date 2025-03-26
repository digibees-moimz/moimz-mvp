from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
import os

# API 키 환경변수로 가져오기
load_dotenv(dotenv_path=".env")
print(os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

router = APIRouter()


class DiaryRequest(BaseModel):
    diary_text: str


# 프롬프트 생성 함수 (일기 → 영어 그림 설명)
def convert_diary_to_prompt(diary_text: str) -> str:
    return f"""
    A cute and vibrant 2D digital illustration in a soft cartoon style with three original characters, standing together in a bright and playful outdoor scene with grass, soft sky gradients, and colorful confetti. Use soft, colorful lighting and smooth textures like in kawaii animations. Each character should be drawn with clear, detailed features:
    
    - Dandy: A plump, round blue bird with a fully white face and yellow beak. He has a tiny tuft of blue feathers on top of his head. And He has soft, straight blue bangs that curve gently across the forehead in a neat line. His personality is cheerful and energetic. He is wearing nothing but looks bright and expressive.
      
    - Ddokdi: A similar blue bird, but with a blue hat shaped like a flower petal edge and a big red flower with a yellow center attached to it. She has a white face, yellow beak, and soft pink blush on her cheeks. She looks warm and sweet.
    
    - Woody: A character with a giant broccoli-shaped green head and a peach-colored body. His expression is slightly sassy and unimpressed, but still cute and friendly.
    
    The scene is based on: {diary_text}.
    Include pastel colors and a soft, warm drawing style, gentle shadows, kawaii-style eyes, and a soft glowing background. Each character should have clear space around them and reflect their unique personality through posture and accessories.
    """


# DALL·E 3 이미지 생성 함수
def generate_dalle_image(prompt: str) -> str:
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        raise RuntimeError(f"[Error] 이미지 생성 실패: {e}")


# 그림 생성 API
@router.post("/generate-image")
async def generate_image(data: DiaryRequest):
    prompt = convert_diary_to_prompt(data.diary_text)
    try:
        image_url = generate_dalle_image(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "diary_text": data.diary_text,
        "prompt": prompt,
        "image_url": image_url,
    }