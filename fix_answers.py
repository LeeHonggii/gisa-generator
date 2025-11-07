"""
잘못 파싱된 답을 수정하는 스크립트
"""

import json
import os


def fix_answers():
    """잘못 파싱된 답을 수정합니다."""

    print("="*60)
    print("잘못 파싱된 답 수정 프로그램")
    print("="*60)

    # 수정할 답 목록
    fixes = [
        {
            '출처': '1. 2024년2회_정보처리기사실기 기출문제',
            '문제번호': 16,
            '잘못된답': '- 30 -',
            '올바른답': '6.5'
        }
    ]

    # 모든 JSON 파일 수정
    files_to_fix = [
        'all_questions.json',
        'theory_questions.json',
        'output/1. 2024년2회_정보처리기사실기 기출문제.json'
    ]

    for file_path in files_to_fix:
        if not os.path.exists(file_path):
            print(f"⚠️  파일 없음: {file_path}")
            continue

        print(f"\n{file_path} 수정 중...")

        # 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)

        # 수정
        fixed_count = 0
        for q in questions:
            for fix in fixes:
                if (q.get('출처', '') == fix['출처'] and
                    q.get('문제번호') == fix['문제번호'] and
                    q.get('답', '').strip() == fix['잘못된답']):

                    old_answer = q['답']
                    q['답'] = fix['올바른답']
                    fixed_count += 1
                    print(f"  ✓ 문제 {fix['문제번호']}번 수정: \"{old_answer}\" → \"{fix['올바른답']}\"")

        if fixed_count > 0:
            # 파일 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(questions, f, ensure_ascii=False, indent=2)
            print(f"  ✅ {fixed_count}개 문제 수정 완료")
        else:
            print(f"  ℹ️  수정할 내용 없음")

    print(f"\n{'='*60}")
    print("수정 완료!")
    print(f"{'='*60}")


if __name__ == "__main__":
    # 스크립트가 있는 디렉토리로 이동
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    fix_answers()
