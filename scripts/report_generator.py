import io
import tempfile
from datetime import datetime
from typing import Optional, List
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, Image, PageBreak
)
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER

@classmethod
def generate_sales_report(
    cls,
    df: pd.DataFrame,
    title: str = "Rapport d'Analyse des Ventes",
    include_details: bool = False,
    include_charts: bool = True
) -> Optional[io.BytesIO]:
    """Méthode de compatibilité avec l'ancienne interface"""
    instance = cls()
    return instance.generate_report(
        df=df,
        title=title,
        report_type="full" if include_details else "summary"
    )
class ReportGenerator:
    """Générateur de rapports PDF professionnels pour données commerciales"""

    # Configuration des styles
    _STYLES = {
        'title': {
            'fontName': 'Helvetica-Bold',
            'fontSize': 18,
            'alignment': TA_CENTER,
            'textColor': colors.HexColor("#003366"),
            'spaceAfter': 12
        },
        'header1': {
            'fontName': 'Helvetica-Bold',
            'fontSize': 14,
            'textColor': colors.HexColor("#0066CC"),
            'spaceBefore': 12,
            'spaceAfter': 6
        },
        'normal': {
            'fontName': 'Helvetica',
            'fontSize': 10,
            'leading': 12
        }
    }

    def __init__(self):
        self._styles = self._initialize_styles()

    @staticmethod
    def _initialize_styles() -> dict:
        """Initialise et retourne les styles PDF"""
        styles = getSampleStyleSheet()
        custom_styles = {
            name: ParagraphStyle(name, **attrs)
            for name, attrs in ReportGenerator._STYLES.items()
        }
        return {**styles.__dict__, **custom_styles}

    def generate_report(
            self,
            df: pd.DataFrame,
            title: str = "Rapport d'Analyse Commerciale",
            report_type: str = "summary"
    ) -> Optional[io.BytesIO]:
        """
        Génère un rapport PDF à partir des données fournies

        Args:
            df: DataFrame contenant les données
            title: Titre du rapport
            report_type: 'summary' ou 'full'

        Returns:
            Buffer PDF ou None en cas d'erreur
        """
        try:
            self._validate_data(df)

            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            elements = self._build_report_elements(df, title, report_type)

            doc.build(elements)
            buffer.seek(0)
            return buffer

        except Exception as e:
            st.error(f"Erreur de génération: {str(e)}")
            return None

    def _validate_data(self, df: pd.DataFrame) -> None:
        """Valide la structure des données"""
        required_columns = {'produit', 'quantite', 'ca_cfa'}
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            raise ValueError(f"Colonnes requises manquantes: {missing}")

    def _build_report_elements(
            self,
            df: pd.DataFrame,
            title: str,
            report_type: str
    ) -> List[Paragraph]:
        """Construit les éléments du rapport"""
        elements = [
            Paragraph(title, self._styles['Title']),
            Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y')}", self._styles['Normal']),
            Spacer(1, 24)
        ]

        # Section Résumé
        elements.extend([
            Paragraph("Résumé Analytique", self._styles['Heading1']),
            *self._create_summary_table(df)
        ])

        # Graphique
        chart_path = self._create_sales_chart(df)
        if chart_path:
            elements.extend([
                Spacer(1, 12),
                Paragraph("Analyse Visuelle", self._styles['Heading1']),
                Image(chart_path, width=6 * inch, height=3 * inch)
            ])

        # Section Détail (si full report)
        if report_type == "full":
            elements.extend([
                PageBreak(),
                Paragraph("Détail des Ventes", self._styles['Heading1']),
                *self._create_detail_table(df)
            ])

        return elements

    def _create_summary_table(self, df: pd.DataFrame) -> List[Table]:
        """Crée le tableau de synthèse"""
        total_ca = df['ca_cfa'].sum()
        avg_basket = total_ca / df['quantite'].sum()

        data = [
            ["Indicateur", "Valeur"],
            ["CA Total", f"{total_ca:,.2f} FCFA"],
            ["Panier Moyen", f"{avg_basket:,.2f} FCFA"],
            ["Produit le Plus Vendu", df['produit'].mode()[0]]
        ]

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F5F5F5")),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
        ]))

        return [table, Spacer(1, 24)]

    def _create_detail_table(self, df: pd.DataFrame) -> List[Table]:
        """Crée le tableau détaillé"""
        summary = df.groupby('produit').agg({
            'quantite': ['sum', 'mean'],
            'ca_cfa': 'sum'
        }).reset_index()

        summary.columns = ['Produit', 'Quantité Totale', 'Moyenne', 'CA Total']
        summary['Moyenne'] = summary['Moyenne'].round(2)

        data = [summary.columns.tolist()] + summary.values.tolist()

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('FONTSIZE', (0, 0), (-1, -1), 8)
        ]))

        return [table]

    def _create_sales_chart(self, df: pd.DataFrame) -> Optional[str]:
        """Génère un graphique et retourne son chemin"""
        try:
            plt.style.use('ggplot')
            fig, ax = plt.subplots(figsize=(10, 6))

            sales = df.groupby('produit')['ca_cfa'].sum().sort_values()
            bars = ax.barh(sales.index.astype(str), sales.values, color='#4e79a7')

            ax.bar_label(bars, fmt='%.0f FCFA', padding=5)
            ax.set_title("Répartition du CA par Produit", pad=20)
            ax.set_xlabel("Chiffre d'Affaires (FCFA)")

            plt.tight_layout()

            img_path = tempfile.mktemp(suffix='.png')
            fig.savefig(img_path, dpi=300, bbox_inches='tight')
            plt.close()

            return img_path

        except Exception as e:
            st.warning(f"Erreur de création du graphique: {str(e)}")
            return None