# LangGraph 기반 문제 생성 시스템 구조

## 전체 흐름도

```
START
  ↓
[1. 문제 타입 선택]
  ↓
[2. 벡터 DB 초기화/로드]
  ↓
[3. Few-shot 예시 검색]
  ↓
[4. 문제 생성 (LLM)]
  ↓
[5. 사용자에게 문제 제시]
  ↓
[6. 사용자 답변 입력]
  ↓
[7. 답변 확인]
  ↓
정답? → [8. 축하 메시지] → END
  ↓ 오답
[9. 틀린 문제 벡터 DB 저장]
  ↓
[10. 해설 제공]
  ↓
END
```

## 노드 정의

### Node 1: 문제 타입 선택
- **입력**: 사용자 선택 (코드/이론)
- **출력**: question_type
- **역할**: 코드 문제 또는 이론 문제 선택

### Node 2: 벡터 DB 초기화
- **입력**: question_type
- **출력**: vector_db
- **역할**: ChromaDB 초기화 및 문제 임베딩

### Node 3: Few-shot 예시 검색
- **입력**: question_type, vector_db
- **출력**: similar_questions (3개)
- **역할**: 유사한 문제 3개 검색

### Node 4: 문제 생성
- **입력**: similar_questions
- **출력**: generated_question, correct_answer
- **역할**: GPT-4를 사용해 새 문제 생성

### Node 5: 문제 제시
- **입력**: generated_question
- **출력**: question_text
- **역할**: 사용자에게 문제 출력

### Node 6: 답변 입력
- **입력**: question_text
- **출력**: user_answer
- **역할**: 사용자 답변 받기

### Node 7: 답변 확인
- **입력**: user_answer, correct_answer
- **출력**: is_correct
- **역할**: 정답 여부 판단

### Node 8: 정답 처리
- **입력**: is_correct = True
- **출력**: success_message
- **역할**: 축하 메시지 출력

### Node 9: 오답 저장
- **입력**: is_correct = False, generated_question
- **출력**: saved
- **역할**: 틀린 문제를 벡터 DB에 저장

### Node 10: 해설 제공
- **입력**: generated_question, correct_answer
- **출력**: explanation
- **역할**: 정답 해설 제공

## State 정의

```python
class QuizState(TypedDict):
    question_type: str  # "code" or "theory"
    similar_questions: List[Dict]  # Few-shot 예시
    generated_question: str  # 생성된 문제
    correct_answer: str  # 정답
    user_answer: str  # 사용자 답변
    is_correct: bool  # 정답 여부
    explanation: str  # 해설
    wrong_questions: List[Dict]  # 틀린 문제 저장
```

## 디렉토리 구조

```
gisa-generator/
├── nodes/
│   ├── __init__.py
│   ├── vector_db.py         # 벡터 DB 관련 노드
│   ├── question_search.py   # Few-shot 검색 노드
│   ├── question_generate.py # 문제 생성 노드
│   ├── answer_check.py      # 답변 확인 노드
│   └── storage.py           # 틀린 문제 저장 노드
├── graph.py                 # LangGraph 그래프 정의
├── main.py                  # 메인 실행 파일
└── vector_store/            # 벡터 DB 저장 폴더
    ├── questions/           # 전체 문제 벡터
    └── wrong_questions/     # 틀린 문제 벡터
```
