import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# 環境変数から URL を取得
DATABASE_URL = "postgresql://postgres.ocjgdulbfpqvgqmyetqn:fozguf-Jaxjik-2cofta@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"
if not DATABASE_URL:
    raise ValueError("DATABASE_URL が設定されていません")

# SQLAlchemy Engine 作成
engine = create_engine(DATABASE_URL, echo=True, future=True)

# セッション作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 簡単な接続テスト
def test_connection():
    try:
        with SessionLocal() as db:
            result = db.execute(text("SELECT 1")).scalar()
            print("接続成功:", result)
    except Exception as e:
        print("接続失敗:", e)

if __name__ == "__main__":
    test_connection()
