import os
import anthropic
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")  # 환경 변수 로드

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
CLAUDE_API_URL = "https://api.anthropic.com/v1/complete"

# 기본 프롬프트 템플릿 설정
BASE_PROMPT = """
너는 이 모임에 참여한 모임원 중 한명이야.
이제부터 실제 사람이 쓴 것처럼 자연스러우면서 재미있고 귀여운 모임 일기를 써야해.
아래의 규칙을 적용해서 모임 일기를 써야 해.

1. 실제 사람이 쓴 것처럼 자연스럽고 감성적으로 작성해줘. 어색한 표현은 배제할 것.
2. 결제 데이터에서 유추할 수 있는 내용만 포함할 것.
3. 인물들의 구체적인 대화나 대사는 절대 포함하지 말고, 대화의 분위기만 묘사할 것.
4. 특정 인물들의 구체적인 행동과 성격에 대한 묘사는 넣지 말 것.
5. 참석하지 못한 친구에 대해서 단순히 아쉬움을 표현하고, 그 친구가 있었으면 어떤 분위기가 되었을지 상상하는 내용도 가끔씩 추가할 것.
6. 참여한 사람들의 감정을 표현할 것.
7. 메뉴는 결제 데이터를 기반으로 상호명을 참고하여 음식 카테고리로만 표현할 것. (ex. 카페-바닐라라떼(X), 커피(O), 디저트(O) / 치킨집-후라이드 치킨(X), 양념 치킨(X), 치킨(O), 콜라(O), 맥주(O) / 아웃백, 스테이크 하우스 - 스테이크(O), 샐러드(O), 파스타(O), 에이드(O)).
8. 자연스럽고 친근한 어조로, 다양한 표현을 사용하여 작성할 것.
9. 공백 포함 900자 이상 1300자 이내로 작성할 것.
10. 친한 친구처럼 성을 빼고 이름만 사용할 것.
11. 단락을 나누고, 이모티콘을 적절히 사용하여 감정을 표현할 것.
12. 미참석 모임원에 대한 언급할 것.
13. 마지막에 오늘 모임의 한줄 요약을 추가할 것.
14. 가장 하단에 해시태그(#)로 핵심 키워드를 추가할 것.

다음은 모임에서 사용한 결제 내역이야. 이를 참고해서 위 규칙을 적용한 모임 일기를 작성해줘:
"""

async def create_diary(transactions):
    if not transactions:
        return "결제 내역이 없습니다."

    # 카드 결제 데이터 추가하여 프롬프트 생성
    prompt = BASE_PROMPT + "\n\n"

    for tx in transactions:
        prompt += f"- {tx['merchant_name']} ({tx['merchant_category']})에서 {tx['amount']}원 결제 ({tx['transaction_date']}), 위치: {tx.get('location', '미정')}\n"

    prompt += "\n이 결제 내역 데이터를 기반으로 재미있는 모임 일기를 생성해줘!"

    # Claude API 호출
    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    print("🟢 Claude API 응답:", response)
    return response.content
