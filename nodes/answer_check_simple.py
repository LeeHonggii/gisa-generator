"""
답변 확인 및 틀린 문제 저장 노드 (간소화 버전)
- JSON 파일로 틀린 문제 저장
"""

import json
import os
import time
from typing import Dict


def check_answer(state: Dict) -> Dict:
    """답변 확인 노드 + 푼 문제 저장"""

    user_answer = (state.get("user_answer") or "").strip()
    correct_answer = (state.get("correct_answer") or "").strip()
    generated_question = state.get("generated_question", {})
    question_type = state.get("question_type", "code")

    print(f"\n{'='*60}")
    print(f"답변 확인 중...")
    print(f"{'='*60}")
    print(f"사용자 답변: {user_answer}")
    print(f"정답: {correct_answer}")

    # 정답이 없는 경우 에러 처리
    if not correct_answer:
        print(f"❌ 에러: 정답이 없습니다. state: {state}")
        return {
            "is_correct": False,
            "messages": [{"role": "system", "content": "정답 정보가 없습니다."}]
        }

    # 정규화 (공백 제거, 소문자 변환)
    def normalize_answer(ans: str) -> str:
        return ans.lower().replace(" ", "").replace("\n", "")

    user_normalized = normalize_answer(user_answer)
    correct_normalized = normalize_answer(correct_answer)

    # 정답 확인 (여러 정답 지원: 쉼표로 구분)
    correct_answers = [normalize_answer(a.strip()) for a in correct_answer.split(',')]

    is_correct = user_normalized in correct_answers

    if is_correct:
        print("✅ 정답입니다!")
    else:
        print("❌ 틀렸습니다.")

    # Few-shot으로 사용된 원본 문제를 "푼 문제"로 저장
    similar_questions = state.get("similar_questions", [])
    if similar_questions:
        solved_file = "solved_questions.json"

        # 기존 데이터 로드
        if os.path.exists(solved_file):
            with open(solved_file, 'r', encoding='utf-8') as f:
                solved_data = json.load(f)
        else:
            solved_data = {"code": [], "theory": []}

        # Few-shot 문제 ID 저장
        for q in similar_questions:
            q_id = q.get('문제번호')
            if q_id and q_id not in solved_data.get(question_type, []):
                if question_type not in solved_data:
                    solved_data[question_type] = []
                solved_data[question_type].append(q_id)

        # 저장
        with open(solved_file, 'w', encoding='utf-8') as f:
            json.dump(solved_data, f, ensure_ascii=False, indent=2)

        print(f"📝 푼 문제 저장 완료 (문제 {similar_questions[0].get('문제번호', '')}번)")

    return {
        "is_correct": is_correct,
        "messages": [{"role": "system", "content": f"정답 여부: {is_correct}"}]
    }


def save_wrong_question(state: Dict) -> Dict:
    """틀린 문제를 JSON 파일에 저장"""

    generated_question = state.get("generated_question")
    user_answer = state.get("user_answer", "")

    if not generated_question:
        return state

    print(f"\n{'='*60}")
    print(f"틀린 문제 저장 중...")
    print(f"{'='*60}")

    # JSON 파일에 저장
    wrong_file = "wrong_questions.json"

    # 기존 데이터 로드
    if os.path.exists(wrong_file):
        with open(wrong_file, 'r', encoding='utf-8') as f:
            wrong_questions = json.load(f)
    else:
        wrong_questions = []

    # 새 틀린 문제 추가
    wrong_questions.append({
        "question": generated_question,
        "user_answer": user_answer,
        "correct_answer": generated_question.get('답', ''),
        "timestamp": time.time()
    })

    # 저장
    with open(wrong_file, 'w', encoding='utf-8') as f:
        json.dump(wrong_questions, f, ensure_ascii=False, indent=2)

    print(f"❌ 틀린 문제가 저장되었습니다. (총 {len(wrong_questions)}개)")

    return {
        "wrong_questions": wrong_questions,
        "messages": [{"role": "system", "content": "틀린 문제가 저장되었습니다."}]
    }
