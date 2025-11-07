"""
코드 문제와 이론 문제를 분류하는 스크립트
"""

import json
import os


def split_questions_by_type(input_file="all_questions.json"):
    """문제를 코드/이론으로 분류하여 저장합니다."""

    print("="*60)
    print("문제 유형별 분류 프로그램")
    print("="*60)

    # JSON 파일 읽기
    print(f"\n파일 읽기: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        all_questions = json.load(f)

    print(f"총 {len(all_questions)}개 문제 로드 완료\n")

    # 분류 기준:
    # 1. 코드 문제: "코드" 필드가 None이 아닌 경우
    # 2. 이론 문제: "코드" 필드가 None인 경우

    code_questions = []
    theory_questions = []

    for question in all_questions:
        if question.get('코드') and question['코드'] is not None:
            code_questions.append(question)
        else:
            theory_questions.append(question)

    # 통계
    print("="*60)
    print("분류 결과")
    print("="*60)
    print(f"\n📝 코드 문제: {len(code_questions)}개")
    print(f"📚 이론 문제: {len(theory_questions)}개")
    print(f"   총합: {len(all_questions)}개")

    # 코드 문제 저장
    code_file = "code_questions.json"
    with open(code_file, 'w', encoding='utf-8') as f:
        json.dump(code_questions, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 코드 문제 저장: {code_file}")

    # 이론 문제 저장
    theory_file = "theory_questions.json"
    with open(theory_file, 'w', encoding='utf-8') as f:
        json.dump(theory_questions, f, ensure_ascii=False, indent=2)
    print(f"✅ 이론 문제 저장: {theory_file}")

    # 상세 통계 생성
    code_stats = analyze_questions(code_questions, "코드")
    theory_stats = analyze_questions(theory_questions, "이론")

    # 통계 출력
    print(f"\n{'='*60}")
    print("코드 문제 상세 분석")
    print(f"{'='*60}")
    print_stats(code_stats)

    print(f"\n{'='*60}")
    print("이론 문제 상세 분석")
    print(f"{'='*60}")
    print_stats(theory_stats)

    # 통계 정보 저장
    stats = {
        "총_문제수": len(all_questions),
        "코드_문제": {
            "개수": len(code_questions),
            "상세": code_stats
        },
        "이론_문제": {
            "개수": len(theory_questions),
            "상세": theory_stats
        }
    }

    stats_file = "questions_stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 통계 정보 저장: {stats_file}")

    return code_questions, theory_questions


def analyze_questions(questions, category):
    """문제 유형별 상세 분석"""
    stats = {
        "출처별": {},
        "언어별": {},
        "답_있음": 0,
        "해설_있음": 0
    }

    # 출처별 카운트
    for q in questions:
        source = q.get('출처', '알 수 없음')
        stats["출처별"][source] = stats["출처별"].get(source, 0) + 1

    # 언어별 카운트 (코드 문제만)
    if category == "코드":
        for q in questions:
            code = q.get('코드', '')
            if code:
                lang = detect_language(code)
                stats["언어별"][lang] = stats["언어별"].get(lang, 0) + 1

    # 답/해설 통계
    for q in questions:
        if q.get('답'):
            stats["답_있음"] += 1
        if q.get('해설'):
            stats["해설_있음"] += 1

    return stats


def detect_language(code):
    """코드 언어 자동 감지"""
    code = code.strip()

    if code.startswith('def ') or 'print(' in code or 'import ' in code:
        return 'Python'
    elif 'public class' in code or 'public static' in code or 'System.out' in code:
        return 'Java'
    elif '#include' in code or 'printf(' in code or 'scanf(' in code:
        return 'C/C++'
    else:
        return '기타'


def print_stats(stats):
    """통계 정보 출력"""
    print(f"\n출처별 분포:")
    for source, count in sorted(stats["출처별"].items()):
        short_name = source.split('_')[0]  # 짧게 표시
        print(f"  - {short_name}: {count}개")

    if stats["언어별"]:
        print(f"\n언어별 분포:")
        for lang, count in sorted(stats["언어별"].items()):
            print(f"  - {lang}: {count}개")

    print(f"\n답/해설:")
    print(f"  - 답 있음: {stats['답_있음']}개")
    print(f"  - 해설 있음: {stats['해설_있음']}개")


if __name__ == "__main__":
    # 스크립트가 있는 디렉토리로 이동
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    print(f"작업 디렉토리: {os.getcwd()}\n")

    # 문제 분류
    code_questions, theory_questions = split_questions_by_type()

    print(f"\n{'='*60}")
    print("완료!")
    print(f"{'='*60}")
    print(f"\n생성된 파일:")
    print(f"  - code_questions.json (코드 문제)")
    print(f"  - theory_questions.json (이론 문제)")
    print(f"  - questions_stats.json (통계 정보)")
