import os


# 일기 그림 생성 프롬프트
def generate_diary_prompt(
    diary_text: str, character_images: list, style_images: list
) -> str:
    character_img_names = "\n".join(
        f"- {os.path.basename(p)}" for p in character_images
    )
    style_img_names = "\n".join(f"- {os.path.basename(p)}" for p in style_images)

    return f"""
정사각형(1024x1024) 비율의 한 장짜리 모임 일기 그림을 그려줘.

다른 인물들 없이 단디, 똑디, 우디만 그림에 나와야 해. 

첨부한 단디, 똑디, 우디 이미지를 참고해서 그려줘:
{character_img_names}
참고로 똑디도 단디와 똑같은 새라서 입과 부리가 단디의 입처럼 생겨야 해. 

표정과 감정 표현은 다양하게 그려주고, 상황과 장소에 맞는 악세사리나 소품도 추가해줘

그림에 글자는 되도록 적지 마.

내가 이제 일기를 줄 건데, 그림은 컷으로 분리하지 말고 일기 내용을 한 눈에 알아볼 수 있도록 한 장의 그림으로 표현해야 해.
일기의 주요 내용을 잘 표현하도록 그리고, 나머지 부가 내용들은 추억할 수 있게 주변의 빈 공간에 소품이나 이모티콘으로 그려줘

[일기 내용]
{diary_text}
"""
