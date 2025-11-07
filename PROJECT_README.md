# 🎓 정보처리기사 문제 생성 시스템 (LangGraph + RAG)

정보처리기사 실기 기출문제를 기반으로 AI가 새로운 문제를 생성하고, 틀린 문제를 복습할 수 있는 시스템입니다.

## ✨ 주요 기능

- 📝 **AI 문제 생성**: GPT-4를 사용하여 기출문제 패턴을 학습하고 새로운 문제 생성
- 🔍 **RAG 기반 Few-shot**: 벡터 DB에서 유사한 문제를 검색하여 Few-shot 예시로 활용
- 💾 **틀린 문제 저장**: 틀린 문제를 벡터 DB에 저장하여 나중에 복습
- 🔄 **LangGraph 모듈화**: 노드 단위로 구조화된 워크플로우

## 🏗️ 시스템 구조

### LangGraph 노드 흐름

```
START
  ↓
[벡터 DB 초기화] → 문제 임베딩 및 ChromaDB 저장
  ↓
[Few-shot 검색] → 유사한 문제 3개 검색
  ↓
[문제 생성] → GPT-4로 새 문제 생성
  ↓
[사용자 답변] → 답변 입력 받기
  ↓
[답변 확인] → 정답 여부 판단
  ↓
정답? → 🎉 축하
  ↓ (오답)
[틀린 문제 저장] → 벡터 DB에 저장
  ↓
[해설 제공]
  ↓
END
```

### 디렉토리 구조

```
gisa-generator/
├── main.py                      # 메인 실행 파일
├── graph.py                     # LangGraph 정의
├── state.py                     # State 정의
├── requirements.txt             # 필요 패키지
│
├── nodes/                       # LangGraph 노드 모듈
│   ├── __init__.py
│   ├── vector_db.py             # 벡터 DB 초기화 및 저장
│   ├── question_search.py       # Few-shot 검색
│   ├── question_generate.py     # 문제 생성
│   └── answer_check.py          # 답변 확인
│
├── code_questions.json          # 코드 문제 (35개)
├── theory_questions.json        # 이론 문제 (45개)
└── vector_store/                # 벡터 DB 저장소
    ├── questions/               # 전체 문제 벡터
    └── wrong_questions/         # 틀린 문제 벡터
```

## 🚀 설치 및 실행

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일에 OpenAI API 키 설정:

```
OPENAI_API_KEY=your-api-key-here
```

### 3. 실행

```bash
python main.py
```

## 📊 데이터 현황

- **전체 문제**: 80개
- **코드 문제**: 35개 (Python 18, C/C++ 12, Java 5)
- **이론 문제**: 45개
- **출처**: 2024~2025년 정보처리기사 실기 기출문제
