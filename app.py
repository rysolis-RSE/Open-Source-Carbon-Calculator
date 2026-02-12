import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="OpenCarbon Enterprise", layout="wide", page_icon="🏦")

# --- 1. REFERENTIEL FACTEURS (CORRIGÉ) ---
# Les noms ici doivent correspondre EXACTEMENT à ceux utilisés dans les calculs plus bas
FE = {
    "Electricité (FR)": 0.052, 
    "Gaz": 0.227, 
    "Fioul": 0.324,
    "Services": 0.14, 
    "Numérique": 0.50, # Ajout de la clé manquante (moyenne matériel/saas)
    "Avion": 0.25, 
    "Train": 0.003, 
    "Voiture": 0.21
}

# --- 2. FONCTIONS DE VISUALISATION ---
def plot_sankey(data_dict):
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

# --- 3. INTERFACE ---
with st.sidebar:
    st.title("🏦 OpenCarbon Enterprise")
    st.caption("Version 2025.1 - Compliance Audit Ready")
    st.markdown("---")
    comp = st.text_input("Organisation", "Global Services Ltd")
    prix_carbone = st.number_input("Shadow Price (€/tCO2e)", value=100)

# --- TABS ---
t_data, t_bi, t_strat = st.tabs(["📋 Collecte de Données", "📊 Business Intelligence", "📈 Plan de Transition"])

# --- TAB 1 : COLLECTE ---
with t_data:
    st.subheader("Saisie des flux d'activité")
    c1, c2 = st.columns(2)
    
    with c1:
        st.info("**Scope 1 & 2**")
        s1_val = st.number_input("Combustibles / Gaz (kWh)", value=50000)
        s2_val = st.number_input("Electricité (kWh)", value=120000)

    with c2:
        st.info("**Scope 3**")
        it_val = st.number_input("Budget Hardware/IT (€)", value=25000)
        achats_val = st.number_input("Budget Services (€)", value=200000)
        voyages_val = st.number_input("Kms Avion (Passager.km)", value=500000)

    # CALCULS (Vérifiés avec le dictionnaire FE)
    val_s1 = s1_val * FE["Gaz"] / 1000
    val_s2 = s2_val * FE["Electricité (FR)"] / 1000
    val_it = it_val * FE["Numérique"] / 1000
    val_achats = achats_val * FE["Services"] / 1000
    val_voyages = voyages_val * FE["Avion"] / 1000
    val_s3 = val_it + val_achats + val_voyages
    total = val_s1 + val_s2 + val_s3

# --- TAB 2 : BI ---
with t_bi:
    k1, k2, k3 = st.columns(3)
    k1.metric("Bilan Total", f"{total:,.1f} tCO2e")
    k2.metric("Risque Financier", f"{total * prix_carbone:,.0f} €")
    k3.metric("Part du Scope 3", f"{(val_s3/total)*100:.1f}%")

    st.markdown("---")
    
    st.subheader("Flux d'émissions (Sankey Diagram)")
    st.plotly_chart(plot_sankey({
        'S1': val_s1, 'S2': val_s2, 'S3': val_s3, 
        'IT': val_it, 'Achats': val_achats, 'Voyages': val_voyages
    }), use_container_width=True)

# --- TAB 3 : STRATEGIE ---
with t_strat:
    st.subheader("Optimisation du Plan de Transition")
    # Simulation simple
    reduction = st.slider("Objectif de réduction (%)", 0, 50, 15)
    st.write(f"En réduisant de {reduction}%, vous évitez l'émission de **{total * reduction / 100:.1f} tonnes de CO2**.")
    st.write(f"Economie financière potentielle sur la taxe carbone : **{(total * reduction / 100) * prix_carbone:,.0f} €**.")
