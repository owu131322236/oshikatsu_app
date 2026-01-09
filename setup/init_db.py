import sqlite3
import os
import atexit

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.close()
    print("DB初期化完了: db.sqlite3 が作成されました")

if __name__ == "__main__":
    init_db()
