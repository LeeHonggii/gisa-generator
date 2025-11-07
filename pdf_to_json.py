"""
정보처리기사 PDF 파일을 JSON으로 변환하는 스크립트

사용법:
    python pdf_to_json.py
"""

import pdfplumber
import json
import re
import os


def read_pdf_text(file_path):
    """PDF 파일의 모든 텍스트를 읽어옵니다."""
    all_text = []

    with pdfplumber.open(file_path) as pdf:
        print(f"  총 페이지 수: {len(pdf.pages)}")

        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if text:
                all_text.append(text)

    return '\n'.join(all_text)


def split_questions_and_answers(text):
    """PDF 텍스트를 문제 섹션과 답/해설 섹션으로 분리합니다."""

    # "기출문제 정답 및 해설" 또는 유사한 패턴 찾기
    split_patterns = [
        r'기출문제\s*정답\s*및\s*해설',
        r'정답\s*및\s*해설',
        r'정답\s*해설',
        r'모범\s*답안'
    ]

    for pattern in split_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            questions_section = text[:match.start()].strip()
            answers_section = text[match.start():].strip()
            print(f"  ✓ '{pattern}' 패턴으로 섹션 분리 성공")
            print(f"    - 문제 섹션: {len(questions_section)} 문자")
            print(f"    - 답/해설 섹션: {len(answers_section)} 문자")
            return questions_section, answers_section

    print("  ⚠ 답/해설 섹션을 찾지 못했습니다.")
    return text, ""


def parse_answers(answers_text):
    """답/해설 섹션에서 각 문제의 답과 해설을 추출합니다."""
    answers_dict = {}

    # [문제 숫자] 패턴으로 분리
    pattern = r'\[문제\s+(\d+)\](.*?)(?=\[문제\s+\d+\]|$)'
    matches = re.finditer(pattern, answers_text, re.DOTALL)

    for match in matches:
        question_num = int(match.group(1))
        content = match.group(2).strip()

        # 답 추출
        lines = content.split('\n')
        answer = ""
        explanation = []

        in_explanation = False

        for i, line in enumerate(lines):
            line = line.strip()

            # [해설] 시작
            if re.match(r'^\[해설\]', line):
                in_explanation = True
                continue

            # 명시적인 "답:" 패턴
            answer_match = re.match(r'^답\s*[:：]\s*(.*)', line)
            if answer_match and not answer:
                answer = answer_match.group(1).strip()
                continue

            # [문제 N] 바로 다음이 답인 경우
            if not answer and line and not line.startswith('※') and not line.startswith('['):
                # 너무 긴 줄은 답이 아닐 가능성이 높음
                if len(line) < 100 and not re.match(r'^(public|def|class|import|from)', line):
                    answer = line
                    continue

            # 해설 내용 수집
            if in_explanation and line:
                explanation.append(line)

        answers_dict[question_num] = {
            "답": answer,
            "해설": '\n'.join(explanation) if explanation else ""
        }

    return answers_dict


def parse_questions_improved(questions_text):
    """문제 섹션에서 문제들을 파싱합니다 (답은 제외)."""
    questions = []

    # "문제 숫자" 패턴으로 분리
    pattern = r'문제\s+(\d+)\s+(.*?)(?=문제\s+\d+|$)'
    matches = re.finditer(pattern, questions_text, re.DOTALL)

    for match in matches:
        question_num = int(match.group(1))
        content = match.group(2).strip()

        # 점수 추출
        score_match = re.search(r'\((\d+)점\)', content)
        score = int(score_match.group(1)) if score_match else 0

        # 코드 블록 추출 (여러 언어 지원)
        code = None
        code_patterns = [
            r'((?:def|class)\s+\w+.*?)(?=답\s*[:：]|$)',  # Python
            r'((?:public|private|protected)\s+(?:static\s+)?(?:class|void|int|String).*?)(?=답\s*[:：]|$)',  # Java
            r'(#include.*?int\s+main.*?)(?=답\s*[:：]|$)',  # C/C++
        ]

        for code_pattern in code_patterns:
            code_match = re.search(code_pattern, content, re.DOTALL)
            if code_match:
                code = code_match.group(1).strip()
                # 코드 부분을 문제 내용에서 제거
                content = content.replace(code, '').strip()
                break

        # "답 :" 이후 내용 제거 (혹시 있다면)
        content = re.sub(r'답\s*[:：].*$', '', content, flags=re.MULTILINE | re.DOTALL).strip()

        question_data = {
            "문제번호": question_num,
            "문제내용": content,
            "코드": code,
            "점수": score,
            "답": "",
            "해설": ""
        }

        questions.append(question_data)

    return questions


def merge_questions_and_answers(questions, answers_dict):
    """문제 리스트와 답 딕셔너리를 합칩니다."""

    for question in questions:
        question_num = question['문제번호']

        if question_num in answers_dict:
            question['답'] = answers_dict[question_num]['답']
            question['해설'] = answers_dict[question_num]['해설']
        else:
            print(f"  ⚠ 문제 {question_num}의 답을 찾을 수 없습니다.")

    return questions


def save_questions_to_json(questions, output_file):
    """문제들을 JSON 파일로 저장합니다."""
    # 출력 디렉토리가 없으면 생성
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    print(f"  ✓ 저장 완료: {output_file}")
    print(f"  ✓ 총 {len(questions)}개 문제 저장")


def pdf_to_json_complete(pdf_path, output_path):
    """PDF 파일을 읽어서 답/해설이 포함된 JSON으로 변환"""

    print("="*60)
    print(f"처리 중: {os.path.basename(pdf_path)}")
    print("="*60)

    # 1. PDF 읽기
    print("\n[1/5] PDF 읽기 중...")
    full_text = read_pdf_text(pdf_path)

    # 2. 문제 섹션과 답/해설 섹션 분리
    print("\n[2/5] 섹션 분리 중...")
    questions_text, answers_text = split_questions_and_answers(full_text)

    # 3. 문제 파싱
    print("\n[3/5] 문제 파싱 중...")
    questions = parse_questions_improved(questions_text)
    print(f"  → {len(questions)}개 문제 발견")

    # 4. 답/해설 파싱
    print("\n[4/5] 답/해설 파싱 중...")
    if answers_text:
        answers_dict = parse_answers(answers_text)
        print(f"  → {len(answers_dict)}개 답/해설 발견")

        # 5. 문제와 답 매칭
        print("\n[5/5] 문제와 답 매칭 중...")
        complete_questions = merge_questions_and_answers(questions, answers_dict)
    else:
        print("  → 답/해설 섹션 없음")
        complete_questions = questions

    # 6. JSON 저장
    print("\n[완료] JSON 파일 저장 중...")
    save_questions_to_json(complete_questions, output_path)

    return complete_questions


def process_all_pdfs(data_folder="data", output_folder="output"):
    """data 폴더의 모든 PDF를 JSON으로 변환"""

    # output 폴더 생성
    os.makedirs(output_folder, exist_ok=True)

    # PDF 파일 목록
    pdf_files = sorted([f for f in os.listdir(data_folder) if f.endswith('.pdf')])

    if not pdf_files:
        print(f"❌ {data_folder} 폴더에 PDF 파일이 없습니다.")
        return {}

    print(f"\n발견된 PDF 파일: {len(pdf_files)}개\n")
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"  {i}. {pdf_file}")
    print()

    all_results = {}

    for idx, pdf_file in enumerate(pdf_files, 1):
        print(f"\n\n{'#'*60}")
        print(f"# [{idx}/{len(pdf_files)}] {pdf_file}")
        print(f"{'#'*60}\n")

        pdf_path = os.path.join(data_folder, pdf_file)
        output_name = pdf_file.replace('.pdf', '.json')
        output_path = os.path.join(output_folder, output_name)

        try:
            questions = pdf_to_json_complete(pdf_path, output_path)
            all_results[pdf_file] = {
                "status": "success",
                "count": len(questions),
                "output": output_path
            }
        except Exception as e:
            import traceback
            print(f"\n❌ 오류 발생: {e}")
            print(traceback.format_exc())
            all_results[pdf_file] = {
                "status": "error",
                "error": str(e)
            }

    # 처리 결과 요약
    print("\n\n" + "="*60)
    print("최종 처리 결과 요약")
    print("="*60)

    success_count = 0
    error_count = 0

    for pdf, result in all_results.items():
        if result["status"] == "success":
            print(f"✓ {pdf}: {result['count']}개 문제")
            success_count += 1
        else:
            print(f"✗ {pdf}: {result['error']}")
            error_count += 1

    print(f"\n성공: {success_count}개, 실패: {error_count}개")
    print(f"\nJSON 파일 저장 위치: {os.path.abspath(output_folder)}/")

    return all_results


if __name__ == "__main__":
    # 스크립트가 있는 디렉토리로 이동
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    print("="*60)
    print("정보처리기사 PDF → JSON 변환 프로그램")
    print("="*60)
    print(f"작업 디렉토리: {os.getcwd()}")

    # 모든 PDF 파일 처리
    results = process_all_pdfs()
