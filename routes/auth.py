from flask import Blueprint, render_template, request, redirect, session, jsonify
from db import get_db

auth_bp = Blueprint('auth_bp', __name__) 

@auth_bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        user = db.execute(
            f"SELECT * FROM users WHERE username ={p} AND password = {p} ",
            (username, password)
        ).fetchone() #fetchoneで1件取得

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "ユーザー名またはパスワードが間違っています"})
    return render_template("login.html")
@auth_bp.route("/loggout")
def loggout():
    session.clear()
    return redirect("/login")