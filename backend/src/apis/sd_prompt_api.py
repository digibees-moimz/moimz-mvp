from fastapi import APIRouter, HTTPException
from ..services.sd.moim_service import generate_prompt_from_scores

router = APIRouter()

@router.get("/prompt/{moim_id}")  # "moims" 빼고 간단화해도 됨
def get_moim_prompt(moim_id: int):
    """
    특정 모임 ID의 최고 카테고리 점수와 레벨로
    Stable Diffusion 프롬프트를 생성해주는 API.
    """
    try:
        result = generate_prompt_from_scores(moim_id)
        return {
            "moim_id": moim_id,
            "category": result["category"],
            "score": result["category_score"],
            "level": result["level"],
            "level_name": result["level_name"],
            "prompt": result["prompt"],
            "negative_prompt": result["negative_prompt"]

        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
