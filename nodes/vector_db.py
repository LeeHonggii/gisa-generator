"""
벡터 DB 관련 노드
- Pinecone (우선) 또는 ChromaDB에 임베딩하여 저장
- 틀린 문제를 별도 컬렉션에 저장
"""

import json
import os
import time
from typing import Dict, List, Optional
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# Pinecone 사용 가능 여부 확인
USE_PINECONE = bool(os.getenv("PINECONE_API_KEY"))

if USE_PINECONE:
    try:
        from pinecone import Pinecone, ServerlessSpec
        print("✓ Pinecone 클라우드 벡터 DB 사용")
    except ImportError:
        print("⚠️ Pinecone 패키지 없음. ChromaDB 사용")
        USE_PINECONE = False

if not USE_PINECONE:
    import chromadb
    from chromadb.config import Settings
    print("✓ ChromaDB 로컬 벡터 DB 사용")


class QuestionVectorDB:
    """문제 벡터 DB 관리 클래스 (Pinecone 또는 ChromaDB)"""

    def __init__(self, persist_directory: str = "vector_store"):
        self.persist_directory = persist_directory
        self.use_pinecone = USE_PINECONE
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small"
        )
        self.dimension = 1536  # text-embedding-3-small 차원

        if self.use_pinecone:
            # Pinecone 클라이언트 초기화
            self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        else:
            # ChromaDB 클라이언트 초기화
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

    def _create_question_text(self, question: Dict) -> str:
        """문제를 텍스트로 변환"""
        text_parts = [
            f"문제 {question.get('문제번호', '')}번",
            f"출처: {question.get('출처', '')}",
            f"내용: {question.get('문제내용', '')}",
        ]

        if question.get('코드'):
            text_parts.append(f"코드: {question.get('코드', '')}")

        return "\n".join(text_parts)

    def _get_index_name(self, question_type: str) -> str:
        """인덱스/컬렉션 이름 생성"""
        return f"gisa-{question_type}-questions"

    # ==================== Pinecone 메서드 ====================

    def _initialize_pinecone_index(self, question_type: str, questions: List[Dict]):
        """Pinecone 인덱스 초기화 (배치 임베딩)"""
        index_name = self._get_index_name(question_type)

        # 기존 인덱스 삭제
        if index_name in self.pc.list_indexes().names():
            print(f"기존 Pinecone 인덱스 '{index_name}' 삭제")
            self.pc.delete_index(index_name)
            time.sleep(1)

        # 새 인덱스 생성
        print(f"Pinecone 인덱스 '{index_name}' 생성 중...")
        self.pc.create_index(
            name=index_name,
            dimension=self.dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )

        # 인덱스 준비 대기
        print(f"인덱스 준비 중...")
        time.sleep(5)
        index = self.pc.Index(index_name)

        # 문제들 임베딩하여 저장
        print(f"\n{question_type} 문제 {len(questions)}개를 Pinecone에 저장 중...")
        print(f"📊 배치 임베딩 생성 중... (OpenAI API 호출)")

        # 모든 문제 텍스트 생성 (배치)
        question_texts = [self._create_question_text(q) for q in questions]

        # 배치 임베딩 생성 (한 번의 API 호출!)
        embeddings = self.embeddings.embed_documents(question_texts)
        print(f"✅ 임베딩 생성 완료!")

        # 벡터 준비
        print(f"📤 Pinecone에 업로드 중...")
        vectors = []
        for i, (question, embedding) in enumerate(zip(questions, embeddings)):
            metadata = {
                "question_number": question.get('문제번호', 0),
                "source": question.get('출처', ''),
                "has_code": bool(question.get('코드')),
                "score": question.get('점수', 0),
                "answer": question.get('답', ''),
                "text": question_texts[i],
                "full_question": json.dumps(question, ensure_ascii=False)
            }

            vectors.append({
                "id": f"q_{i}",
                "values": embedding,
                "metadata": metadata
            })

        # 배치로 업로드
        index.upsert(vectors=vectors)
        print(f"✅ {len(questions)}개 문제 Pinecone 저장 완료!\n")

    def _get_pinecone_index(self, question_type: str):
        """Pinecone 인덱스 가져오기"""
        index_name = self._get_index_name(question_type)

        if index_name not in self.pc.list_indexes().names():
            raise ValueError(f"인덱스 '{index_name}'가 존재하지 않습니다.")

        return self.pc.Index(index_name)

    def _search_pinecone(self, index, query_text: str, top_k: int = 3) -> List[Dict]:
        """Pinecone에서 유사 문제 검색"""
        # 쿼리 임베딩
        query_embedding = self.embeddings.embed_query(query_text)

        # 검색
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )

        # 결과 변환
        questions = []
        for match in results['matches']:
            full_question = json.loads(match['metadata']['full_question'])
            questions.append(full_question)

        return questions

    def _save_to_pinecone_wrong(self, question: Dict, user_answer: str):
        """Pinecone에 틀린 문제 저장"""
        index_name = "gisa-wrong-questions"

        # 인덱스 없으면 생성
        if index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=index_name,
                dimension=self.dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
            time.sleep(5)

        index = self.pc.Index(index_name)

        # 문제 텍스트 생성
        question_text = self._create_question_text(question)
        embedding = self.embeddings.embed_query(question_text)

        # 저장
        doc_id = f"wrong_{int(time.time() * 1000)}"
        index.upsert(vectors=[{
            "id": doc_id,
            "values": embedding,
            "metadata": {
                "question_number": question.get('문제번호', 0),
                "user_answer": user_answer,
                "correct_answer": question.get('답', ''),
                "timestamp": time.time(),
                "text": question_text,
                "full_question": json.dumps(question, ensure_ascii=False)
            }
        }])

        print(f"❌ 틀린 문제가 Pinecone 복습 DB에 저장되었습니다.")

    # ==================== ChromaDB 메서드 ====================

    def _initialize_chroma_collection(self, question_type: str, questions: List[Dict]):
        """ChromaDB 컬렉션 초기화 (배치 임베딩)"""
        collection_name = f"{question_type}_questions"

        # 기존 컬렉션 삭제 후 재생성
        try:
            self.client.delete_collection(collection_name)
            print(f"기존 {collection_name} 컬렉션 삭제")
        except:
            pass

        # 컬렉션 생성
        collection = self.client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        print(f"\n{question_type} 문제 {len(questions)}개를 ChromaDB에 저장 중...")
        print(f"📊 배치 임베딩 생성 중... (OpenAI API 호출)")

        # 모든 문제 텍스트 생성 (배치)
        question_texts = [self._create_question_text(q) for q in questions]

        # 배치 임베딩 생성 (한 번의 API 호출!)
        embeddings = self.embeddings.embed_documents(question_texts)
        print(f"✅ 임베딩 생성 완료!")

        # ChromaDB에 배치로 저장
        print(f"💾 ChromaDB에 저장 중...")
        collection.add(
            ids=[f"q_{i}" for i in range(len(questions))],
            embeddings=embeddings,
            documents=question_texts,
            metadatas=[{
                "question_number": q.get('문제번호', 0),
                "source": q.get('출처', ''),
                "has_code": bool(q.get('코드')),
                "score": q.get('점수', 0),
                "answer": q.get('답', ''),
                "full_question": json.dumps(q, ensure_ascii=False)
            } for q in questions]
        )

        print(f"✅ {len(questions)}개 문제 ChromaDB 저장 완료!\n")
        return collection

    def _get_chroma_collection(self, question_type: str):
        """ChromaDB 컬렉션 가져오기"""
        collection_name = f"{question_type}_questions"
        return self.client.get_collection(collection_name)

    def _search_chroma(self, collection, query_text: str, top_k: int = 3) -> List[Dict]:
        """ChromaDB에서 유사 문제 검색"""
        # 쿼리 임베딩
        query_embedding = self.embeddings.embed_query(query_text)

        # 검색
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["metadatas"]
        )

        # 결과 변환
        questions = []
        if results['metadatas']:
            for metadata in results['metadatas'][0]:
                full_question = json.loads(metadata['full_question'])
                questions.append(full_question)

        return questions

    def _save_to_chroma_wrong(self, question: Dict, user_answer: str):
        """ChromaDB에 틀린 문제 저장"""
        # wrong_questions 컬렉션 가져오기 또는 생성
        try:
            collection = self.client.get_collection("wrong_questions")
        except:
            collection = self.client.create_collection(
                name="wrong_questions",
                metadata={"hnsw:space": "cosine"}
            )

        # 문제 텍스트 생성
        question_text = self._create_question_text(question)
        embedding = self.embeddings.embed_query(question_text)

        # 고유 ID 생성
        doc_id = f"wrong_{int(time.time() * 1000)}"

        # ChromaDB에 저장
        collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[question_text],
            metadatas=[{
                "question_number": question.get('문제번호', 0),
                "user_answer": user_answer,
                "correct_answer": question.get('답', ''),
                "timestamp": time.time(),
                "full_question": json.dumps(question, ensure_ascii=False)
            }]
        )

        print(f"❌ 틀린 문제가 ChromaDB 복습 DB에 저장되었습니다.")

    # ==================== 공통 인터페이스 ====================

    def initialize_questions(self, question_type: str = "code"):
        """문제들을 벡터 DB에 저장 (Pinecone 또는 ChromaDB)"""
        # JSON 파일 로드
        json_file = f"{question_type}_questions.json"
        if not os.path.exists(json_file):
            raise FileNotFoundError(f"{json_file} 파일이 없습니다.")

        with open(json_file, 'r', encoding='utf-8') as f:
            questions = json.load(f)

        if self.use_pinecone:
            self._initialize_pinecone_index(question_type, questions)
        else:
            self._initialize_chroma_collection(question_type, questions)

    def get_collection(self, question_type: str = "code"):
        """컬렉션/인덱스 가져오기"""
        if self.use_pinecone:
            return self._get_pinecone_index(question_type)
        else:
            return self._get_chroma_collection(question_type)

    def search_similar(self, question_type: str, query_text: str, top_k: int = 3) -> List[Dict]:
        """유사 문제 검색"""
        if self.use_pinecone:
            index = self._get_pinecone_index(question_type)
            return self._search_pinecone(index, query_text, top_k)
        else:
            collection = self._get_chroma_collection(question_type)
            return self._search_chroma(collection, query_text, top_k)

    def save_wrong_question(self, question: Dict, user_answer: str):
        """틀린 문제 저장"""
        if self.use_pinecone:
            self._save_to_pinecone_wrong(question, user_answer)
        else:
            self._save_to_chroma_wrong(question, user_answer)

    def get_collection_count(self, question_type: str) -> int:
        """컬렉션/인덱스의 문제 개수"""
        if self.use_pinecone:
            index = self._get_pinecone_index(question_type)
            stats = index.describe_index_stats()
            return stats.get('total_vector_count', 0)
        else:
            collection = self._get_chroma_collection(question_type)
            return collection.count()


# ==================== LangGraph 노드 함수들 ====================

def initialize_vector_db(state: Dict) -> Dict:
    """벡터 DB 초기화 노드"""

    question_type = state.get("question_type", "code")

    print(f"\n{'='*60}")
    print(f"벡터 DB 확인 중... (타입: {question_type})")
    print(f"{'='*60}")

    db = QuestionVectorDB()

    # 컬렉션이 없거나 비어있으면 초기화
    try:
        count = db.get_collection_count(question_type)

        if count == 0:
            print(f"컬렉션이 비어있습니다. 새로 생성합니다...")
            db.initialize_questions(question_type)
        else:
            db_type = "Pinecone" if db.use_pinecone else "ChromaDB"
            print(f"✓ 기존 {question_type} 벡터 DB 로드 완료 ({count}개 문제, {db_type})")
    except Exception as e:
        print(f"컬렉션이 없습니다. 새로 생성합니다... ({e})")
        db.initialize_questions(question_type)

    return {
        "vector_db_initialized": True,
        "messages": [{"role": "system", "content": f"{question_type} 벡터 DB 초기화 완료"}]
    }


def save_wrong_question(state: Dict) -> Dict:
    """틀린 문제 저장 노드"""

    generated_question = state.get("generated_question")
    user_answer = state.get("user_answer", "")

    if not generated_question:
        return state

    db = QuestionVectorDB()
    db.save_wrong_question(generated_question, user_answer)

    # wrong_questions 리스트에 추가
    wrong_questions = state.get("wrong_questions", [])
    wrong_questions.append({
        "question": generated_question,
        "user_answer": user_answer,
        "correct_answer": generated_question.get('답', '')
    })

    return {
        "wrong_questions": wrong_questions,
        "messages": [{"role": "system", "content": "틀린 문제가 복습 DB에 저장되었습니다."}]
    }
