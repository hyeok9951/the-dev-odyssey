from app import rag_processor

def get_faq_answer(user_query):
    """
    RAG 파이프라인 전체를 실행하여 최종 답변을 반환합니다.
    """
    # 1. 유사 FAQ 검색
    similar_faqs = rag_processor.find_similar_faqs(user_query, top_k=2)
    
    # 2. LLM으로 답변 생성
    final_answer = rag_processor.generate_answer_with_gemini(user_query, similar_faqs)
    
    return final_answer

if __name__ == "__main__":
    print("--- RAG 챗봇을 시작합니다. 종료하시려면 '종료'를 입력하세요. ---")
    
    while True:
        # 사용자로부터 질문 입력받기
        user_question = input("You: ")
        
        # 종료 조건 확인
        if user_question.lower() in ["종료", "exit", "quit"]:
            print("Bot: 챗봇을 종료합니다.")
            break
        
        # 답변 생성 및 출력
        answer = get_faq_answer(user_question)
        print(f"Bot: {answer}\n")