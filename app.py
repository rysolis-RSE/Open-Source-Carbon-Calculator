import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="OpenCarbon Enterprise", layout="wide")

# --- 1. RÉFÉRENTIEL FACTEURS ---
FE = {
    "Electricité (FR)": 0.052, 
    "Gaz": 0.227, 
    "Services": 0.14, 
    "Numérique": 0.50,
    "Avion": 0.25,
}

# --- 2. FONCTIONS DE VISUALISATION ---
def plot_sankey(data_dict):
    nodes = ["Bilan Total", "Scope 1", "Scope 2", "Scope 3", "Energie", "Achats", "Voyages", "Numérique"]
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
        node = dict(pad=15, thickness=20, label=nodes, color="#1b5e20"),
        link = dict(source=[l['source'] for l in links], target=[l['target'] for l in links], 
                    value=[l['value'] for l in links], color="rgba(200, 200, 200, 0.4)")
    )])
    return fig

def generate_pdf_report(company, total, val_s1, val_s2, val_s3):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Rapport de Performance Carbone - {company}", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Bilan Total : {total:,.2f} tCO2e", ln=True)
    pdf.cell(0, 10, f"- Scope 1 : {val_s1:,.2f} tCO2e", ln=True)
    pdf.cell(0, 10, f"- Scope 2 : {val_s2:,.2f} tCO2e", ln=True)
    pdf.cell(0, 10, f"- Scope 3 : {val_s3:,.2f} tCO2e", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- 3. INTERFACE ---
with st.sidebar:
    st.title("OpenCarbon Enterprise")
    company = st.text_input("Organisation", "Global Services Ltd")
    audit_mode = st.toggle("🛡️ Mode Audit", value=False)
    prix_carbone = st.number_input("Shadow Price (€/tCO2e)", value=100)

t_data, t_bi, t_strat, t_rep = st.tabs(["Collecte", "Business Intelligence", "Plan de Transition", "Rapport"])

with t_data:
    st.subheader("Saisie des flux d'activité")
    c1, c2 = st.columns(2)
    with c1:
        s1_val = st.number_input("Combustibles (kWh)", value=50000)
        s2_val = st.number_input("Electricité (kWh)", value=120000)
    with c2:
        it_val = st.number_input("Budget IT (€)", value=25000)
        achats_val = st.number_input("Budget Services (€)", value=200000)
        voyages_val = st.number_input("Kms Avion", value=500000)

    val_s1, val_s2 = s1_val * FE["Gaz"]/1000, s2_val * FE["Electricité (FR)"]/1000
    val_it, val_achats, val_voyages = it_val * FE["Numérique"]/1000, achats_val * FE["Services"]/1000, voyages_val * FE["Avion"]/1000
    val_s3 = val_it + val_achats + val_voyages
    total = val_s1 + val_s2 + val_s3

with t_bi:
    k1, k2, k3 = st.columns(3)
    k1.metric("Bilan Total", f"{total:,.1f} tCO2e")
    k2.metric("Risque Financier", f"{total * prix_carbone:,.0f} €")
    k3.metric("Intensité S3", f"{(val_s3/total)*100:.1f}%")
    st.plotly_chart(plot_sankey({'S1': val_s1, 'S2': val_s2, 'S3': val_s3, 'IT': val_it, 'Achats': val_achats, 'Voyages': val_voyages}), use_container_width=True)

with t_strat:
    st.subheader("Marginal Abatement Cost Curve")
    actions = pd.DataFrame({
        "Action": ["Télétravail", "LED", "Solaire", "Véhicules Elec", "Cloud Vert"],
        "Réduction (tCO2e)": [8, 5, 12, 20, 4],
        "Coût (€/tCO2e)": [-200, -150, -50, 120, 45]
    }).sort_values("Coût (€/tCO2e)")
    fig_macc = px.bar(actions, x="Action", y="Coût (€/tCO2e)", color="Coût (€/tCO2e)", color_continuous_scale="RdYlGn_r")
    st.plotly_chart(fig_macc, use_container_width=True)

with t_rep:
    st.subheader("Export Réglementaire")
    if st.button("Générer le PDF"):
        pdf_data = generate_pdf_report(company, total, val_s1, val_s2, val_s3)
        st.download_button("Télécharger le rapport", pdf_data, "Rapport_Carbone.pdf", "application/pdf")
