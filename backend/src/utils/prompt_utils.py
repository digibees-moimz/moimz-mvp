import os
import random


# 일기 그림 생성 프롬프트 (실행할 때마다 문장들의 순서가 랜덤하게 섞임)
def generate_diary_prompt(
    diary_text: str, character_images: list, style_images: list, filename_mapping: dict
) -> str:
    # 바뀐 파일 이름 기준으로 표시
    character_img_names = ", ".join(
        f"{os.path.basename(filename_mapping.get(p, p))}" for p in character_images
    )
    style_img_names = ", ".join(
        f"{os.path.basename(filename_mapping.get(p, p))}" for p in style_images
    )

    static_lines = [
        "정사각형(1024x1024) 비율의 한 장짜리 모임 일기 그림을 그려줘.",
        "다른 인물들 없이 단디, 똑디, 우디만 그림에 나와야 해.",
        f"첨부한 단디, 똑디, 우디 이미지를 참고해서 그려줘: [{character_img_names}]",
        f"그림의 분위기와 그림체는 첨부한 이미지처럼 밝고 행복하고, 귀엽게 그려줘: [{style_img_names}]",
        "참고로 똑디도 단디와 똑같은 새라서 입과 부리가 단디의 입처럼 생겨야 해!",
        "표정과 감정 표현은 첨부한 이미지를 참고해서 다양하게 그려주고, 상황과 장소에 맞는 악세사리나 소품, 옷도 추가해줘.",
        "그림에 글자는 되도록 적지 마.",
        "그림은 컷으로 분리하지 말고 일기 내용을 한 눈에 알아볼 수 있도록 한 장의 그림으로 표현해야 해.",
        "일기의 주요 내용을 잘 표현하도록 하나의 그림에 그리고, 나머지 부가 내용들은 추억할 수 있게 주변(빈 공간)에 소품으로 그려줘.",
        "일기에 적힌 장소가 잘 표현되게 그려주면 좋겠어",
    ]

    random.shuffle(static_lines)  # 순서 섞기
    instructions = "\n\n".join(static_lines)

    return f"""
{instructions}
--------------------------------------
[일기 내용]
{diary_text.strip()}
"""


def split_image_paths(upload_paths: list):
    character_imgs = [
        p
        for p in upload_paths
        if any(
            name in os.path.basename(p).lower()
            for name in ["dandi", "ddockdi", "woodi"]
        )
    ]
    style_imgs = [p for p in upload_paths if "style" in os.path.basename(p).lower()]
    return character_imgs, style_imgs
