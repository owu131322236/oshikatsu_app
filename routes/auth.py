from flask import Blueprint, render_template, request, redirect, session, jsonify
from sqlalchemy import text
from db import SessionLocal

auth_bp = Blueprint('auth_bp', __name__) 

@auth_bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = SessionLocal()
        sql = text("SELECT * FROM users WHERE username = :username AND password = :password")
        user = db.execute(sql, {"username": username, "password": password}).mappings().first()

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