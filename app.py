from flask import Flask, request, render_template, session, redirect, jsonify
from routes.chatgpt import get_chatgpt_response, build_prompt
from routes.gemini import ask_gemini
from routes.auth import auth_bp
from routes.items import items_bp
from db import get_db
import json
import atexit
import os
import re
# from db import get_db, close_db

app = Flask(__name__)
# app.teardown_appcontext(close_db)
app.secret_key = "your_secret_key"
app.register_blueprint(auth_bp)
app.register_blueprint(items_bp)

DB_PATH = "setup/app.db"
UNUSED_DB_PATH = "app.db"
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f"{DB_PATH} を削除しました（起動時）")
def cleanup():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"{DB_PATH} を削除しました")
    if os.path.exists(UNUSED_DB_PATH):
        os.remove(UNUSED_DB_PATH)
        print(f"{UNUSED_DB_PATH} を削除しました")
atexit.register(cleanup)

def extract_json(text):
    if not text:
        return None
    match = re.search(r"\{[\s\S]*\}", text)
    return match.group(0) if match else None


def valid_kw(s):
    NG = ["不明", "未定義", "作品名不明", "キャラクター名不明"]
    return s and s not in NG


@app.context_processor
def inject_user():
    icon_id = session.get("icon_id", 1)
    username = session.get("username", "None")
    initial = username[0].upper() if username else "N" 
    db = get_db()
    icon_row = db.execute("SELECT image_path FROM icons WHERE id = ?", (icon_id,)).fetchone()
    icon_path = icon_row["image_path"] 
    return dict(username=session.get("username"), initial=initial, icon_path=icon_path)

# ======================
# ログイン（DB方式）
# ======================
@app.route("/login", methods=["GET", "POST"])
def login():
    # GET：ログイン画面表示
    if request.method == "GET":
        if "user_id" in session:
            return redirect("/")
        return render_template("login.html")

@app.route('/signup')
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    db = get_db()
    icons = db.execute("SELECT id, image_path FROM icons").fetchall()
    if request.method == 'POST':
        icon_id = request.form.get("icon", 1)
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        password_confirm = request.form.get("password_confirm")

        row = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if row:
            return jsonify({"status": "error", "message": "すでに登録済みのメールアドレスです"})

        if password != password_confirm:
            return jsonify({"status": "error", "message": "パスワードが一致しません"})

        db.execute(
            "INSERT INTO users (icon_id, username, email, password) VALUES (?, ?, ?, ?)",
            (icon_id, username, email, password)
        )
        db.commit()
        return render_template("index.html",icons=icons)

    return render_template("signup.html",icons=icons)

    # # POST：ログイン処理
    # username = request.form.get("username", "")
    # password = request.form.get("password", "")

    # db = get_db()
    # user = db.execute(
    #     "SELECT id, username, password FROM users WHERE username = ?",
    #     (username,)
    # ).fetchone()

    # if user is None:
    #     return jsonify({
    #         "status": "error",
    #         "message": "ユーザー名が存在しません"
    #     }), 401

    # if password != user["password"]:
    #     return jsonify({
    #         "status": "error",
    #         "message": "パスワードが違います"
    #     }), 401

    # # ログイン成功
    # session["user_id"] = user["id"]        # ← DBのid（整数）
    # session["username"] = user["username"]

    # return jsonify({"status": "success"})

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        # ログイン済みならトップへ
        if "user_id" in session:
            return redirect("/")
        return render_template("register.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")

    if not username or not password:
        return jsonify({"status": "error", "message": "ユーザー名とパスワードは必須です"}), 400

    if password != confirm:
        return jsonify({"status": "error", "message": "パスワードが一致しません"}), 400

    db = get_db()

    # 同じユーザー名があるかチェック
    exists = db.execute(
        "SELECT id FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    if exists is not None:
        return jsonify({"status": "error", "message": "そのユーザー名は既に使われています"}), 400

    # 登録
    db.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (username, password)
    )
    db.commit()

    # 登録したユーザーでログイン状態にする
    user = db.execute(
        "SELECT id, username FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    session["user_id"] = user["id"]
    session["username"] = user["username"]

    return jsonify({"status": "success"})


# ログアウト
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ======================
# ログイン必須ページ
# ======================
@app.route("/")
def index():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("index.html")


# @app.route("/upload", methods=["POST"])
# def upload():
#     if "user_id" not in session:
#         return jsonify({"status": "error", "message": "ログインしてください"}), 401
#     return ask_gemini(request)
@app.route('/items/create')
def item_creare():

    if "user_id" not in session:
        return redirect("/login")
    return render_template("item_new.html")

@app.route('/items/search')
def item_search():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("item_search.html")

@app.route('/account/edit', methods=['GET', 'POST'])
def account_edit():
    if "user_id" not in session:
        return redirect("/login")
    db = get_db()
    user_id = session['user_id']
    icons = db.execute("SELECT id, image_path FROM icons").fetchall()
    user = db.execute("SELECT username, email, icon_id FROM users WHERE id = ?", (user_id,)).fetchone()
    if request.method == 'POST':
        db = get_db()
        user_id = session['user_id']
        icon = request.form.get('icon')
        username = request.form.get('username')
        email =request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        password_confirm = request.form.get('confirm_password')

        # パスワード変更
        if new_password or password_confirm:
            if not current_password:
                return jsonify({"status": "error", "message": "現在のパスワードを入力してください"})

            row = db.execute(
                'SELECT password FROM users WHERE id = ?',
                (user_id,)
            ).fetchone()

            if not row or current_password != row['password']:
                return jsonify({"status": "error", "message": "現在のパスワードが間違っています"})

            if new_password != password_confirm:
                return jsonify({"status": "error", "message": "パスワードが一致しません"})

            db.execute(
                'UPDATE users SET password = ? WHERE id = ?',
                (new_password, user_id)
            )
        if icon:
            db.execute(
                'UPDATE users SET icon_id = ? WHERE id = ?',
                (icon, user_id)
            )

        if username:
            db.execute(
                'UPDATE users SET username = ? WHERE id = ?',
                (username, user_id)
            )
        if email:
            db.execute(
                'UPDATE users SET email = ? WHERE id = ?',
                (email, user_id)
            )

        db.commit()
        return jsonify({"status": "success"})
    
    return render_template('account_edit.html',
        icons=icons,
        username=user["username"],
        email=user["email"],
        selected_icon=user["icon_id"])  

@app.route("/upload", methods=["POST"])
def upload():
    data = request.get_json(force=True)
    imgurl = data.get("img_base64")

    if not imgurl:
        return render_template(
            "components/item_list.html",
            items=[],
            message="画像が取得できませんでした。"
        )

    db = get_db()

    # --- category一覧をAIに渡す ---
    categories = db.execute("SELECT name FROM categories").fetchall()
    category_names = [c["name"] for c in categories]

    prompt = build_prompt(category_names)

    ai_raw = get_chatgpt_response(imgurl, prompt)
    print("AI RAW:", ai_raw)

    # --- JSON抽出 ---
    json_text = extract_json(ai_raw)
    if not json_text:
        return render_template(
            "components/item_list.html",
            items=[],
            message="画像を判別できませんでした。別の角度から撮影してみてください。"
        )

    try:
        ai_result = json.loads(json_text)
    except json.JSONDecodeError:
        return render_template(
            "components/item_list.html",
            items=[],
            message="画像を判別できませんでした。別の角度から撮影してみてください。"
        )

    category = ai_result.get("category")
    keywords = ai_result.get("keywords", [])
    title = ai_result.get("title", "")
    character = ai_result.get("character", "")

    where = []
    params = []

    # --- category（OR条件の1つ） ---
    if valid_kw(category):
        where.append("categories.name = ?")
        params.append(category)

    # --- keywords / title / character ---
    for kw in keywords + [title, character]:
        if not valid_kw(kw):
            continue
        where.append("(items.name LIKE ? OR items.description LIKE ?)")
        params.extend([f"%{kw}%", f"%{kw}%"])

    if not where:
        return render_template(
            "components/item_list.html",
            items=[],
            message="検索条件を生成できませんでした。"
        )

    sql = f"""
    SELECT DISTINCT items.*
    FROM items
    JOIN item_categories ON items.id = item_categories.item_id
    JOIN categories ON categories.id = item_categories.category_id
    WHERE {" OR ".join(where)}
    """

    items = db.execute(sql, params).fetchall()

    if not items:
        return render_template(
            "components/item_list.html",
            items=[],
            message="該当するアイテムが見つかりませんでした。"
        )

    return render_template(
        "components/item_list.html",
        items=items
    )


if __name__ == "__main__": #起動用
    app.run(host="0.0.0.0", port=5001, debug=True)
