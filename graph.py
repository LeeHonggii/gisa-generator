"""
LangGraph 그래프 정의
- 노드들을 연결하여 전체 플로우 구성
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from state import QuizState
from nodes import (
    search_similar_questions,
    generate_question,
    check_answer,
    save_wrong_question
)


def create_quiz_graph():
    """문제 생성 그래프 (generate까지만)"""

    # StateGraph 초기화
    workflow = StateGraph(QuizState)

    # 노드 추가
    workflow.add_node("search_questions", search_similar_questions)
    workflow.add_node("generate_question", generate_question)

    # 엣지 정의
    # START → Few-shot 검색
    workflow.set_entry_point("search_questions")

    # Few-shot 검색 → 문제 생성 → END (여기서 멈춤!)
    workflow.add_edge("search_questions", "generate_question")
    workflow.add_edge("generate_question", END)

    # 그래프 컴파일
    app = workflow.compile()

    return app


def create_answer_graph():
    """답변 확인 그래프 (check_answer → save_wrong)"""

    # StateGraph 초기화
    workflow = StateGraph(QuizState)

    # 노드 추가
    workflow.add_node("check_answer", check_answer)
    workflow.add_node("save_wrong", save_wrong_question)

    # 엣지 정의
    # START → 답변 확인
    workflow.set_entry_point("check_answer")

    # 조건부 엣지: 답변 확인 후
    def should_save_wrong(state: QuizState) -> Literal["save_wrong", "end"]:
        """오답이면 저장, 정답이면 종료"""
        if state.get("is_correct"):
            return "end"
        else:
            return "save_wrong"

    workflow.add_conditional_edges(
        "check_answer",
        should_save_wrong,
        {
            "save_wrong": "save_wrong",
            "end": END
        }
    )

    # 틀린 문제 저장 → 종료
    workflow.add_edge("save_wrong", END)

    # 그래프 컴파일
    app = workflow.compile()

    return app


def visualize_graph(app):
    """그래프 시각화 (선택사항)"""
    try:
        from IPython.display import Image, display
        display(Image(app.get_graph().draw_mermaid_png()))
    except Exception as e:
        print(f"그래프 시각화 실패: {e}")
        print("mermaid 그래프:")
        print(app.get_graph().draw_mermaid())
