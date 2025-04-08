from fpdf import FPDF
import pandas as pd
from pathlib import Path
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PDFReport(FPDF):
    def __init__(self):
        super().__init__()
        # Utilisation des polices core PDF standard
        self.set_font("helvetica", size=12)

    def header(self):
        """En-tête du document PDF"""
        self.set_font("helvetica", "B", 16)
        self.cell(0, 10, "Rapport d'Analyse des Ventes", new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_font("helvetica", size=10)
        self.cell(0, 10, f"Genere le {datetime.now().strftime('%d/%m/%Y %H:%M')}", new_x="LMARGIN", new_y="NEXT",
                  align="C")
        self.ln(10)

    def footer(self):
        """Pied de page du document PDF"""
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def add_section_title(self, title):
        """Ajoute un titre de section"""
        self.set_font("helvetica", "B", 14)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(5)


def generer_rapport():
    """Genere le rapport PDF a partir des donnees analysees"""
    try:
        # Configuration des chemins
        BASE_DIR = Path(__file__).parent
        OUTPUT_DIR = BASE_DIR.parent / "output"
        OUTPUT_DIR.mkdir(exist_ok=True)

        csv_path = OUTPUT_DIR / "top_produits.csv"
        logger.info(f"Recherche du fichier de donnees: {csv_path}")

        if not csv_path.exists():
            raise FileNotFoundError(f"Fichier {csv_path} introuvable")

        # Initialisation PDF
        pdf = PDFReport()
        pdf.add_page()

        # 1. Chargement des donnees
        df = pd.read_csv(csv_path)
        logger.info("Donnees chargees avec succes")

        # Verification des colonnes requises
        required_columns = {'produit', 'quantite', 'ca_cfa'}
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            raise ValueError(f"Colonnes manquantes: {missing}. Colonnes disponibles: {list(df.columns)}")

        # 2. Metriques principales
        pdf.add_section_title("Resultats Cles")
        pdf.set_font("helvetica", size=12)

        # Calcul des metriques
        ca_total = df['ca_cfa'].sum()
        produit_phare = df.loc[df['ca_cfa'].idxmax(), 'produit']
        quantite_totale = df['quantite'].sum()

        # Utilisation de caracteres simples
        texte_metriques = (
            f"- Chiffre d'affaires total : {ca_total:,.0f} FCFA\n"
            f"- Produit phare : {produit_phare}\n"
            f"- Quantite totale vendue : {quantite_totale:,.0f} unites"
        )
        pdf.multi_cell(0, 10, texte_metriques)

        # 3. Insertion des graphiques
        images = ["ca_produits_cfa.png", "repartition_ca.png"]
        for img in images:
            img_path = OUTPUT_DIR / img
            if img_path.exists():
                pdf.add_page()
                pdf.add_section_title(img.replace(".png", "").replace("_", " ").title())
                pdf.image(str(img_path), x=10, y=30, w=180)
                logger.info(f"Image {img} ajoutee au rapport")
            else:
                logger.warning(f"Image {img} non trouvee")

        # 4. Details des produits
        pdf.add_page()
        pdf.add_section_title("Details par Produit")

        # En-tetes du tableau
        pdf.set_fill_color(200, 220, 255)
        pdf.set_font("helvetica", "B", 12)
        col_widths = [80, 40, 60]

        for col, width in zip(["Produit", "Quantite", "CA (FCFA)"], col_widths):
            pdf.cell(width, 10, col, border=1, align="C", fill=True)
        pdf.ln()

        # Donnees du tableau
        pdf.set_font("helvetica", size=10)
        for _, row in df.iterrows():
            pdf.cell(col_widths[0], 10, row["produit"], border=1)
            pdf.cell(col_widths[1], 10, f"{row['quantite']:,}", border=1, align="R")
            pdf.cell(col_widths[2], 10, f"{row['ca_cfa']:,.0f}", border=1, align="R")
            pdf.ln()

        # Sauvegarde du rapport
        rapport_path = OUTPUT_DIR / "rapport_ventes.pdf"
        pdf.output(str(rapport_path))
        logger.info(f"Rapport genere avec succes: {rapport_path}")

    except Exception as e:
        logger.error(f"Erreur lors de la generation du rapport: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    generer_rapport()