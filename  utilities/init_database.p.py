# utilities/init_database.py
import sqlite3
import hashlib
from pathlib import Path


def initialize_database():
    """Initialise la base de données avec un admin"""
    db_path = Path(r'C:\Users\maham\PycharmProjects\python\data\users.db')

    try:
        # Crée le dossier data si inexistant
        db_path.parent.mkdir(exist_ok=True)

        # Connexion et création table
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Structure complète de la table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'user'
        )
        """)

        # Hash du mot de passe admin
        password = "admin"
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # Insertion de l'admin
        cursor.execute("""
        INSERT OR REPLACE INTO users (username, password_hash, full_name, role)
        VALUES (?, ?, ?, ?)
        """, ('admin', password_hash, 'Administrateur', 'admin'))

        conn.commit()
        print("\n✅ BASE DE DONNÉES INITIALISÉE")
        print(f"📂 Emplacement: {db_path}")
        print(f"👤 Compte admin: admin/admin")

    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
    finally:
        if 'conn' in locals(): conn.close()


if __name__ == "__main__":
    initialize_database()