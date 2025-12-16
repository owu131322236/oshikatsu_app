import sqlite3
import os

def init_db():
    db_path = os.path.join(os.path.dirname(__file__), "app.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    with open("schema.sql", "r", encoding="utf-8") as f:
        cursor.executescript(f.read())

    default_username = "test"
    default_password = "test123"  
    cursor.execute(
        "INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
        (default_username, default_password)
    )

    conn.commit()
    conn.close()
    print("DB初期化完了: db.sqlite3 が作成されました")

if __name__ == "__main__":
    init_db()
