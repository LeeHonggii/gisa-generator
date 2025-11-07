"""
Few-shot 예시 검색 노드
- JSON에서 직접 랜덤 문제 선택 (벡터 DB 불필요)
"""

import json
import os
import random
from typing import Dict, List


def search_similar_questions(state: Dict) -> Dict:
    """유사한 문제 검색 노드 (Few-shot 예시용) - JSON 직접 읽기
    - 1개만 선택
    - 이미 푼 문제 제외
    """

    question_type = state.get("question_type", "code")

    print(f"\n{'='*60}")
    print(f"Few-shot 예시 검색 중... (타입: {question_type})")
    print(f"{'='*60}")

    # JSON 파일에서 직접 읽기
    json_file = f"{question_type}_questions.json"

    if not os.path.exists(json_file):
        print(f"❌ {json_file} 파일이 없습니다.")
        return {
            "similar_questions": [],
            "messages": [{"role": "system", "content": "문제 파일을 찾을 수 없습니다."}]
        }

    with open(json_file, 'r', encoding='utf-8') as f:
        all_questions = json.load(f)

    # 이미 푼 문제 로드
    solved_file = "solved_questions.json"
    solved_ids = set()
    if os.path.exists(solved_file):
        with open(solved_file, 'r', encoding='utf-8') as f:
            solved_data = json.load(f)
            solved_ids = set(solved_data.get(question_type, []))

    # 아직 안 푼 문제만 필터링
    unsolved_questions = [
        q for q in all_questions
        if q.get('문제번호') not in solved_ids
    ]

    if not unsolved_questions:
        print(f"⚠️ 모든 {question_type} 문제를 다 풀었습니다! 초기화가 필요합니다.")
        return {
            "similar_questions": [],
            "messages": [{"role": "system", "content": "모든 문제를 다 풀었습니다."}],
            "all_solved": True
        }

    # 랜덤하게 1개만 선택 (Few-shot 예시용)
    similar_questions = random.sample(unsolved_questions, 1)

    for i, full_question in enumerate(similar_questions):
        print(f"\n[Few-shot 예시]")
        print(f"  문제 {full_question.get('문제번호', '')}번")
        print(f"  출처: {full_question.get('출처', '')[:30]}...")
        print(f"  내용: {full_question.get('문제내용', '')[:60]}...")
        if full_question.get('코드'):
            print(f"  코드: 있음")

    print(f"\n✅ Few-shot 예시 1개 선택 완료 (남은 문제: {len(unsolved_questions)}/{len(all_questions)})\n")

    return {
        "similar_questions": similar_questions,
        "messages": [{"role": "system", "content": "Few-shot 예시 1개 선택"}],
        "all_solved": False
    }


def search_wrong_questions(state: Dict) -> Dict:
    """틀린 문제 중에서 복습할 문제 검색 - JSON 파일에서 읽기"""

    print(f"\n{'='*60}")
    print(f"복습할 문제 검색 중...")
    print(f"{'='*60}")

    # JSON 파일에서 틀린 문제 읽기
    wrong_file = "wrong_questions.json"

    try:
        if os.path.exists(wrong_file):
            with open(wrong_file, 'r', encoding='utf-8') as f:
                wrong_questions = json.load(f)

            # 최근 5개만 (역순)
            wrong_questions = wrong_questions[-5:]

            # 결과 출력
            if wrong_questions:
                for i, item in enumerate(wrong_questions):
                    print(f"\n[틀린 문제 {i+1}]")
                    print(f"  문제 {item['question'].get('문제번호', '')}번")
                    print(f"  내 답: {item['user_answer']}")
                    print(f"  정답: {item['correct_answer']}")
                print(f"\n✅ {len(wrong_questions)}개의 복습 문제를 찾았습니다.\n")
            else:
                print("아직 틀린 문제가 없습니다. 새로운 문제를 풀어보세요!\n")

            return {
                "wrong_questions": wrong_questions,
                "messages": [{"role": "system", "content": f"{len(wrong_questions)}개의 복습 문제를 찾았습니다."}]
            }
        else:
            print("아직 틀린 문제가 없습니다. 새로운 문제를 풀어보세요!\n")
            return {
                "wrong_questions": [],
                "messages": [{"role": "system", "content": "복습 문제가 없습니다."}]
            }

    except Exception as e:
        print(f"복습 문제를 읽을 수 없습니다: {e}\n")
        return {
            "wrong_questions": [],
            "messages": [{"role": "system", "content": "복습 문제가 없습니다."}]
        }
