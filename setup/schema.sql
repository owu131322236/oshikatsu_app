
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS icons (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  image_path TEXT
);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- ユーザーIDを自動生成
    icon_id INTEGER DEFAULT 1,
    username TEXT NOT NULL, 
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL, -- パスワード必須
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 作成日時デフォルトは現在時刻
    FOREIGN KEY(icon_id) REFERENCES icons(id)
);
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    image_path TEXT NOT NULL,
    description TEXT,
    work_title TEXT,
    character_name TEXT,
    quantity INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS item_categories (
    item_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    PRIMARY KEY (item_id, category_id),
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);
