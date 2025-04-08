# admin_reset_perfect.py
import sqlite3
import hashlib
from pathlib import Path

# Chemin vérifié
DB_PATH = Path(__file__).parent.parent / 'data' / 'users.db'


def reset_admin():
    print("⚙ Réinitialisation du compte admin...")
    print(f"📂 Base de données: {DB_PATH}")

    try:
        # Connexion
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Vérification structure table (adaptée à votre schéma)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'user'
        )
        """)

        # Hash du mot de passe
        password = "admin123"
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # Insertion avec TOUTES les colonnes
        cursor.execute("""
        INSERT OR REPLACE INTO users 
        (username, password_hash, full_name, role)
        VALUES (?, ?, ?, ?)
        """, ('admin', password_hash, 'Administrateur', 'admin'))

        conn.commit()
        print("\n✅ COMPTE ADMIN CONFIGURÉ")
        print(f"👤 Utilisateur: admin")
        print(f"🔒 Mot de passe: {password}")
        print(f"👔 Rôle: admin")

    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
    finally:
        if conn: conn.close()


if __name__ == "__main__":
    reset_admin()