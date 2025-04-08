import subprocess
import time
from pathlib import Path
import sys


def run_script(script_path):
    """Exécute un script Python avec gestion des erreurs"""
    print(f"\n\033[1;34m▶ Exécution de {script_path.name}\033[0m")
    start = time.time()

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            text=True,
            capture_output=True
        )
        print(f"\033[1;32m✓ Succès ({time.time() - start:.2f}s)\033[0m")
        if result.stdout.strip():
            print(f"Sortie:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"\033[1;31m✖ Erreur dans {script_path.name}:\033[0m")
        print(f"Message d'erreur:\n{e.stderr}")
        print(f"Code de sortie: {e.returncode}")
        sys.exit(1)


def find_scripts(scripts_dir):
    """Trouve les scripts dans l'ordre d'exécution"""
    script_patterns = [
        "*create*.py",  # 01_create_db.py
        "*analyse*.py",  # 02_analyse.py
        "*visual*.py",  # 03_visualisation.py
        "*rapport*.py"  # 04_rapport.py
    ]

    found_scripts = []
    for pattern in script_patterns:
        matches = list(scripts_dir.glob(pattern))
        if matches:
            found_scripts.append(matches[0])
        else:
            print(f"\033[1;33m⚠ Avertissement: Aucun script trouvé pour {pattern}\033[0m")

    return found_scripts


def main():
    print("\033[1;35m=== DÉBUT DU PIPELINE ===\033[0m")

    # Configuration des chemins
    base_dir = Path(__file__).parent
    scripts_dir = base_dir / "scripts"
    output_dir = base_dir / "output"
    data_dir = base_dir / "data"

    # Debug: Affiche la structure
    print(f"\n\033[1;36mStructure du projet:\033[0m")
    print(f"Racine: {base_dir}")
    print(f"Scripts: {list(scripts_dir.glob('*.py'))}")
    print(f"Data: {list(data_dir.glob('*'))}")
    print(f"Output: {list(output_dir.glob('*'))}\n")

    # Vérification de la structure
    required_dirs = [scripts_dir, output_dir, data_dir]
    for d in required_dirs:
        if not d.exists():
            print(f"\033[1;31mERREUR: Dossier manquant - {d.relative_to(base_dir)}\033[0m")
            sys.exit(1)

    # Recherche des scripts
    scripts = find_scripts(scripts_dir)
    if not scripts:
        print("\033[1;31mERREUR: Aucun script trouvé dans le dossier scripts/\033[0m")
        sys.exit(1)

    # Exécution du pipeline
    for script in scripts:
        run_script(script)

    # Résultat final
    rapport_path = output_dir / "rapport_ventes.pdf"
    print(f"\n\033[1;35m=== PIPELINE TERMINÉ ===\033[0m")
    if rapport_path.exists():
        print(f"Rapport généré: \033[1;36m{rapport_path}\033[0m")
    else:
        print("\033[1;33m⚠ Avertissement: Le rapport final n'a pas été généré\033[0m")


if __name__ == "__main__":
    main()