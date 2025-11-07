"""
여러 JSON 파일을 하나로 합치는 스크립트
"""

import json
import os
from pathlib import Path


def merge_json_files(input_folder="output", output_file="all_questions.json"):
    """output 폴더의 모든 JSON 파일을 하나로 합칩니다."""

    # JSON 파일 목록
    json_files = sorted([f for f in os.listdir(input_folder) if f.endswith('.json')])

    if not json_files:
        print(f"❌ {input_folder} 폴더에 JSON 파일이 없습니다.")
        return

    print(f"발견된 JSON 파일: {len(json_files)}개\n")

    all_questions = []
    file_info = []

    for idx, json_file in enumerate(json_files, 1):
        json_path = os.path.join(input_folder, json_file)

        print(f"[{idx}/{len(json_files)}] {json_file} 읽는 중...")

        with open(json_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)

        # 각 문제에 출처 정보 추가
        exam_name = json_file.replace('.json', '')

        for question in questions:
            question['출처'] = exam_name

        all_questions.extend(questions)

        file_info.append({
            '파일명': json_file,
            '문제수': len(questions)
        })

        print(f"  → {len(questions)}개 문제 추가")

    # 통합 데이터 저장
    print(f"\n{'='*60}")
    print(f"통합 JSON 파일 저장 중...")
    print(f"{'='*60}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 저장 완료: {output_file}")
    print(f"✅ 총 {len(all_questions)}개 문제")

    # 요약 정보도 별도 저장
    summary = {
        '총_문제수': len(all_questions),
        '파일_정보': file_info,
        '출처별_문제수': {}
    }

    # 출처별 문제 수 계산
    for q in all_questions:
        source = q['출처']
        summary['출처별_문제수'][source] = summary['출처별_문제수'].get(source, 0) + 1

    summary_file = output_file.replace('.json', '_summary.json')
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"✅ 요약 정보 저장: {summary_file}")

    # 결과 출력
    print(f"\n{'='*60}")
    print(f"통합 결과")
    print(f"{'='*60}")
    for info in file_info:
        print(f"  - {info['파일명']}: {info['문제수']}개")
    print(f"\n  총 {len(all_questions)}개 문제가 하나의 파일로 통합되었습니다.")

    return all_questions


if __name__ == "__main__":
    # 스크립트가 있는 디렉토리로 이동
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    print("="*60)
    print("JSON 파일 통합 프로그램")
    print("="*60)
    print(f"작업 디렉토리: {os.getcwd()}\n")

    # 모든 JSON 파일 통합
    merge_json_files()
