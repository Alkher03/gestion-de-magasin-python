import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
from pathlib import Path

# Configuration
output_dir = Path(__file__).parent.parent / 'output'
os.makedirs(output_dir, exist_ok=True)


def setup_plot_style():
    """Configure le style des graphiques"""
    try:
        sns.set_theme(style="whitegrid")
        plt.rcParams.update({
            'figure.figsize': (16, 8),
            'font.size': 12,
            'axes.titlesize': 16,
            'axes.labelpad': 15,
            'savefig.facecolor': 'white'
        })
    except Exception as e:
        print(f"Warning: Could not set plot style - {str(e)}", file=sys.stderr)


def load_and_validate_data():
    """Charge et valide les données d'entrée"""
    input_file = output_dir / 'top_produits.csv'
    if not input_file.exists():
        raise FileNotFoundError(f"Fichier {input_file} introuvable. Exécutez d'abord 02_analyse.py")

    df = pd.read_csv(input_file)
    print("Colonnes détectées:", list(df.columns))

    required_cols = ['produit', 'ca_cfa']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Colonnes manquantes: {missing_cols}. Colonnes disponibles: {list(df.columns)}")

    return df.sort_values('ca_cfa', ascending=False)


def create_visualizations(df):
    """Crée les visualisations"""
    # Calcul des pourcentages
    df['pourcentage'] = df['ca_cfa'] / df['ca_cfa'].sum() * 100

    # Création de la figure
    fig, (ax1, ax2) = plt.subplots(1, 2)
    fig.suptitle('Analyse du Chiffre d\'Affaires', y=1.05, fontsize=18)

    # Graphique à barres
    bar_plot = sns.barplot(
        data=df,
        x='produit',
        y='ca_cfa',
        palette='viridis',
        ax=ax1
    )
    ax1.set(title='CA par Produit (FCFA)', xlabel='', ylabel='Montant en FCFA')
    ax1.tick_params(axis='x', rotation=45)

    # Ajout des valeurs sur les barres
    for p in bar_plot.patches:
        ax1.annotate(
            f"{p.get_height():,.0f}",
            (p.get_x() + p.get_width() / 2., p.get_height()),
            ha='center', va='center',
            xytext=(0, 10),
            textcoords='offset points'
        )

    # Camembert
    pie_wedges, _, _ = ax2.pie(
        df['ca_cfa'],
        labels=df['produit'],
        autopct='%1.1f%%',
        startangle=90,
        colors=sns.color_palette('pastel'),
        textprops={'fontsize': 10},
        wedgeprops={'linewidth': 1, 'edgecolor': 'white'}
    )
    ax2.set_title('Répartition du CA')

    # Légende
    ax2.legend(
        pie_wedges,
        [f"{n}: {v:,.0f} FCFA ({p:.1f}%)" for n, v, p in zip(df['produit'], df['ca_cfa'], df['pourcentage'])],
        title='Détail par produit',
        loc='center left',
        bbox_to_anchor=(1, 0.5)
    )

    plt.tight_layout()
    return fig


def visualiser_cfa():
    """Fonction principale"""
    try:
        print("=== DÉBUT DE LA VISUALISATION ===")

        # Configuration
        setup_plot_style()

        # Données
        df = load_and_validate_data()

        # Visualisation
        fig = create_visualizations(df)

        # Sauvegarde
        output_file = output_dir / 'repartition_ca.png'
        fig.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Visualisation sauvegardée dans {output_file}")
        plt.close(fig)

        print("=== VISUALISATION TERMINÉE AVEC SUCCÈS ===")
        return True

    except Exception as e:
        print(f"ERREUR: {str(e)}", file=sys.stderr)
        return False


if __name__ == "__main__":
    success = visualiser_cfa()
    sys.exit(0 if success else 1)