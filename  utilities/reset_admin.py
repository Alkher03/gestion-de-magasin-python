import sqlite3
import hashlib
import os

# Chemin ABSOLU vérifié
DB_PATH = r'C:\Users\maham\PycharmProjects\python\data\users.db'


def reset_admin():
    print("⚙ Initialisation du compte admin...")
    print(f"📂 Emplacement base: {DB_PATH}")

    try:
        # Crée le dossier si inexistant
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

        # Connexion à SQLite
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        print("🔌 Connexion réussie")

        # Crée la table
        cursor.execute('''CREATE TABLE IF NOT EXISTS users
                        (username TEXT PRIMARY KEY,
                         password_hash TEXT NOT NULL,
                         role TEXT DEFAULT 'admin')''')

        # Hash du mot de passe
        password = "admin123"
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # Insère l'admin
        cursor.execute("INSERT OR REPLACE INTO users VALUES (?,?,?)",
                       ('admin', password_hash, 'admin'))

        conn.commit()
        print("\n✅ COMPTE ADMIN CRÉÉ AVEC SUCCÈS")
        print(f"👤 Utilisateur: admin")
        print(f"🔒 Mot de passe: {password}")

    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
    finally:
        if 'conn' in locals(): conn.close()


if __name__ == "__main__":
    reset_admin()
