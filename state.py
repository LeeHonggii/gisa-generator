"""
LangGraph State 정의
"""

from typing import TypedDict, List, Dict, Optional, Annotated
from langgraph.graph import add_messages


class QuizState(TypedDict):
    """문제 풀이 시스템의 상태"""

    # 문제 타입
    question_type: str  # "code" or "theory"

    # Few-shot 예시
    similar_questions: List[Dict]  # 유사한 문제들

    # 생성된 문제
    generated_question: Optional[Dict]  # 생성된 문제 전체
    question_text: Optional[str]  # 문제 텍스트
    question_code: Optional[str]  # 코드 (코드 문제인 경우)
    correct_answer: Optional[str]  # 정답

    # 사용자 입력
    user_answer: Optional[str]  # 사용자 답변

    # 채점 결과
    is_correct: Optional[bool]  # 정답 여부

    # 해설
    explanation: Optional[str]  # 해설

    # 틀린 문제 저장
    wrong_questions: List[Dict]  # 틀린 문제 목록

    # 메시지 (대화 이력)
    messages: Annotated[list, add_messages]

    # 벡터 DB 상태
    vector_db_initialized: bool  # 벡터 DB 초기화 여부
