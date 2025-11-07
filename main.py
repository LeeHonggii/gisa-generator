"""
메인 실행 파일
- 문제 풀이 시스템 실행
"""

from graph import create_quiz_graph
from state import QuizState


def run_quiz(question_type: str = "code"):
    """문제 풀이 시작"""

    print("="*60)
    print("🎓 정보처리기사 문제 생성 시스템")
    print("="*60)
    print(f"\n문제 유형: {'코드' if question_type == 'code' else '이론'}\n")

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

    try:
        # 그래프 실행 (문제 생성까지)
        config = {"recursion_limit": 50}

        # 문제 생성까지 실행
        state = initial_state
        for step_name in ["initialize_db", "search_questions", "generate_question"]:
            result = app.invoke(state, config)
            state.update(result)

        # 생성된 문제 출력
        print("\n" + "="*60)
        print("📝 생성된 문제")
        print("="*60)
        print(f"\n{state['question_text']}\n")

        if state.get('question_code'):
            print("코드:")
            print("-" * 60)
            print(state['question_code'])
            print("-" * 60)

        # 사용자 답변 입력
        print("\n답을 입력하세요:")
        user_answer = input("> ")

        # 답변 확인
        state['user_answer'] = user_answer

        # 답변 확인 및 틀린 문제 저장 실행
        final_result = app.invoke(state, config)

        # 결과 출력
        print("\n" + "="*60)
        print("📊 결과")
        print("="*60)

        if final_result.get('is_correct'):
            print("\n🎉 정답입니다! 축하합니다!")
        else:
            print(f"\n❌ 틀렸습니다.")
            print(f"\n정답: {final_result.get('correct_answer', '')}")

        # 해설 출력
        if final_result.get('explanation'):
            print("\n" + "-"*60)
            print("해설:")
            print("-"*60)
            print(final_result['explanation'])

    except KeyboardInterrupt:
        print("\n\n프로그램을 종료합니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


def main():
    """메인 함수"""

    while True:
        print("\n" + "="*60)
        print("문제 유형을 선택하세요:")
        print("="*60)
        print("1. 코드 문제")
        print("2. 이론 문제")
        print("3. 복습하기 (틀린 문제)")
        print("4. 종료")
        print()

        choice = input("선택 (1-4): ")

        if choice == "1":
            run_quiz("code")
        elif choice == "2":
            run_quiz("theory")
        elif choice == "3":
            print("\n복습 기능은 아직 구현 중입니다.")
            # run_review()
        elif choice == "4":
            print("\n프로그램을 종료합니다. 👋")
            break
        else:
            print("\n잘못된 입력입니다. 다시 선택해주세요.")

        # 계속할지 물어보기
        continue_quiz = input("\n다른 문제를 풀어보시겠습니까? (y/n): ")
        if continue_quiz.lower() != 'y':
            print("\n프로그램을 종료합니다. 👋")
            break


if __name__ == "__main__":
    main()
