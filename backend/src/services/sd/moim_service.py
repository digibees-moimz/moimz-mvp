from ...prompts.sd_template import prompt_data
from ...utils.score_utils import get_level_from_score

# 여기서는 "moims" 테이블에서 점수를 가져온다고 가정.
# 실제 DB 연동은 ORM or raw SQL로 처리하면 됨.
# 지금은 예시로 딕셔너리 사용(또는 DB 조회 가정).

def get_scores_by_moim_id(moim_id: int) -> dict:
    """
    실제로는 DB에서:
      SELECT score_restaurant, score_bar, ...
      FROM moims
      WHERE id = moim_id
    한 뒤, 딕셔너리로 반환.
    여기서는 예시로 하드코딩 or 임시 데이터.
    """
    # 예: 가상의 DB조회 결과
    fake_db_result = {
        "restaurant": 250,
        "bar": 130,
        "travel": 50,
        "cafe": 400,
        "leisure": 300
    }
    return fake_db_result

def generate_prompt_from_scores(moim_id: int, char_token: str = "a cutr blue bird character, <lora:dandi_style:1>") -> dict:
    """
    1) moim_id로 각 카테고리 점수 가져오기
    2) 가장 점수가 높은 카테고리 찾기
    3) 레벨 계산
    4) prompt_data에서 keywords를 꺼내 템플릿에 넣어 최종 프롬프트 구성
    """
    scores = get_scores_by_moim_id(moim_id)

    # 1) highest category
    top_category = max(scores, key=scores.get)
    top_score = scores[top_category]

    # 2) 레벨 산정
    level = get_level_from_score(top_score)

    # 3) 해당 카테고리/레벨 키워드 찾기
    cat_info = prompt_data[top_category][level]
    level_name = cat_info["level_name"]
    keywords = cat_info["keywords"]  # comma-separated keywords

    # 4) 최종 프롬프트
    # 예) "(char_token:1.2), fine dining chef jacket, elegant plating, ... , best quality"
    final_prompt = (
        f"{char_token}, "
        f"{keywords}, "
        "extremely detailed, cartoon style, 4k, trending on ArtStation, cinematic lighting, "
        "masterpiece, best quality"
    )

    return {
        "category": top_category,
        "category_score": top_score,
        "level": level,
        "level_name": level_name,
        "prompt": final_prompt
    }
