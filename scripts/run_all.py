import subprocess
import time

scripts = [
    '01_create_db.py',
    '02_analyse.py',
    '03_visualisation.py',
    '04_rapport.py'  # Ajouté ici
]

for script in scripts:
    print(f"\n{'='*50}\nExécution de {script}\n{'='*50}")
    start_time = time.time()
    subprocess.run(['python', script], check=True)
    print(f"Terminé en {time.time() - start_time:.2f}s")