"""
답변 확인 노드
- 사용자 답변과 정답 비교
"""

from typing import Dict


def normalize_answer(answer: str) -> str:
    """답변 정규화 (공백, 대소문자 등)"""
    return answer.strip().lower()


def check_answer(state: Dict) -> Dict:
    """답변 확인 노드"""

    user_answer = state.get("user_answer", "")
    correct_answer = state.get("correct_answer", "")

    print(f"\n{'='*60}")
    print(f"답변 확인 중...")
    print(f"{'='*60}")

    print(f"\n입력한 답: {user_answer}")
    print(f"정답: {correct_answer}")

    # 답변 정규화
    user_normalized = normalize_answer(user_answer)
    correct_normalized = normalize_answer(correct_answer)

    # 정답 확인
    # 여러 정답이 있는 경우 (쉼표로 구분)
    if ',' in correct_answer:
        correct_options = [normalize_answer(opt) for opt in correct_answer.split(',')]
        is_correct = user_normalized in correct_options
    else:
        # 부분 일치도 허용 (정답이 사용자 답변에 포함되어 있으면 정답)
        is_correct = (user_normalized == correct_normalized or
                      user_normalized in correct_normalized or
                      correct_normalized in user_normalized)

    if is_correct:
        print("\n🎉 정답입니다!")
        message = "정답입니다! 잘하셨습니다."
    else:
        print("\n❌ 틀렸습니다.")
        message = f"틀렸습니다. 정답은 '{correct_answer}'입니다."

    return {
        "is_correct": is_correct,
        "messages": [{"role": "assistant", "content": message}]
    }
