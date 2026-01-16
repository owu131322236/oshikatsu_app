from flask import Flask, request, render_template, session, redirect, jsonify
from routes.chatgpt import get_chatgpt_response, build_prompt
from routes.gemini import ask_gemini
from routes.auth import auth_bp
from routes.items import items_bp
from db import SessionLocal
from sqlalchemy import text
import json
import atexit
import os
import re

app = Flask(__name__)
# app.teardown_appcontext(close_db)
app.secret_key = "your_secret_key"
app.register_blueprint(auth_bp)
app.register_blueprint(items_bp)

# DB_PATH = "setup/app.db"
# UNUSED_DB_PATH = "app.db"
# if os.path.exists(DB_PATH):
#     os.remove(DB_PATH)
#     print(f"{DB_PATH} を削除しました（起動時）")
# def cleanup():
#     if os.path.exists(DB_PATH):
#         os.remove(DB_PATH)
#         print(f"{DB_PATH} を削除しました")
#     if os.path.exists(UNUSED_DB_PATH):
#         os.remove(UNUSED_DB_PATH)
#         print(f"{UNUSED_DB_PATH} を削除しました")
# atexit.register(cleanup)

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
    db = SessionLocal()
    sql=text("SELECT image_path FROM icons WHERE id = :icon_id")
    icon_row = db.execute(sql, {"icon_id": icon_id}).fetchone()
    db.close()
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
    db = SessionLocal()
    icons = db.execute("SELECT id, image_path FROM icons").fetchall()
    if request.method == 'POST':
        icon_id = request.form.get("icon", 1)
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        password_confirm = request.form.get("password_confirm")
        sql= text("SELECT id FROM users WHERE email = :email")
        row = db.execute(sql, {"email":email}).fetchone()
        if row:
            db.close()
            return jsonify({"status": "error", "message": "すでに登録済みのメールアドレスです"})

        if password != password_confirm:
            db.close()
            return jsonify({"status": "error", "message": "パスワードが一致しません"})

        db.execute(
            text("""INSERT INTO users (icon_id, username, email, password) VALUES (:icon_id, :username, :email, :password)"""),
            {"icon_id":icon_id, "username":username, "email":email, "password":password}
        )
        db.commit()
        db.close()
        return render_template("index.html",icons=icons)

    return render_template("signup.html",icons=icons)

    # # POST：ログイン処理
    # username = request.form.get("username", "")
    # password = request.form.get("password", "")

    # db = SessionLocal()
    #sql=text("SELECT id, username, password FROM users WHERE username = :username")
    # user = db.execute(sql, {"username": username}).fetchone()

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

    db = SessionLocal()

    # 同じユーザー名があるかチェック
    check_user_sql=text("SELECT id FROM users WHERE username = :username")
    existing_user = db.execute(check_user_sql,{"username":username}).fetchone()

    if existing_user is not None:
        return jsonify({"status": "error", "message": "そのユーザー名は既に使われています"}), 400

    # 登録
    insert_user_sql = text("""INSERT INTO users (username, password)VALUES (:username, :password)""")
    db.execute(insert_user_sql, {"username": username, "password": password})
    db.commit()

    # 登録したユーザーでログイン状態にする
    get_user_sql = text("SELECT id, username FROM users WHERE username = :username")
    new_user = db.execute(get_user_sql, {"username": username}).fetchone()

    session["user_id"] = new_user["id"]
    session["username"] = new_user["username"]

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

    db = SessionLocal()
    current_user_id = session['user_id']

    icons = db.execute(text("SELECT id, image_path FROM icons")).fetchall()

    user_sql = text("SELECT username, email, icon_id FROM users WHERE id = :user_id")
    current_user = db.execute(user_sql, {"user_id": current_user_id}).fetchone()

    if request.method == 'POST':
        icon = request.form.get('icon')
        new_username = request.form.get('username')
        new_email = request.form.get('email')
        current_password_input = request.form.get('current_password')
        new_password = request.form.get('new_password')
        password_confirm = request.form.get('confirm_password')

        if new_password or password_confirm:
            if not current_password_input:
                return jsonify({"status": "error", "message": "現在のパスワードを入力してください"})

            pw_sql = text("SELECT password FROM users WHERE id = :user_id")
            user_pw_row = db.execute(pw_sql, {"user_id": current_user_id}).fetchone()

            if not user_pw_row or current_password_input != user_pw_row['password']:
                return jsonify({"status": "error", "message": "現在のパスワードが間違っています"})

            if new_password != password_confirm:
                return jsonify({"status": "error", "message": "パスワードが一致しません"})

            update_pw_sql = text("UPDATE users SET password = :password WHERE id = :user_id")
            db.execute(update_pw_sql, {"password": new_password, "user_id": current_user_id})

        if icon:
            update_icon_sql = text("UPDATE users SET icon_id = :icon_id WHERE id = :user_id")
            db.execute(update_icon_sql, {"icon_id": icon, "user_id": current_user_id})

        if new_username:
            update_username_sql = text("UPDATE users SET username = :username WHERE id = :user_id")
            db.execute(update_username_sql, {"username": new_username, "user_id": current_user_id})

        if new_email:
            update_email_sql = text("UPDATE users SET email = :email WHERE id = :user_id")
            db.execute(update_email_sql, {"email": new_email, "user_id": current_user_id})

        db.commit()
        db.close()
        return jsonify({"status": "success"})

    db.close()
    return render_template(
        'account_edit.html',
        icons=icons,
        username=current_user["username"],
        email=current_user["email"],
        selected_icon=current_user["icon_id"]
    )

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

    db = SessionLocal()

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
    params = {}

    # --- category（OR条件の1つ） ---
    if valid_kw(category):
        where.append("categories.name = :category")
        params["category"] = category

    # --- keywords / title / character ---
    for i, kw in enumerate(keywords + [title, character]):
        if not valid_kw(kw):
            continue
        # 名前付きパラメータを一意にする
        name_param = f"kw_name_{i}"
        desc_param = f"kw_desc_{i}"

        where.append(f"(items.name LIKE :{name_param} OR items.description LIKE :{desc_param})")
        params[name_param] = f"%{kw}%"
        params[desc_param] = f"%{kw}%"

    # SQL組み立て
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

    items = db.execute(text(sql), params).fetchall()

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


if __name__ == "__main__":
    from app import app
    app.run(host="0.0.0.0", port=5001, debug=(os.getenv("FLASK_ENV") != "production"))
