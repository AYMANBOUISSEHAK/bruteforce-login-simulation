from flask import Flask, render_template, request
from datetime import datetime

app = Flask(__name__)

# Utilisateur volontairement faible
USER = {
    "username": "admin",
    "password": "123456"
}

LOG_FILE = "logs.txt"

@app.route("/", methods=["GET", "POST"])
def login():
    message = ""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Enregistrer chaque tentative (LOG)
        with open(LOG_FILE, "a") as f:
            f.write(f"{datetime.now()} | USER={username} | PASS={password}\n")

        if username == USER["username"] and password == USER["password"]:
            message = "Connexion réussie"
        else:
            message = "Login ou mot de passe incorrect"

    # Compter le nombre total de tentatives
    try:
        with open(LOG_FILE, "r") as f:
            attempts = len(f.readlines())
    except FileNotFoundError:
        attempts = 0

    return render_template(
        "login.html",
        message=message,
        attempts=attempts
    )

if __name__ == "__main__":
    app.run(debug=True)
