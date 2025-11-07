# 🚀 설치 및 실행 가이드

## 1단계: 패키지 설치

\`\`\`bash
pip install -r requirements.txt
\`\`\`

필요한 패키지:
- pdfplumber: PDF 읽기
- openai: GPT-4 API
- chromadb: 벡터 DB
- langchain, langgraph: RAG 시스템
- python-dotenv: 환경 변수

## 2단계: 환경 변수 확인

\`.env\` 파일에 OpenAI API 키가 설정되어 있는지 확인:

\`\`\`
OPENAI_API_KEY=sk-...
\`\`\`

## 3단계: 실행

\`\`\`bash
python main.py
\`\`\`

## 트러블슈팅

### ImportError 발생 시

\`\`\`bash
pip install --upgrade langchain langgraph langchain-openai
\`\`\`

### ChromaDB 오류 시

\`\`\`bash
rm -rf vector_store/  # 벡터 DB 초기화
python main.py  # 재실행
\`\`\`

### OpenAI API 오류 시

- API 키가 올바른지 확인
- API 사용량 확인
- 인터넷 연결 확인
