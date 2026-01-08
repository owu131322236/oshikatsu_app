import sqlite3
import os

def init_db():
    db_path= ":memory:" 
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    with open("schema.sql", "r", encoding="utf-8") as f:
        cursor.executescript(f.read())

    # 状態テーブル
    cursor.executemany(
        "INSERT OR IGNORE INTO categories (id, name) VALUES(?, ?)",
        [
            (1, "アクリルスタンド"),
            (2, "缶バッジ"),
            (3, "キーホルダー"),
            (4, "フィギュア"),
        ]
    )
    cursor.executemany(
        "INSERT OR IGNORE INTO icons(id, image_path) VALUES(?,?)",
        [
            (1,"barcode.png"),
            (2,"bulbs.png"),
            (3, "flower.png"),
            (4,"magnifying_glass.png"),
            (5, "zombie.png")
        ]
    )
    #初期テーブル
    default_username = "test"
    default_email = "test@example.com"
    default_password = "test123"
    cursor.execute(
        "INSERT OR IGNORE INTO users (username, email, password) VALUES (?, ?, ?)",
        (default_username, default_email, default_password)
    )
    cursor.executemany(
        "INSERT OR IGNORE INTO items (id, user_id, name, image_path) VALUES(?, ?, ?, ?)",
        [
            (1, 1, "アクスタA", "boy_keychain.png"),
            (2, 1, "フィギュアA", "girl_figure.png"),
            (3, 1, "フィギュアB", "blue_figure.png"),
            (4, 1, "フィギュアC", "white_figure.png"),
            (5, 1, "ぱしゃこれ(かふか)", "kafuka_photo.png"),
            (6, 1, "ぱしゃこれ(なぎ)", "mikoto_photo.png"),
        ]
        
    )
    cursor.executemany(
        "INSERT OR IGNORE INTO item_categories (item_id, category_id) VALUES (?, ?)",
        [
            (1, 1),
            (2, 4),
            (3, 4),
            (4, 4),
            (5, 2),
            (6, 2),
        ]
    )
    conn.commit()
    conn.close()
    print("DB初期化完了: db.sqlite3 が作成されました")

if __name__ == "__main__":
    init_db()
