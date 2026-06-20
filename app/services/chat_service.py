import json
from app.clients.llm_client import get_groq_client
from app.schemas.chat import ChatMessage

def chat(message: str, history: list[ChatMessage]) -> str:
    client = get_groq_client()

    system_prompt = """
당신은 대한민국 충청북도 여행 전문 AI 어시스턴트입니다.
반드시 모든 답변을 100% 한국어로만 작성하세요. 영어, 중국어, 일본어 등 다른 언어는 절대 사용하지 마세요.

## 답변 규칙
- 답변은 3~5문장 이내로 짧고 간결하게 작성합니다.
- 여행지 추천 시 장소명과 한 줄 특징만 간단히 제공합니다.
- 충청북도 외 지역 질문은 충청북도 여행으로 안내를 유도합니다.
- 마크다운 문법(*, **, #, - 등)을 절대 사용하지 마세요. 일반 텍스트로만 답변하세요.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        *[{"role": msg.role, "content": msg.content} for msg in history],
        {"role": "user", "content": message},
    ]

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=messages,
    )
    return response.choices[0].message.content


def suggest_questions(message: str, reply: str) -> list[str]:
    client = get_groq_client()

    prompt = f"""
사용자가 충청북도 여행 챗봇과 나눈 대화입니다.

사용자 질문: {message}
AI 답변: {reply}

위 대화를 바탕으로 사용자가 다음에 궁금해할 만한 추천 질문 3개를 생성하세요.
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 절대 포함하지 마세요.

{{"questions": ["질문1", "질문2", "질문3"]}}
"""

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.choices[0].message.content.strip()

    # JSON 블록 안에 감싸진 경우 추출
    if "```" in content:
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    # JSON 객체 부분만 추출
    start = content.find("{")
    end = content.rfind("}") + 1
    if start != -1 and end > start:
        content = content[start:end]

    try:
        return json.loads(content)["questions"]
    except Exception:
        return []
