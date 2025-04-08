import sqlite3
import pandas as pd
import os
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional
import logging

# Configuration
TAUX_EURO_CFA = 655.96  # Taux de conversion BCEAO
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "../data/vente.db"
OUTPUT_DIR = BASE_DIR / "../output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUT_DIR / 'analyse.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Exception personnalisée pour les erreurs de base de données"""
    pass


def verify_database_schema(conn: sqlite3.Connection) -> None:
    """Vérifie que le schéma de la base correspond aux attentes"""
    required_tables = {
        'ventes': {'id', 'produit_id', 'client_id', 'date', 'quantite'},
        'produits': {'id', 'nom', 'prix'},
        'clients': {'id', 'nom'}
    }

    cursor = conn.cursor()

    try:
        # Vérification des tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = {row[0] for row in cursor.fetchall()}

        missing_tables = set(required_tables.keys()) - existing_tables
        if missing_tables:
            raise DatabaseError(f"Tables manquantes: {missing_tables}")

        # Vérification des colonnes
        for table, columns in required_tables.items():
            cursor.execute(f"PRAGMA table_info({table});")
            existing_columns = {row[1] for row in cursor.fetchall()}

            missing_columns = columns - existing_columns
            if missing_columns:
                raise DatabaseError(f"Colonnes manquantes dans '{table}': {missing_columns}")

    except sqlite3.Error as e:
        raise DatabaseError(f"Erreur de vérification du schéma: {e}")
    finally:
        cursor.close()


def get_db_connection() -> sqlite3.Connection:
    """Établit une connexion sécurisée à la base SQLite"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        verify_database_schema(conn)
        return conn
    except sqlite3.Error as e:
        logger.error(f"Erreur de connexion à la base: {e}")
        raise DatabaseError(f"Impossible de se connecter à la base: {e}")


def calculate_kpis(conn: sqlite3.Connection) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Calcule les indicateurs clés de performance"""
    try:
        # CA Total
        ca_query = """
        SELECT 
            SUM(p.prix * v.quantite) as ca_eur,
            SUM(p.prix * v.quantite) * ? as ca_cfa,
            COUNT(DISTINCT v.client_id) as clients_uniques,
            AVG(p.prix * v.quantite) as panier_moyen_eur
        FROM ventes v 
        JOIN produits p ON v.produit_id = p.id
        """
        ca_total = pd.read_sql(ca_query, conn, params=(TAUX_EURO_CFA,))

        # Validation des données
        if ca_total.isnull().any().any():
            logger.warning("Certaines valeurs KPIs sont nulles - vérifiez les données source")

        # Top produits
        top_produits_query = """
        SELECT 
            p.nom as produit,
            SUM(v.quantite) as quantite,
            SUM(p.prix * v.quantite) as ca_eur,
            SUM(p.prix * v.quantite) * ? as ca_cfa,
            ROUND(SUM(p.prix * v.quantite) * 100.0 / 
                (SELECT SUM(p.prix * v.quantite) FROM ventes v JOIN produits p ON v.produit_id = p.id), 2) as part_marche
        FROM ventes v
        JOIN produits p ON v.produit_id = p.id
        GROUP BY p.nom
        ORDER BY ca_eur DESC
        LIMIT 5
        """
        top_produits = pd.read_sql(top_produits_query, conn, params=(TAUX_EURO_CFA,))

        return ca_total, top_produits

    except sqlite3.Error as e:
        logger.error(f"Erreur lors du calcul des KPIs: {e}")
        raise DatabaseError(f"Erreur d'exécution des requêtes: {e}")


def export_results(df: pd.DataFrame, filename: str, output_dir: Path = OUTPUT_DIR) -> None:
    """Exporte les résultats en CSV avec gestion robuste des erreurs"""
    try:
        filepath = output_dir / filename
        df.to_csv(
            filepath,
            index=False,
            encoding='utf-8-sig',  # Pour une meilleure compatibilité Excel
            date_format='%Y-%m-%d'  # Format standard pour les dates
        )
        logger.info(f"Fichier exporté avec succès: {filepath}")
    except PermissionError:
        logger.error(f"Permission refusée pour écrire dans {filepath}")
        raise
    except Exception as e:
        logger.error(f"Erreur inattendue lors de l'export: {e}")
        raise


def generate_report(ca_total: pd.DataFrame, top_produits: pd.DataFrame) -> str:
    """Génère un rapport textuel des résultats"""
    report = []
    report.append("\n=== RAPPORT D'ANALYSE ===")
    report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    if not ca_total.empty:
        report.append("\n=== INDICATEURS CLÉS ===")
        report.append(f"• CA Total: {ca_total.iloc[0]['ca_eur']:,.2f} € ({ca_total.iloc[0]['ca_cfa']:,.0f} FCFA)")
        report.append(f"• Clients uniques: {ca_total.iloc[0]['clients_uniques']}")
        report.append(f"• Panier moyen: {ca_total.iloc[0]['panier_moyen_eur']:,.2f} €")

    if not top_produits.empty:
        report.append("\n=== TOP 5 PRODUITS ===")
        with pd.option_context('display.float_format', '{:,.2f}'.format):
            report.append(top_produits.to_string(index=False))

    return "\n".join(report)


def analyser_ventes() -> Optional[bool]:
    """Workflow principal d'analyse avec gestion complète des erreurs"""
    conn = None
    try:
        logger.info("Début de l'analyse des ventes")

        # 1. Connexion et vérification
        conn = get_db_connection()
        logger.info("Connexion à la base établie avec succès")

        # 2. Calcul des indicateurs
        ca_total, top_produits = calculate_kpis(conn)
        logger.info("Calcul des indicateurs terminé")

        # 3. Génération et affichage du rapport
        report = generate_report(ca_total, top_produits)
        print(report)

        # 4. Export des résultats
        export_results(top_produits, 'top_produits.csv')
        export_results(ca_total, 'ca_total.csv')

        # 5. Export du rapport texte
        with open(OUTPUT_DIR / 'rapport_analyse.txt', 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info("Analyse terminée avec succès")
        return True

    except DatabaseError as e:
        logger.error(f"Erreur de base de données: {e}")
        return False
    except Exception as e:
        logger.critical(f"Erreur inattendue: {e}", exc_info=True)
        return False
    finally:
        if conn:
            conn.close()
            logger.info("Connexion à la base fermée")


if __name__ == "__main__":
    print("=== DÉBUT DE L'ANALYSE ===")
    success = analyser_ventes()
    status = "SUCCÈS" if success else "ÉCHEC"
    print(f"\n=== ANALYSE TERMINÉE - {status} ===")
    if not success:
        print("Consultez les logs pour plus de détails")