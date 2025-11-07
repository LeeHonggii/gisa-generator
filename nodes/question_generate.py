"""
문제 생성 노드
- Few-shot 예시를 기반으로 새로운 문제 생성
"""

import json
from typing import Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()


def generate_question(state: Dict) -> Dict:
    """문제 생성 노드 (GPT-4 사용)"""

    question_type = state.get("question_type", "code")
    similar_questions = state.get("similar_questions", [])

    if not similar_questions:
        raise ValueError("Few-shot 예시가 없습니다. 먼저 검색 노드를 실행하세요.")

    print(f"\n{'='*60}")
    print(f"새로운 {question_type} 문제 생성 중...")
    print(f"{'='*60}")

    # LLM 초기화
    llm = ChatOpenAI(
        model="gpt-5-chat-latest",
        temperature=0.8  # 창의성을 위해 높은 temperature
    )

    # Few-shot 예시에서 사용된 언어 감지
    detected_language = "Python"  # 기본값
    if similar_questions and similar_questions[0].get('코드'):
        code = similar_questions[0].get('코드', '')
        if '#include' in code or 'printf' in code or 'scanf' in code:
            detected_language = "C"
        elif 'public class' in code or 'System.out' in code or 'public static void main' in code:
            detected_language = "Java"
        elif 'def ' in code or 'print(' in code:
            detected_language = "Python"

    print(f"📌 감지된 언어: {detected_language}")

    # Few-shot 예시 포맷팅
    examples_text = ""
    for i, q in enumerate(similar_questions, 1):
        examples_text += f"\n\n=== 예시 {i} ===\n"
        examples_text += f"문제내용: {q.get('문제내용', '')}\n"

        if q.get('코드'):
            examples_text += f"\n코드:\n{q.get('코드', '')}\n"

        examples_text += f"\n답: {q.get('답', '')}\n"

        if q.get('해설'):
            examples_text += f"\n해설:\n{q.get('해설', '')}\n"

    # 프롬프트 템플릿
    if question_type == "code":
        system_prompt = f"""당신은 정보처리기사 실기 시험의 코드 문제를 출제하는 전문가입니다.

주어진 예시 문제들을 참고하여, 비슷한 난이도와 형식의 **완전히 새로운** 문제를 생성하세요.

요구사항:
1. **반드시 {detected_language} 언어를 사용**하여 문제를 작성하세요
2. 프로그램 분석 및 실행 결과를 묻는 형식
3. 난이도는 정보처리기사 실기 수준
4. 5점 배점
5. 명확한 정답 포함
6. 예시 문제와 동일한 언어({detected_language})로 작성

출력 형식 (JSON):
{{{{
  "문제내용": "문제 설명",
  "코드": "실제 실행 가능한 {detected_language} 코드",
  "점수": 5,
  "답": "정확한 답",
  "해설": "상세한 해설"
}}}}"""
    else:  # theory
        system_prompt = """당신은 정보처리기사 실기 시험의 이론 문제를 출제하는 전문가입니다.

주어진 예시 문제들을 참고하여, 비슷한 난이도와 형식의 **완전히 새로운** 문제를 생성하세요.

요구사항:
1. 데이터베이스, 소프트웨어공학, 네트워크, 보안 등 정보처리기사 범위 내
2. 용어 설명, 개념 이해, SQL 등의 형식
3. 난이도는 정보처리기사 실기 수준
4. 5점 배점
5. 명확한 정답 포함

출력 형식 (JSON):
{{{{
  "문제내용": "문제 설명",
  "코드": null,
  "점수": 5,
  "답": "정확한 답",
  "해설": "상세한 해설"
}}}}"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "다음 예시 문제들을 참고하여 새로운 문제를 만들어주세요:\n{examples}\n\n반드시 JSON 형식으로만 답변하세요.")
    ])

    # 문제 생성
    chain = prompt | llm
    response = chain.invoke({"examples": examples_text})

    # JSON 파싱
    try:
        # 마크다운 코드 블록 제거
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        generated_question = json.loads(content.strip())

        # 필수 필드 추가
        generated_question["문제번호"] = 0  # 생성된 문제
        generated_question["출처"] = "AI 생성"

        print("\n✅ 문제 생성 완료!")
        print(f"\n문제: {generated_question.get('문제내용', '')[:100]}...")

        if generated_question.get('코드'):
            print("\n코드:")
            print(generated_question.get('코드', '')[:200] + "...")

        print(f"\n정답: {generated_question.get('답', '')}")

    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: {e}")
        print(f"응답 내용: {response.content}")
        raise

    return {
        "generated_question": generated_question,
        "question_text": generated_question.get('문제내용', ''),
        "question_code": generated_question.get('코드'),
        "correct_answer": generated_question.get('답', ''),
        "explanation": generated_question.get('해설', ''),
        "messages": [{"role": "assistant", "content": f"새로운 문제가 생성되었습니다."}]
    }
