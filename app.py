from flask import Flask, request, render_template, session, redirect
from gemini import ask_gemini
from auth import auth_bp

app = Flask(__name__)

app.secret_key = "your_secret_key"
app.register_blueprint(auth_bp)

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

if __name__ == "__main__": #起動用
    app.run(debug=True)
