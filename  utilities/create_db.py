# utilities/create_db.py


import sqlite3
import hashlib
import os
from pathlib import Path


def create_database():
    # Chemin absolu explicite
    db_path = Path(r'C:\Users\maham\PycharmProjects\python\data\users.db')
    print(f"🔧 Création de la base à: {db_path}")

    try:
        # Crée le dossier data si nécessaire
        os.makedirs(db_path.parent, exist_ok=True)

        # Connexion (crée le fichier si inexistant)
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Crée la table users
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
        """)

        # Ajoute l'admin
        password = "admin"
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("""
        INSERT OR REPLACE INTO users (username, password_hash, role)
        VALUES (?, ?, ?)
        """, ('admin', password_hash, 'admin'))

        conn.commit()
        print("\n✅ BASE CRÉÉE AVEC SUCCÈS")
        print(f"👤 Admin: admin/{password}")

    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
    finally:
        if 'conn' in locals(): conn.close()


if __name__ == "__main__":
    create_database()