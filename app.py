from flask import Flask, render_template, request, session
import time
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = "uir_brute_force_demo_secret_2025"

# Utilisateur volontairement faible
USER = {
    "username": "admin",
    "password": "123456789"
}

LOG_FILE = "logs.txt"

# Variables de sécurité (en mémoire)
login_attempts = {}  # {username: {"count": int, "locked_until": timestamp}}
MAX_ATTEMPTS = 5
LOCK_DURATION_SECONDS = 300  # 5 minutes

def get_security_mode():
    mode = request.args.get("mode", "secure").lower()
    return mode == "vuln"  # True = mode vulnérable

@app.route("/", methods=["GET", "POST"])
def login():
    is_vulnerable = get_security_mode()

    message = ""
    attempts = 0
    locked = False
    captcha_question = None

    # Lecture du nombre total de tentatives
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            attempts = len(f.readlines())
    except FileNotFoundError:
        attempts = 0

    # CAPTCHA en mode secure - génération FORCÉE au chargement
    captcha_input_str = ""  # Valeur par défaut

    if not is_vulnerable:
        # Force la génération si absent
        if "captcha_solution" not in session:
            operations = [
                (random.randint(3, 12), "+", random.randint(4, 15)),
                (random.randint(8, 20), "-", random.randint(1, 7)),
                (random.randint(2, 9), "×", random.randint(2, 8))
            ]
            op1, op_symbol, op2 = random.choice(operations)
            
            if op_symbol == "+":
                solution = op1 + op2
            elif op_symbol == "-":
                solution = op1 - op2
            else:
                solution = op1 * op2
                
            session["captcha_solution"] = solution
            captcha_question = f"{op1} {op_symbol} {op2}"
        else:
            # Si déjà présent (après échec), recalcule ou garde (ici recalcule pour simplicité)
            operations = [
                (random.randint(3, 12), "+", random.randint(4, 15)),
                (random.randint(8, 20), "-", random.randint(1, 7)),
                (random.randint(2, 9), "×", random.randint(2, 8))
            ]
            op1, op_symbol, op2 = random.choice(operations)
            
            if op_symbol == "+":
                solution = op1 + op2
            elif op_symbol == "-":
                solution = op1 - op2
            else:
                solution = op1 * op2
                
            session["captcha_solution"] = solution
            captcha_question = f"{op1} {op_symbol} {op2}"

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        captcha_input_str = request.form.get("captcha", "").strip()

        now = time.time()

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()} | USER={username} | PASS={password}\n")

        if not is_vulnerable:
            if username in login_attempts and "locked_until" in login_attempts[username]:
                if login_attempts[username]["locked_until"] > now:
                    remaining = int(login_attempts[username]["locked_until"] - now)
                    message = f"ACCOUNT_LOCKED: Compte verrouillé. Réessayez dans {remaining//60} min {remaining%60} s"
                    locked = True
                else:
                    del login_attempts[username]

        if locked:
            return render_template(
                "login.html",
                message=message,
                attempts=attempts,
                captcha_question=captcha_question
            )

        # CAPTCHA obligatoire et bloquant en mode secure
        if not is_vulnerable:
            if not captcha_input_str:
                message = "CAPTCHA_REQUIRED: Veuillez remplir le CAPTCHA"
                return render_template(
                    "login.html",
                    message=message,
                    attempts=attempts,
                    captcha_question=captcha_question
                )
            try:
                captcha_input = int(captcha_input_str)
                correct = session.get("captcha_solution", -999)
                
                if captcha_input != correct:
                    message = "WRONG_CAPTCHA: Vérification CAPTCHA incorrecte. Réessayez."
                    # Regénérer un nouveau CAPTCHA après échec
                    if "captcha_solution" in session:
                        session.pop("captcha_solution")
                    return render_template(
                        "login.html",
                        message=message,
                        attempts=attempts,
                        captcha_question=captcha_question
                    )
                
                # CAPTCHA OK → continue
                if "captcha_solution" in session:
                    session.pop("captcha_solution")
                    
            except ValueError:
                message = "CAPTCHA_INVALID: Le CAPTCHA doit être un nombre valide"
                return render_template(
                    "login.html",
                    message=message,
                    attempts=attempts,
                    captcha_question=captcha_question
                )

        # Délai artificiel en mode secure
        if not is_vulnerable:
            time.sleep(random.uniform(1.5, 2.8))

        # Vérification identifiants
        if username == USER["username"] and password == USER["password"]:
            message = "SUCCESS: Connexion réussie"
            if not is_vulnerable and username in login_attempts:
                del login_attempts[username]
        else:
            message = "FAILURE: Login ou mot de passe incorrect"

            if not is_vulnerable:
                if username not in login_attempts:
                    login_attempts[username] = {"count": 0}
                
                login_attempts[username]["count"] += 1
                
                if login_attempts[username]["count"] >= MAX_ATTEMPTS:
                    login_attempts[username]["locked_until"] = now + LOCK_DURATION_SECONDS
                    message = f"ACCOUNT_LOCKED: Trop de tentatives. Compte verrouillé {LOCK_DURATION_SECONDS//60} minutes"

    return render_template(
        "login.html",
        message=message,
        attempts=attempts,
        captcha_question=captcha_question
    )

if __name__ == "__main__":
    print("Démarrage serveur UIR Brute Force Demo")
    print("→ Mode vulnérable  : http://127.0.0.1:5000/?mode=vuln")
    print("→ Mode sécurisé    : http://127.0.0.1:5000/")
    app.run(debug=True)