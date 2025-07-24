import os
import sys
import csv
import psycopg2
from sentence_transformers import SentenceTransformer

# app 모듈을 임포트하기 위해 프로젝트 루트 디렉토리를 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import config

def load_faqs_from_csv(file_path):
    faqs = []
    with open(file_path, mode='r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            faqs.append(row)
    return faqs

def initialize_database():
    faq_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'faqs.csv')
    faqs = load_faqs_from_csv(faq_file_path)
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    conn = None
    cur = None

    try:
        conn = psycopg2.connect(**config.DB_CONFIG)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS faq_data (id SERIAL PRIMARY KEY, question TEXT, answer TEXT, embedding VECTOR(384));")
        cur.execute("TRUNCATE TABLE faq_data;")
        print("테이블 준비 완료, 데이터 삽입 시작...")

        for faq in faqs:
            question_embedding = model.encode(faq['question']).tolist()
            cur.execute("INSERT INTO faq_data (question, answer, embedding) VALUES (%s, %s, %s)", (faq['question'], faq['answer'], question_embedding))
        
        conn.commit()
        print(f"총 {len(faqs)}개의 FAQ 데이터가 DB에 저장되었습니다.")

    except psycopg2.Error as e:
        print(f"데이터베이스 오류: {e}")
    finally:
        if cur: cur.close()
        if conn: conn.close()

if __name__ == "__main__":
    initialize_database()