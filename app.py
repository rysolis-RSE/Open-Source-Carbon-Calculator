import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="OpenCarbon Enterprise", layout="wide", page_icon="🏦")

# --- 1. RÉFÉRENTIEL FACTEURS (GHG PROTOCOL) ---
FE = {
    "Electricité (FR)": 0.052, 
    "Gaz": 0.227, 
    "Fioul": 0.324,
    "Services": 0.14, 
    "Numérique": 0.50, # Ratio hybride matériel/cloud
    "Avion": 0.25, 
    "Train": 0.003, 
    "Voiture": 0.21
}

# --- 2. FONCTIONS DE VISUALISATION ---
def plot_sankey(data_dict):
    """Diagramme de flux Scopes -> Catégories"""
    nodes = ["Bilan Total", "Scope 1", "Scope 2", "Scope 3", 
             "Energie", "Achats", "Voyages", "Numérique"]
    
    links = [
        {"source": 1, "target": 4, "value": data_dict['S1']},
        {"source": 2, "target": 4, "value": data_dict['S2']},
        {"source": 3, "target": 5, "value": data_dict['Achats']},
        {"source": 3, "target": 6, "value": data_dict['Voyages']},
        {"source": 3, "target": 7, "value": data_dict['IT']},
        {"source": 0, "target": 1, "value": data_dict['S1']},
        {"source": 0, "target": 2, "value": data_dict['S2']},
        {"source": 0, "target": 3, "value": data_dict['S3']},
    ]
    
    fig = go.Figure(data=[go.Sankey(
        node = dict(pad = 15, thickness = 20, line = dict(color = "black", width = 0.5),
            label = nodes, color = "#2e7d32"),
        link = dict(
            source = [l['source'] for l in links],
            target = [l['target'] for l in links],
            value = [l['value'] for l in links],
            color = "rgba(46, 125, 50, 0.4)"
        ))])
    return fig

# --- 3. INTERFACE SIDEBAR ---
with st.sidebar:
    st.title("🏦 OpenCarbon Enterprise")
    st.caption("Version 2025.1 - Full Features")
    st.markdown("---")
    comp = st.text_input("Organisation", "Global Services Ltd")
    
    # RETOUR DU MODE AUDIT
    audit_mode = st.toggle("🛡️ Mode Audit (Justificatifs)", value=False)
    
    st.markdown("---")
    prix_carbone = st.number_input("Shadow Price (€/tCO2e)", value=100)

# --- TABS ---
t_data, t_bi, t_strat, t_rep = st.tabs(["📋 Collecte & Qualité", "📊 Business Intelligence", "📈 Plan de Transition", "📜 Rapport CSRD"])

# --- TAB 1 : COLLECTE & QUALITÉ ---
with t_data:
    st.subheader("Saisie des flux d'activité")
    c1, c2 = st.columns(2)
    
    with c1:
        st.info("**Scope 1 & 2**")
        s1_val = st.number_input("Combustibles / Gaz (kWh)", value=50000)
        if audit_mode:
            st.select_slider("Preuve S1", ["Aucune", "Facture", "Compteur certifié"], key="q1")
            
        s2_val = st.number_input("Electricité (kWh)", value=120000)
        if audit_mode:
            st.select_slider("Preuve S2", ["Aucune", "Facture", "Garantie Origine"], key="q2")

    with c2:
        st.info("**Scope 3 (Dépenses & Kms)**")
        it_val = st.number_input("Budget Hardware/IT (€)", value=25000)
        achats_val = st.number_input("Budget Services (€)", value=200000)
        voyages_val = st.number_input("Kms Avion (Passager.km)", value=500000)
        if audit_mode:
            st.file_uploader("Upload FEC (Fichier Ecritures Comptables)", type=["csv", "xlsx"])

    # CALCULS
    val_s1 = s1_val * FE["Gaz"] / 1000
    val_s2 = s2_val * FE["Electricité (FR)"] / 1000
    val_it = it_val * FE["Numérique"] / 1000
    val_achats = achats_val * FE["Services"] / 1000
    val_voyages = voyages_val * FE["Avion"] / 1000
    val_s3 = val_it + val_achats + val_voyages
    total = val_s1 + val_s2 + val_s3

# --- TAB 2 : BI (AVEC SANKEY) ---
with t_bi:
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Bilan Total", f"{total:,.1f} tCO2e")
    k2.metric("Risque Financier", f"{total * prix_carbone:,.0f} €")
    k3.metric("Scope 3", f"{(val_s3/total)*100:.1f}%")
    k4.metric("Fiabilité Data", "Excellent" if not audit_mode else "Audit-Ready")

    st.markdown("---")
    
    c_sankey, c_radar = st.columns([2, 1])
    with c_sankey:
        st.subheader("Visualisation des Flux (Sankey Diagram)")
        st.plotly_chart(plot_sankey({
            'S1': val_s1, 'S2': val_s2, 'S3': val_s3, 
            'IT': val_it, 'Achats': val_achats, 'Voyages': val_voyages
        }), use_container_width=True)
    
    with c_radar:
        st.subheader("Structure par Scope")
        fig_pie = px.pie(values=[val_s1, val_s2, val_s3], names=['Scope 1', 'Scope 2', 'Scope 3'], hole=0.5)
        st.plotly_chart(fig_pie, use_container_width=True)

# --- TAB 3 : STRATEGIE (MACC CURVE) ---
with t_strat:
    st.subheader("Courbe d'Abattement Marginal (MACC)")
    st.caption("Classement des actions par rentabilité carbone et financière.")
    
    # Données MACC
    actions = pd.DataFrame({
        "Action": ["Télétravail 2j", "LED & Capteurs", "Solaire Toiture", "Flotte Electrique", "Cloud Vert"],
        "Réduction (tCO2e)": [8, 5, 12, 20, 4],
        "Coût (€/tCO2e)": [-200, -150, -50, 120, 45] # Le négatif signifie "Rentable"
    }).sort_values("Coût (€/tCO2e)")

    fig_macc = px.bar(actions, x="Action", y="Coût (€/tCO2e)", color="Coût (€/tCO2e)",
                      text="Réduction (tCO2e)", color_continuous_scale="RdYlGn_r")
    fig_macc.add_hline(y=0, line_dash="dash", line_color="black")
    st.plotly_chart(fig_macc, use_container_width=True)

# --- TAB 4 : EXPORT ---
with t_rep:
    st.subheader("Génération Rapport Réglementaire")
    st.markdown("Exportez les résultats pour votre déclaration CSRD.")
    if st.button("📄 Télécharger Rapport Expert"):
        st.balloons()
        st.info("Export PDF en cours de génération...")
