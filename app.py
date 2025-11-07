"""
Streamlit 웹 인터페이스
정보처리기사 문제 생성 및 학습 시스템
"""

import streamlit as st
import json
from datetime import datetime
from graph import create_quiz_graph, create_answer_graph
from state import QuizState
from nodes.question_search import search_wrong_questions


# 페이지 설정
st.set_page_config(
    page_title="정보처리기사 문제 생성기",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .question-box {
        background-color: #f0f8ff;
        padding: 2rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin: 1rem 0;
    }
    .code-box {
        background-color: #282c34;
        color: #abb2bf;
        padding: 1.5rem;
        border-radius: 10px;
        font-family: 'Courier New', monospace;
        margin: 1rem 0;
    }
    .correct-answer {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #28a745;
    }
    .wrong-answer {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #dc3545;
    }
    .stat-box {
        background-color: #e7f3ff;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# Session State 초기화
def initialize_session_state():
    """세션 상태 초기화"""
    if 'quiz_state' not in st.session_state:
        st.session_state.quiz_state = {
            "question_type": "code",
            "similar_questions": [],
            "generated_question": None,
            "question_text": None,
            "question_code": None,
            "correct_answer": None,
            "user_answer": None,
            "is_correct": None,
            "explanation": None,
            "wrong_questions": [],
            "messages": [],
            "vector_db_initialized": False
        }

    if 'question_generated' not in st.session_state:
        st.session_state.question_generated = False

    if 'answer_submitted' not in st.session_state:
        st.session_state.answer_submitted = False

    if 'stats' not in st.session_state:
        st.session_state.stats = {
            'total_questions': 0,
            'correct_count': 0,
            'wrong_count': 0,
            'code_correct': 0,
            'code_wrong': 0,
            'theory_correct': 0,
            'theory_wrong': 0
        }


def generate_question_async(question_type: str):
    """문제 생성 (비동기 처리)"""

    with st.spinner('🔄 문제 생성 중... 잠시만 기다려주세요!'):
        try:
            # 그래프 생성
            app = create_quiz_graph()

            # 초기 상태
            initial_state: QuizState = {
                "question_type": question_type,
                "similar_questions": [],
                "generated_question": None,
                "question_text": None,
                "question_code": None,
                "correct_answer": None,
                "user_answer": None,
                "is_correct": None,
                "explanation": None,
                "wrong_questions": [],
                "messages": [],
                "vector_db_initialized": False
            }

            # 문제 생성까지 실행 (벡터 DB 초기화 스킵!)
            config = {"recursion_limit": 50}

            # 그래프 실행 (search_questions → generate_question 자동 진행)
            final_state = app.invoke(initial_state, config)

            # 세션 상태 업데이트
            st.session_state.quiz_state = final_state
            st.session_state.question_generated = True
            st.session_state.answer_submitted = False

            return True, "문제가 생성되었습니다!"

        except Exception as e:
            return False, f"오류 발생: {str(e)}"


def check_answer_async(user_answer: str):
    """답변 확인 (비동기 처리)"""

    with st.spinner('답변 확인 중...'):
        try:
            # 답변 확인용 그래프 사용
            app = create_answer_graph()

            # 현재 상태 가져오기
            state = st.session_state.quiz_state
            state['user_answer'] = user_answer

            # 답변 확인 실행
            config = {"recursion_limit": 50}
            result = app.invoke(state, config)

            # 세션 상태 업데이트
            st.session_state.quiz_state = result
            st.session_state.answer_submitted = True

            # 통계 업데이트
            st.session_state.stats['total_questions'] += 1

            question_type = state.get('question_type', 'code')

            if result.get('is_correct'):
                st.session_state.stats['correct_count'] += 1
                if question_type == 'code':
                    st.session_state.stats['code_correct'] += 1
                else:
                    st.session_state.stats['theory_correct'] += 1
            else:
                st.session_state.stats['wrong_count'] += 1
                if question_type == 'code':
                    st.session_state.stats['code_wrong'] += 1
                else:
                    st.session_state.stats['theory_wrong'] += 1

            return True, result

        except Exception as e:
            return False, f"오류 발생: {str(e)}"


def generate_similar_question_from_wrong(wrong_question: dict):
    """틀린 문제를 기반으로 비슷한 문제 생성"""

    try:
        from nodes.question_generate import generate_question

        # 틀린 문제를 Few-shot 예시로 사용
        question_type = "code" if wrong_question.get('코드') else "theory"

        # 상태 생성 (틀린 문제 1개를 Few-shot으로!)
        state = {
            "question_type": question_type,
            "similar_questions": [wrong_question],  # 틀린 문제만 사용!
            "generated_question": None,
            "question_text": None,
            "question_code": None,
            "correct_answer": None,
            "user_answer": None,
            "is_correct": None,
            "explanation": None,
            "wrong_questions": [],
            "messages": [],
            "vector_db_initialized": False
        }

        # 문제 생성
        result = generate_question(state)

        # 세션 상태 업데이트
        st.session_state.quiz_state = {**state, **result}
        st.session_state.question_generated = True
        st.session_state.answer_submitted = False

        return True, "비슷한 문제가 생성되었습니다!"

    except Exception as e:
        return False, f"오류 발생: {str(e)}"


# 메인 앱
def main():
    """메인 애플리케이션"""

    initialize_session_state()

    # 헤더
    st.markdown('<h1 class="main-header">🎓 정보처리기사 문제 생성기</h1>', unsafe_allow_html=True)

    # 사이드바
    with st.sidebar:
        st.header("⚙️ 설정")

        # 페이지 선택
        page = st.radio(
            "메뉴 선택",
            ["📝 문제 풀기", "🔁 복습하기", "📊 통계"],
            index=0
        )

        st.divider()

        # 통계 표시
        st.subheader("📈 나의 학습 현황")

        total = st.session_state.stats['total_questions']
        correct = st.session_state.stats['correct_count']
        wrong = st.session_state.stats['wrong_count']

        if total > 0:
            accuracy = (correct / total) * 100
            st.metric("정답률", f"{accuracy:.1f}%", f"{correct}/{total}")
        else:
            st.metric("정답률", "0%", "0/0")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("✅ 정답", correct)
        with col2:
            st.metric("❌ 오답", wrong)

        st.divider()

        # 초기화 버튼들
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 통계\n초기화", type="secondary", use_container_width=True):
                st.session_state.stats = {
                    'total_questions': 0,
                    'correct_count': 0,
                    'wrong_count': 0,
                    'code_correct': 0,
                    'code_wrong': 0,
                    'theory_correct': 0,
                    'theory_wrong': 0
                }
                st.success("통계 초기화 완료!")
                st.rerun()

        with col2:
            if st.button("♻️ 문제\n초기화", type="secondary", use_container_width=True):
                import os
                # solved_questions.json 삭제
                if os.path.exists("solved_questions.json"):
                    os.remove("solved_questions.json")
                # 세션 초기화
                st.session_state.question_generated = False
                st.session_state.answer_submitted = False
                st.success("푼 문제 초기화! 모든 문제를 다시 풀 수 있습니다!")
                st.rerun()

    # 메인 페이지
    if page == "📝 문제 풀기":
        show_quiz_page()
    elif page == "🔁 복습하기":
        show_review_page()
    elif page == "📊 통계":
        show_statistics_page()


def show_quiz_page():
    """문제 풀기 페이지"""

    st.header("📝 새로운 문제 풀기")

    # 상단: 문제 유형 선택 및 버튼
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        question_type = st.selectbox(
            "문제 유형",
            ["code", "theory"],
            format_func=lambda x: "💻 코드 문제" if x == "code" else "📚 이론 문제",
            key="question_type_select"
        )

    with col2:
        if st.button("🎲 문제 생성", type="primary", use_container_width=True):
            # 세션 초기화 (새 문제 시작)
            st.session_state.question_generated = False
            st.session_state.answer_submitted = False

            success, message = generate_question_async(question_type)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    with col3:
        if st.session_state.question_generated:
            if st.button("🔄 새 문제", type="secondary", use_container_width=True):
                st.session_state.question_generated = False
                st.session_state.answer_submitted = False
                st.rerun()

    st.divider()

    # 생성된 문제 표시
    if st.session_state.question_generated:
        state = st.session_state.quiz_state

        # 문제 표시
        st.markdown('<div class="question-box">', unsafe_allow_html=True)
        st.markdown(f"### 📋 문제")
        st.write(state.get('question_text', ''))
        st.markdown('</div>', unsafe_allow_html=True)

        # 코드 표시 (있는 경우)
        if state.get('question_code'):
            st.markdown("### 💻 코드")
            st.code(state['question_code'], language='python')

        st.divider()

        # 답변 입력
        if not st.session_state.answer_submitted:
            st.markdown("### ✍️ 답변 입력")

            user_answer = st.text_input(
                "정답을 입력하세요:",
                key="answer_input",
                placeholder="답을 입력하세요..."
            )

            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("✅ 확인", type="primary", use_container_width=True):
                    if user_answer.strip():
                        success, result = check_answer_async(user_answer)
                        if success:
                            st.rerun()
                    else:
                        st.warning("답변을 입력해주세요!")

        # 결과 표시
        else:
            result = st.session_state.quiz_state

            st.markdown("### 📊 결과")

            if result.get('is_correct'):
                st.markdown(f"""
                <div class="correct-answer">
                    <h3>🎉 정답입니다!</h3>
                    <p><strong>정답:</strong> {result.get('correct_answer', '')}</p>
                    <p>훌륭합니다! 계속 이 조자로 하시면 합격할 수 있습니다!</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="wrong-answer">
                    <h3>❌ 틀렸습니다</h3>
                    <p><strong>내 답:</strong> {result.get('user_answer', '')}</p>
                    <p><strong>정답:</strong> {result.get('correct_answer', '')}</p>
                    <p>틀린 문제가 복습 목록에 저장되었습니다.</p>
                </div>
                """, unsafe_allow_html=True)

            # 해설
            if result.get('explanation'):
                st.divider()
                st.markdown("### 📖 해설")
                st.text(result['explanation'])
    else:
        # 문제가 없을 때 안내
        st.info("위에서 문제 유형을 선택하고 '🎲 문제 생성' 버튼을 클릭하세요!")


def show_review_page():
    """복습하기 페이지"""

    st.header("🔁 틀린 문제 복습하기")

    # 복습 문제 검색
    if st.button("📚 복습 문제 불러오기", type="primary"):
        with st.spinner("복습 문제를 찾는 중..."):
            try:
                result = search_wrong_questions({})
                wrong_questions = result.get('wrong_questions', [])

                if wrong_questions:
                    st.session_state.review_questions = wrong_questions
                    st.success(f"{len(wrong_questions)}개의 복습 문제를 찾았습니다!")
                else:
                    st.info("아직 틀린 문제가 없습니다. 새로운 문제를 풀어보세요!")
            except Exception as e:
                st.error(f"오류 발생: {e}")

    # 복습 문제 표시
    if 'review_questions' in st.session_state and st.session_state.review_questions:
        st.divider()

        for i, item in enumerate(st.session_state.review_questions, 1):
            question = item['question']

            with st.expander(f"❌ 문제 {i} - {question.get('문제내용', '')[:50]}..."):
                st.markdown(f"**문제 내용:**")
                st.write(question.get('문제내용', ''))

                if question.get('코드'):
                    st.markdown("**코드:**")
                    st.code(question['코드'], language='python')

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**내 답:** `{item.get('user_answer', '')}`")
                with col2:
                    st.markdown(f"**정답:** `{item.get('correct_answer', '')}`")

                # 해설 표시
                if question.get('해설'):
                    st.markdown("**해설:**")
                    st.text(question.get('해설', ''))

                st.divider()

                # 비슷한 문제 재생성 버튼
                if st.button(f"🔄 비슷한 문제 다시 풀기", key=f"retry_{i}", type="primary", use_container_width=True):
                    # 이 틀린 문제를 Few-shot으로 사용해서 새 문제 생성
                    success, message = generate_similar_question_from_wrong(question)
                    if success:
                        st.success("비슷한 문제가 생성되었습니다! 아래에서 문제를 풀어보세요!")

                        # 생성된 문제 바로 표시
                        state = st.session_state.quiz_state

                        st.divider()
                        st.markdown("### 📋 생성된 문제")

                        # 문제 표시
                        st.markdown('<div class="question-box">', unsafe_allow_html=True)
                        st.write(state.get('question_text', ''))
                        st.markdown('</div>', unsafe_allow_html=True)

                        # 코드 표시
                        if state.get('question_code'):
                            st.markdown("### 💻 코드")
                            st.code(state['question_code'], language='python')

                        # 답변 입력
                        st.markdown("### ✍️ 답변 입력")
                        user_answer = st.text_input(
                            "정답을 입력하세요:",
                            key=f"answer_retry_{i}",
                            placeholder="답을 입력하세요..."
                        )

                        if st.button("✅ 확인", key=f"submit_retry_{i}", type="primary"):
                            if user_answer.strip():
                                success, result = check_answer_async(user_answer)
                                if success:
                                    st.rerun()
                            else:
                                st.warning("답변을 입력해주세요!")
                    else:
                        st.error(message)


def show_statistics_page():
    """통계 페이지"""

    st.header("📊 학습 통계")

    stats = st.session_state.stats
    total = stats['total_questions']

    if total == 0:
        st.info("아직 푼 문제가 없습니다. 문제를 풀어보세요!")
        return

    # 전체 통계
    st.subheader("📈 전체 통계")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown('<div class="stat-box">', unsafe_allow_html=True)
        st.metric("총 문제 수", total)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="stat-box">', unsafe_allow_html=True)
        st.metric("정답 수", stats['correct_count'])
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="stat-box">', unsafe_allow_html=True)
        st.metric("오답 수", stats['wrong_count'])
        st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        accuracy = (stats['correct_count'] / total) * 100
        st.markdown('<div class="stat-box">', unsafe_allow_html=True)
        st.metric("정답률", f"{accuracy:.1f}%")
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # 유형별 통계
    st.subheader("📊 유형별 통계")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 💻 코드 문제")
        code_total = stats['code_correct'] + stats['code_wrong']
        if code_total > 0:
            code_accuracy = (stats['code_correct'] / code_total) * 100
            st.metric("정답률", f"{code_accuracy:.1f}%")
            st.write(f"정답: {stats['code_correct']} / 오답: {stats['code_wrong']}")
        else:
            st.info("아직 코드 문제를 풀지 않았습니다.")

    with col2:
        st.markdown("### 📚 이론 문제")
        theory_total = stats['theory_correct'] + stats['theory_wrong']
        if theory_total > 0:
            theory_accuracy = (stats['theory_correct'] / theory_total) * 100
            st.metric("정답률", f"{theory_accuracy:.1f}%")
            st.write(f"정답: {stats['theory_correct']} / 오답: {stats['theory_wrong']}")
        else:
            st.info("아직 이론 문제를 풀지 않았습니다.")


if __name__ == "__main__":
    main()
