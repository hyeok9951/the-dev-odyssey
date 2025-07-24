import psycopg2
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from . import config, database

# 1. 임베딩 모델 로드
embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# 2. Gemini 모델 설정
genai.configure(api_key=config.GEMINI_API_KEY)
llm = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")

def find_similar_faqs(user_query, top_k=3):
    query_embedding = embedding_model.encode(user_query).tolist()
    results = []
    conn = None
    cur = None
    try:
        conn = database.get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT question, answer FROM faq_data ORDER BY embedding <=> %s LIMIT %s", (str(query_embedding), top_k))
            results = cur.fetchall()
    except psycopg2.Error as e:
        print(f"검색 중 데이터베이스 오류: {e}")
    finally:
        if cur: cur.close()
        if conn: conn.close()
    return results

def generate_answer_with_gemini(user_query, context_faqs):
    if not context_faqs:
        return "죄송합니다. 관련 정보를 찾을 수 없어 답변을 드릴 수 없습니다."

    context = "\n".join([f"- Q: {q}\n  A: {a}" for q, a in context_faqs])
    prompt = f"""
    당신은 사용자 문의에 답변하는 친절한 AI 상담원입니다.
    아래 '참고 FAQ' 내용을 기반으로 사용자의 '질문'에 대해 답변해주세요.
    참고 내용으로 답변할 수 없다면, 정보가 부족하다고 솔직하게 말해주세요.

    [참고 FAQ]
    {context}

    [질문]
    {user_query}

    [답변]
    """
    try:
        response = llm.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API 오류: {e}")
        return "답변 생성 중 오류가 발생했습니다."