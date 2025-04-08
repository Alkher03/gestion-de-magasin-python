# scripts/pdf_utils.py
import base64
import io
import PyPDF2
import pdfplumber
import streamlit as st
import pandas as pd
from datetime import datetime
import tempfile

def read_pdf(file):
    """Lit un PDF et retourne son texte"""
    try:
        with pdfplumber.open(file) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        return text
    except Exception as e:
        st.error(f"Erreur de lecture du PDF : {str(e)}")
        return ""

def display_pdf(file):
    """Affiche un PDF dans Streamlit"""
    # Votre implémentation ici...
    pass

def pdf_to_dataframe(file):
    """Convertit les tableaux PDF en DataFrame"""
    # Votre implémentation ici...
    pass


def generate_sales_report(
        df,
        title="Rapport d'Analyse des Ventes",
        full_report=False  # Ajoutez ce paramètre
):
    """Génère un rapport PDF avec option pour rapport complet ou résumé

    Args:
        df: DataFrame contenant les données
        title: Titre du rapport
        full_report: Si True, génère un rapport détaillé
    """
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf_path = temp_file.name
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter

        # Page 1 - Résumé
        c.setFont("Helvetica-Bold", 16)
        c.drawString(72, height - 72, title)
        c.setFont("Helvetica", 12)
        c.drawString(72, height - 92, f"Généré le : {datetime.now().strftime('%d/%m/%Y %H:%M')}")

        # Statistiques clés
        c.setFont("Helvetica-Bold", 12)
        c.drawString(72, height - 120, "Statistiques Clés:")
        c.setFont("Helvetica", 10)

        metrics = [
            f"CA Total: {df['ca_cfa'].sum():,.0f} FCFA",
            f"Produit le plus vendu: {df.loc[df['quantite'].idxmax(), 'produit']}",
            f"Panier moyen: {df['ca_cfa'].sum() / df['quantite'].sum():,.0f} FCFA"
        ]

        for i, metric in enumerate(metrics):
            c.drawString(72, height - 140 - (i * 20), metric)

        # Page 2 - Détails (seulement si full_report=True)
        if full_report:
            c.showPage()
            c.setFont("Helvetica-Bold", 12)
            c.drawString(72, height - 72, "Détail des Ventes")

            # Ajoutez ici le contenu détaillé
            # Par exemple, un tableau avec les données

        c.save()
        return pdf_path

    except Exception as e:
        st.error(f"Erreur lors de la génération du PDF : {str(e)}")
        return None