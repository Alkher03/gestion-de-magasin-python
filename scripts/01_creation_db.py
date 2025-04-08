import sqlite3
import os
from datetime import datetime, timedelta
import random
# Chemin absolu vers la base
db_path = os.path.join(os.path.dirname(__file__), '../data/vente.db')
def create_db():
    # Création du dossier si inexistant
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    # Connexion/Création de la base
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Nettoyage des tables existantes
    cursor.execute("DROP TABLE IF EXISTS ventes")
    cursor.execute("DROP TABLE IF EXISTS produits")
    cursor.execute("DROP TABLE IF EXISTS clients")
    # Création des tables
    cursor.execute("""
    CREATE TABLE produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        prix REAL NOT NULL
    )""")

    cursor.execute("""
    CREATE TABLE clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL
    )""")

    cursor.execute("""
    CREATE TABLE ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produit_id INTEGER,
        client_id INTEGER,
        date TEXT NOT NULL,
        quantite INTEGER NOT NULL,
        FOREIGN KEY (produit_id) REFERENCES produits(id),
        FOREIGN KEY (client_id) REFERENCES clients(id)
    )""")

    # Insertion de données de test
    produits = [
        ("Ordinateur portable", 999.99),
        ("Téléphone", 599.99),
        ("Casque audio", 99.99),
        ("Souris sans fil", 25.99),  # Nouveau
        ("Clavier mécanique", 89.99),  # Nouveau
        ("Écran 4K", 299.99),  # Nouveau
        ("Disque dur SSD", 120.50),  # Nouveau
        ("Webcam HD", 75.00)  # Nouveau
    ]
    cursor.executemany("INSERT INTO produits (nom, prix) VALUES (?, ?)", produits)

    clients = [
        ("Jean Dupont",),
        ("Marie Martin",)
    ]
    cursor.executemany("INSERT INTO clients (nom) VALUES (?)", clients)

    # Génération de 50 ventes aléatoires
    for _ in range(50):
        cursor.execute(
            """INSERT INTO ventes 
            (produit_id, client_id, date, quantite) 
            VALUES (?, ?, ?, ?)""",
            (
                random.randint(1, 3),  # produit_id
                random.randint(1, 2),  # client_id
                (datetime.now() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d"),
                random.randint(1, 3)  # quantite
            )
        )

    conn.commit()
    conn.close()
    print(f"Base créée avec succès : {db_path}")


if __name__ == "__main__":
    create_db()