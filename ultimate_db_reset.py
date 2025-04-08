import sqlite3
import hashlib
import os
from pathlib import Path

# Configuration
DB_PATH = Path(r'C:\Users\maham\PycharmProjects\python\data\users.db')

def reset_database():
    print("⚙ Initialisation de la base de données...")
    
    try:
        # Création du dossier data
        os.makedirs(DB_PATH.parent, exist_ok=True)
        
        # Connexion et création table
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Structure de table vérifiée
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'user'
        )
        """)
        
        # Hash du mot de passe admin123
        password = "admin123"
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Insertion admin
        cursor.execute("""
        INSERT OR REPLACE INTO users 
        (username, password_hash, full_name, role)
        VALUES (?, ?, ?, ?)
        """, ('admin', password_hash, 'Administrateur', 'admin'))
        
        conn.commit()
        print("\n✅ BASE DE DONNÉES CRÉÉE AVEC SUCCÈS")
        print(f"👤 Compte admin créé")
        print(f"🔑 Mot de passe: {password}")
        print(f"📂 Emplacement: {DB_PATH}")
        
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {str(e)}")
    finally:
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    reset_database()
