from flask import Flask, request, render_template, session, redirect, jsonify
from routes.gemini import ask_gemini
from routes.auth import auth_bp
from routes.items import items_bp
from db import get_db

# git-graphテスト

app = Flask(__name__)

app.secret_key = "your_secret_key"
app.register_blueprint(auth_bp)
app.register_blueprint(items_bp)

@app.context_processor
def inject_user():
    username = session.get("username", "None")
    initial = username[0].upper() if username else "N" 
    return dict(username=session.get("username"), initial=initial)


@app.route("/login")
def home():
    if "user_id" not in session:
        return redirect("/login")
    return redirect("/")

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    return ask_gemini(request)

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

# POSTに関するルート
@app.route('/account/edit', methods=['GET', 'POST'])
def account_edit():
    if "user_id" not in session:
        return redirect("/login")
    if request.method == 'POST':
        db = get_db()
        user_id = session['user_id']
        username = request.form.get('username')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        password_confirm = request.form.get('confirm_password')

        if new_password or password_confirm:
            if not current_password:
                return jsonify({
                    "status": "error",
                    "message": "現在のパスワードを入力してください"
                })

            row = db.execute(
                'SELECT password FROM users WHERE id = ?',
                (user_id,)
            ).fetchone()

            if not row or current_password != row['password']:
                return jsonify({
                    "status": "error",
                    "message": "現在のパスワードが間違っています"
                })

            if new_password != password_confirm:
                return jsonify({
                    "status": "error",
                    "message": "パスワードが一致しません"
                })

            db.execute(
                'UPDATE users SET password = ? WHERE id = ?',
                (new_password, user_id)
            )

        if username:
            db.execute(
                'UPDATE users SET username = ? WHERE id = ?',
                (username, user_id)
            )

        db.commit()

        return jsonify({"status": "success"})
    return render_template('account_edit.html')  

if __name__ == "__main__": #起動用
    app.run(host="0.0.0.0", port=5001, debug=True)
