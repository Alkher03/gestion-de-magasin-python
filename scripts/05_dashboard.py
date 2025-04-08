# 1. Importations standards
from datetime import datetime
import sys
from pathlib import Path
import hashlib
import sqlite3
import tempfile

# 2. Importations tierces
import streamlit as st
import pandas as pd
import plotly.express as px

# 3. Importations locales (vos modules)
from report_generator import ReportGenerator
# Configuration des chemins
output_dir = Path(__file__).parent.parent / 'output'
DB_PATH = Path(__file__).parent.parent / 'data' / 'users.db'


# ---- PARTIE AUTHENTIFICATION ----
def init_auth_db():
    """Initialise la base de données d'authentification avec le bon schéma"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Vérifie si la table existe déjà
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            # Crée la table avec les colonnes exactes
            cursor.execute("""
            CREATE TABLE users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'user'
            )
            """)

            # Insertion du compte admin avec toutes les colonnes
            password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
            cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, role)
            VALUES (?, ?, ?, ?)
            """, ('admin', password_hash, 'Administrateur', 'admin'))

            conn.commit()
    except Exception as e:
        st.error(f"Erreur d'initialisation de la base: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


def hash_password(password):
    """Hash le mot de passe avec SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_user(username, password):
    """Vérifie les identifiants de l'utilisateur"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password_hash, role, full_name FROM users WHERE username = ?",
            (username,)
        )
        result = cursor.fetchone()
        if result:
            stored_hash, role, full_name = result
            if stored_hash == hash_password(password):
                return True, role, full_name
    except sqlite3.Error as e:
        st.error(f"Erreur de base de données: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
    return False, None, None


def login_page():
    """Affiche la page de connexion"""
    st.title("🔐 Connexion au Dashboard")

    with st.form("login_form"):
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        submit = st.form_submit_button("Se connecter")

        if submit:
            is_valid, role, full_name = verify_user(username, password)
            if is_valid:
                st.session_state.update({
                    'authenticated': True,
                    'username': username,
                    'role': role,
                    'full_name': full_name
                })
                st.success("Connexion réussie!")
                st.rerun()  # <-- Changement ici (remplacement de experimental_rerun)
            else:
                st.error("Identifiants incorrects")

# ---- PARTIE DASHBOARD ----
def load_data():
    """
    Charge les données depuis la base SQLite et les prépare pour l'analyse.
    Retourne un DataFrame consolidé avec les ventes, produits et clients.
    """
    try:
        db_path = Path(__file__).parent / "../data/vente.db"
        conn = sqlite3.connect(db_path)

        # Chargement des tables avec des alias pour éviter les conflits de noms
        df_ventes = pd.read_sql("SELECT * FROM ventes", conn)
        df_produits = pd.read_sql("SELECT id as produit_id, nom, prix FROM produits", conn)
        df_clients = pd.read_sql("SELECT id as client_id, nom FROM clients", conn)

        # Fusion des DataFrames en vérifiant les colonnes
        if not df_ventes.empty:
            df = pd.merge(df_ventes, df_produits, on="produit_id")
            df = pd.merge(df, df_clients, on="client_id")

            # Conversion des dates et calculs
            df['date'] = pd.to_datetime(df['date'])
            df['mois'] = df['date'].dt.strftime('%Y-%m')
            df['chiffre_affaires'] = df['quantite'] * df['prix']

            # Suppression uniquement des colonnes existantes
            cols_to_drop = [col for col in ['id', 'id_vente'] if col in df.columns]
            if cols_to_drop:
                df = df.drop(columns=cols_to_drop)

            conn.close()
            return df
        else:
            st.warning("Aucune donnée de vente trouvée dans la base.")
            return pd.DataFrame()

    except sqlite3.Error as e:
        st.error(f"Erreur de base de données : {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erreur de traitement : {str(e)}")
        return pd.DataFrame()

def display_metrics(df):
    """Affiche les indicateurs clés"""
    if df.empty:
        st.warning("Aucune donnée disponible pour afficher les métriques")
        return

    st.header("📊 Vue d'Ensemble")
    cols = st.columns(4)

    try:
        metrics = {
            "CA Total": f"{df['ca_cfa'].sum():,.0f} FCFA",
            "Produit Phare": df.loc[df['ca_cfa'].idxmax(), 'produit'],
            "Panier Moyen": f"{df['ca_cfa'].sum() / df['quantite'].sum():,.0f} FCFA",
            "Transactions": f"{df['quantite'].sum():,.0f}"
        }

        for col, (name, value) in zip(cols, metrics.items()):
            with col:
                st.markdown(f"""
                <div style="
                    background: white;
                    border-radius: 10px;
                    padding: 15px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    text-align: center;
                ">
                    <h3 style="margin:0;color:#555;">{name}</h3>
                    <p style="font-size:24px;margin:10px 0;font-weight:bold;">{value}</p>
                </div>
                """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erreur dans l'affichage des métriques: {e}")


def display_charts(df):
    """Affiche les visualisations"""
    if df.empty:
        st.warning("Aucune donnée disponible pour afficher les graphiques")
        return

    st.header("📈 Analyse des Ventes")
    tab1, tab2, tab3 = st.tabs(["Répartition", "Évolution", "Comparaison"])

    with tab1:
        try:
            fig = px.pie(
                df,
                values='ca_cfa',
                names='produit',
                title='Répartition du CA par Produit',
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Viridis
            )
            fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.2))
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Erreur dans le graphique de répartition: {e}")

    with tab2:
        try:
            if 'mois' in df.columns:
                monthly = df.groupby('mois', as_index=False).agg({'ca_cfa': 'sum', 'quantite': 'sum'})
                fig = px.line(
                    monthly,
                    x='mois',
                    y='ca_cfa',
                    title='Évolution Mensuelle du CA',
                    markers=True,
                    labels={'ca_cfa': 'CA (FCFA)', 'mois': 'Mois'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Données temporelles non disponibles")
        except Exception as e:
            st.error(f"Erreur dans le graphique d'évolution: {e}")

    with tab3:
        try:
            fig = px.bar(
                df.sort_values('ca_cfa', ascending=False),
                x='produit',
                y=['ca_cfa', 'quantite'],
                barmode='group',
                title='Comparaison Produits',
                labels={'value': 'Valeur', 'variable': 'Métrique'},
                color_discrete_sequence=['#636EFA', '#00CC96']
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Erreur dans le graphique de comparaison: {e}")


def display_data_table(df):
    """Affiche le tableau de données avec filtres"""
    if df.empty:
        st.warning("Aucune donnée disponible pour afficher le tableau")
        return

    st.header("🔍 Données Détailées")
    with st.expander("🔎 Filtres", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            min_ca = st.slider("CA Minimum (FCFA)", 0, int(df['ca_cfa'].max()), 0)
        with col2:
            selected = st.multiselect(
                "Produits",
                df['produit'].unique(),
                default=df['produit'].unique()
            )

    filtered = df[(df['ca_cfa'] >= min_ca) & (df['produit'].isin(selected))]

    try:
        st.dataframe(
            filtered.style
            .background_gradient(subset=['ca_cfa'], cmap='Blues')
            .format({'ca_cfa': '{:,.0f} FCFA'}),
            height=500,
            use_container_width=True
        )

        st.download_button(
            "💾 Exporter les données",
            filtered.to_csv(index=False).encode('utf-8'),
            "export_ventes.csv",
            "text/csv"
        )
    except Exception as e:
        st.error(f"Erreur dans l'affichage du tableau: {e}")


def admin_section():
    """Section réservée à l'administrateur"""
    if st.session_state.get('role') != 'admin':
        return

    with st.expander("⚙️ Administration", expanded=False):
        st.subheader("Gestion des Utilisateurs")

        # Afficher la liste des utilisateurs
        try:
            conn = sqlite3.connect(str(DB_PATH))
            users_df = pd.read_sql("SELECT username, full_name, role FROM users", conn)
            st.dataframe(users_df, hide_index=True)
        except Exception as e:
            st.error(f"Erreur lors du chargement des utilisateurs: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

        # Formulaire d'ajout d'utilisateur
        with st.form("add_user"):
            st.write("Ajouter un nouvel utilisateur")
            new_user = st.text_input("Nom d'utilisateur*")
            new_pass = st.text_input("Mot de passe*", type="password")
            full_name = st.text_input("Nom complet")
            is_admin = st.checkbox("Administrateur")

            if st.form_submit_button("Créer"):
                if not new_user or not new_pass:
                    st.error("Les champs marqués d'un * sont obligatoires")
                else:
                    try:
                        conn = sqlite3.connect(str(DB_PATH))
                        conn.execute(
                            "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
                            (new_user, hash_password(new_pass), full_name, 'admin' if is_admin else 'user')
                        )
                        conn.commit()
                        st.success(f"Utilisateur {new_user} créé avec succès!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Ce nom d'utilisateur existe déjà")
                    except Exception as e:
                        st.error(f"Erreur lors de la création: {e}")
                    finally:
                        if 'conn' in locals():
                            conn.close()


def main_dashboard():
    """Page principale du dashboard avec gestion intégrée des rapports PDF"""
    # Configuration de la page
    st.set_page_config(
        page_title="Tableau de Bord Commercial",
        page_icon="📊",
        layout="wide"
    )

    # Barre latérale améliorée
    with st.sidebar:
        # Section utilisateur
        st.markdown(f"""
        <div style="text-align:center;margin-bottom:30px;">
            <h2 style="color:#2c3e50;">Tableau de Bord</h2>
            <div style="background:#f8f9fa;padding:15px;border-radius:10px;">
                <p>👤 <strong>{st.session_state.get('full_name', st.session_state.get('username', 'Inconnu'))}</strong></p>
                <p style="color:{'#e74c3c' if st.session_state.get('role') == 'admin' else '#2ecc50'}; 
                          font-weight:bold;">
                    {st.session_state.get('role', 'user').upper()}
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Bouton de déconnexion
        if st.button("🚪 Se déconnecter", use_container_width=True, key="logout_btn"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.markdown("---")

        # Section administration
        admin_section()

        # Menu de navigation
        st.markdown("### 📂 Navigation")
        page_options = ["Tableau de bord", "Gestion PDF"]
        selected_page = st.radio("", page_options, label_visibility="collapsed")

    # Chargement des données (une seule fois)
    df = load_data()

    if df.empty:
        st.warning("Aucune donnée disponible pour l'analyse")
        return

    # Contenu principal conditionnel
    if selected_page == "Tableau de bord":
        display_dashboard_content(df)
    else:
        #display_pdf_tools(df)
        display_export_section(df)  # Ajoutez cette ligne


def display_dashboard_content(df):
    """Affiche le contenu principal du dashboard avec gestion des erreurs"""
    if df.empty:
        st.warning("Aucune donnée disponible pour l'analyse")
        return

    # Vérification et renommage des colonnes
    if 'nom_x' in df.columns and 'nom_y' in df.columns:
        df = df.rename(columns={'nom_x': 'produit', 'nom_y': 'client'})
    elif 'nom_x' in df.columns:
        df = df.rename(columns={'nom_x': 'produit'})

    # Création de la colonne ca_cfa si elle n'existe pas
    if 'chiffre_affaires' in df.columns:
        df['ca_cfa'] = df['chiffre_affaires']
    else:
        st.error("Colonne 'chiffre_affaires' manquante - impossible de calculer le CA")
        return

    # Section des métriques
    st.write("📈 Analyse des Ventes")

    try:
        # Calcul des indicateurs clés
        total_ca = df['ca_cfa'].sum()
        avg_ca = df['ca_cfa'].mean()
        nb_transactions = len(df)

        col1, col2, col3 = st.columns(3)
        col1.metric("CA Total", f"{total_ca:,.0f} FCFA")
        col2.metric("CA Moyen", f"{avg_ca:,.0f} FCFA")
        col3.metric("Nombre de ventes", nb_transactions)

    except Exception as e:
        st.error(f"Erreur dans l'affichage des métriques: {str(e)}")

    # Section des visualisations
    tab1, tab2, tab3 = st.tabs(["Répartition", "Évolution", "Comparaison"])

    with tab1:
        try:
            if 'produit' in df.columns:
                st.subheader("Répartition du CA par produit")
                ca_par_produit = df.groupby('produit')['ca_cfa'].sum().sort_values(ascending=False)
                st.bar_chart(ca_par_produit)
            else:
                st.warning("Colonne 'produit' manquante pour la répartition")
        except Exception as e:
            st.error(f"Erreur dans le graphique de répartition: {str(e)}")

    with tab2:
        try:
            # Vérifier si la colonne mois existe ou créer une colonne mois à partir de la date
            if 'date' in df.columns:
                df['mois'] = pd.to_datetime(df['date']).dt.to_period('M').astype(str)

            if 'mois' in df.columns:
                st.subheader("Évolution du CA par mois")
                ca_par_mois = df.groupby('mois')['ca_cfa'].sum().sort_index()
                st.line_chart(ca_par_mois)
            else:
                st.warning("Colonne 'mois' ou 'date' manquante pour l'évolution temporelle")
        except Exception as e:
            st.error(f"Erreur dans le graphique d'évolution: {str(e)}")

    with tab3:
        try:
            st.subheader("Comparaisons")

            # Exemple de comparaison entre produits et clients
            if 'produit' in df.columns and 'client' in df.columns:
                option = st.selectbox(
                    "Choisir une comparaison:",
                    ("Top 10 Produits", "Top 10 Clients", "CA par Produit et Client")
                )

                if option == "Top 10 Produits":
                    top_produits = df.groupby('produit')['ca_cfa'].sum().nlargest(10)
                    st.bar_chart(top_produits)
                elif option == "Top 10 Clients":
                    top_clients = df.groupby('client')['ca_cfa'].sum().nlargest(10)
                    st.bar_chart(top_clients)
                else:
                    pivot_table = df.pivot_table(values='ca_cfa', index='produit', columns='client', aggfunc='sum')
                    st.write(pivot_table)
            else:
                st.warning("Colonnes manquantes pour les comparaisons")
        except Exception as e:
            st.error(f"Erreur dans les comparaisons: {str(e)}")

    # Section des données détaillées
    st.write("🔍 Données Détailées")
    try:
        display_data_table(df)
    except Exception as e:
        st.error(f"Erreur dans l'affichage des données: {str(e)}")


def display_data_table(df):
    """Affiche le tableau de données avec filtres"""
    st.write("🔎 Filtres")

    # Vérification des colonnes avant filtrage
    available_columns = df.columns.tolist()

    col1, col2 = st.columns(2)

    with col1:
        if 'produit' in available_columns:
            produits = df['produit'].unique()
            sel_produit = st.multiselect("Produits", produits, default=produits)
        else:
            st.warning("Colonne 'produit' non disponible")

    with col2:
        if 'ca_cfa' in available_columns:
            min_ca = st.slider("CA Minimum (FCFA)", 0, int(df['ca_cfa'].max()), 0)
        else:
            st.warning("Colonne 'ca_cfa' non disponible")

    # Application des filtres
    filtered_df = df.copy()

    if 'produit' in available_columns and len(sel_produit) > 0:
        filtered_df = filtered_df[filtered_df['produit'].isin(sel_produit)]

    if 'ca_cfa' in available_columns:
        filtered_df = filtered_df[filtered_df['ca_cfa'] >= min_ca]

    st.dataframe(filtered_df)





def display_export_section(df):
    """Affiche la section d'export des données"""
    st.write("## 📤 Export des Données")

    with st.expander("Options d'Export", expanded=True):
        col1, col2 = st.columns([1, 2])

        with col1:
            export_format = st.radio(
                "Format d'export:",
                ["CSV", "Excel", "JSON"],
                index=0,
                horizontal=True
            )

        with col2:
            export_name = st.text_input(
                "Nom du fichier (sans extension)",
                value="export_ventes",
                help="Choisissez un nom pour votre fichier exporté"
            )

        if st.button("🔄 Générer l'Export", type="primary"):
            try:
                if export_format == "CSV":
                    data = df.to_csv(index=False)
                    file_ext = "csv"
                    mime_type = "text/csv"
                elif export_format == "Excel":
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name="Ventes")
                    data = output.getvalue()
                    file_ext = "xlsx"
                    mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                else:  # JSON
                    data = df.to_json(indent=2, orient="records")
                    file_ext = "json"
                    mime_type = "application/json"

                # Bouton de téléchargement
                st.download_button(
                    label=f"⬇️ Télécharger {export_format}",
                    data=data,
                    file_name=f"{export_name}.{file_ext}",
                    mime=mime_type,
                    help=f"Cliquez pour sauvegarder au format {export_format}"
                )

                st.success("Export généré avec succès!")

            except Exception as e:
                st.error(f"Erreur lors de l'export: {str(e)}")

import io  # Pour utiliser un buffer en mémoire


def display_export_options(df: pd.DataFrame, default_filename: str = "export") -> None:
    """
    Affiche les options d'exportation et permet le téléchargement des données.

    Args:
        df: DataFrame à exporter
        default_filename: Nom de fichier par défaut (sans extension)
    """
    st.write("### 📤 Options d'exportation")

    # Options d'export
    col1, col2 = st.columns(2)
    with col1:
        export_format = st.selectbox(
            "Format d'export :",
            ["CSV", "Excel", "JSON"],
            help="Sélectionnez le format de fichier pour l'export"
        )

    with col2:
        filename = st.text_input(
            "Nom du fichier :",
            value=default_filename,
            help="Nom du fichier (sans extension)"
        ).strip()

    # Bouton d'export
    if st.button("🔄 Générer l'export", type="primary"):
        try:
            if export_format == "CSV":
                export_data = df.to_csv(index=False)
                file_extension = "csv"
                mime_type = "text/csv"

            elif export_format == "Excel":
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name="Données")
                export_data = excel_buffer.getvalue()
                file_extension = "xlsx"
                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

            elif export_format == "JSON":
                export_data = df.to_json(indent=2, orient="records", force_ascii=False)
                file_extension = "json"
                mime_type = "application/json"

            # Téléchargement
            st.download_button(
                label=f"⬇️ Télécharger {export_format}",
                data=export_data,
                file_name=f"{filename}.{file_extension}",
                mime=mime_type,
                help=f"Cliquez pour télécharger le fichier {export_format}"
            )

            st.success(f"Export {export_format} prêt !")

        except Exception as e:
            st.error(f"Erreur lors de l'export : {str(e)}")
            st.exception(e)
# ---- EXECUTION ----
if __name__ == "__main__":
    # Initialisation de la base de données
    init_auth_db()

    # Vérification de l'authentification
    if not st.session_state.get('authenticated'):
        login_page()
    else:
        main_dashboard()