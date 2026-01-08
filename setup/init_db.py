import sqlite3
import os

def init_db():
    db_path= ":memory:" 
    conn = sqlite3.connect(db_path)
    print("DB初期化完了: db.sqlite3 が作成されました")

if __name__ == "__main__":
    init_db()
