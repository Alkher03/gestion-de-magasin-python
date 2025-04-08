# utilities/db_init.py


import sqlite3
import hashlib
from pathlib import Path


def init_db():
    print("⚙ Initialisation de la base de données...")
    db_path = Path(r'C:\Users\maham\PycharmProjects\python\data\users.db')

    try:
        # Crée le dossier data si inexistant
        db_path.parent.mkdir(exist_ok=True)

        # Connexion et création table
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Supprime et recrée la table pour être certain
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("""
        CREATE TABLE users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
        """)

        # Hash du mot de passe admin
        password = "admin"
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # Insertion admin
        cursor.execute("""
        INSERT INTO users (username, password_hash, role)
        VALUES (?, ?, ?)
        """, ('admin', password_hash, 'admin'))

        conn.commit()
        print("\n✅ BASE CRÉÉE AVEC SUCCÈS")
        print(f"📂 Emplacement: {db_path}")
        print(f"👤 Compte admin: admin/admin")

    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
    finally:
        if 'conn' in locals(): conn.close()


if __name__ == "__main__":
    init_db()
