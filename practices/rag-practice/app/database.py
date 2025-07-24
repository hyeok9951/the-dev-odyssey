import psycopg2
from . import config

def get_db_connection():
    try:
        conn = psycopg2.connect(**config.DB_CONFIG)
        return conn
    except psycopg2.OperationalError as e:
        print(f"데이터베이스 연결 오류: {e}")
        return None