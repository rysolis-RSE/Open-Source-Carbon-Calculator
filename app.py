import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from fpdf import FPDF

# --- CONFIGURATION DU SITE ---
st.set_page_config(page_title="OpenCarbon | Calculateur CSRD", layout="wide", page_icon="🌱")

# --- STYLE CSS ---
st.markdown("""
<style>
    .metric-card {background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center;}
    .stButton>button {width: 100%; border-radius: 20px;}
</style>
""", unsafe_allow_html=True)

# --- 1. DONNÉES & FACTEURS ---
FACTEURS = {
    "Electricité (France)": 0.06, 
    "Gaz Naturel": 0.22, 
    "Essence/Diesel": 2.5, 
    "Achats Services": 0.15, 
    "Achats Informatiques": 0.25,
    "Publicité & Marketing": 0.10,
    "Matériel IT": 0.80, 
    "Déplacements": 0.50,
}

# --- 2. FONCTION PDF (Sobre) ---
def create_pdf_report(company, data, total, trees):
    pdf = FPDF()
    pdf.add_page()
    
    # En-tête Corporate
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 10, f"Rapport Bilan Carbone 2025", ln=True, align='L')
    pdf.set_font("Arial", 'I', 12)
    pdf.cell(0, 10, f"Societe : {company}", ln=True, align='L')
    pdf.line(10, 30, 200, 30) # Ligne de séparation
    pdf.ln(20)
    
    # Résumé
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Synthese des Emissions", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Total Emissions : {total:,.2f} tCO2e", ln=True)
    pdf.cell(0, 10, f"Compensation theorique : {trees:,.0f} arbres", ln=True)
    pdf.ln(10)
    
    # Détails
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Details par poste :", ln=True)
    pdf.set_font("Arial", '', 11)
    
    # Tableau simple
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(100, 10, "Poste d'emission", 1, 0, 'C', 1)
    pdf.cell(50, 10, "tCO2e", 1, 1, 'C', 1)
    
    for poste, val in data.items():
        val_t = val / 1000
        pdf.cell(100, 10, f" {poste}", 1)
        pdf.cell(50, 10, f"{val_t:,.2f}", 1, 1, 'R')
        
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 8)
    pdf.multi_cell(0, 5, "Document genere automatiquement par OpenCarbon. Ce rapport est une estimation basee sur les facteurs monetaires et physiques standards.")

    return pdf.output(dest='S').encode('latin-1')

# --- 3. INTERFACE STREAMLIT ---

# Header
c1, c2 = st.columns([1, 4])
with c1: st.image("https://img.icons8.com/color/96/000000/leaf.png", width=80)
with c2: 
    st.title("OpenCarbon Calculator")
    st.markdown("**Bilan Carbone Open Source & Reporting CSRD**")

st.markdown("---")

# Sidebar
st.sidebar.header("🏢 Paramètres")
company_name = st.sidebar.text_input("Entreprise", "Ma Super Boite")
nb_employes = st.sidebar.number_input("Employés", value=10, min_value=1)

# Saisie
st.subheader("📝 Données d'activité")
tab1, tab2, tab3 = st.tabs(["🔥 Energie (S1/S2)", "💸 Achats (S3)", "✈️ Déplacements (S3)"])

data_input = {}
with tab1:
    c1, c2 = st.columns(2)
    data_input["Elec"] = c1.number_input("Électricité (kWh)", 10000)
    data_input["Gaz"] = c2.number_input("Gaz/Carburant (kWh/L)", 500)
with tab2:
    c1, c2 = st.columns(2)
    data_input["Services"] = c1.number_input("Services & Pub (€)", 50000)
    data_input["IT"] = c2.number_input("Numérique & Matériel (€)", 20000)
with tab3:
    data_input["Deplacement"] = st.number_input("Budget Voyage (€)", 20000)

# Calculs
emissions = {
    "Energie (S2)": data_input["Elec"] * FACTEURS["Electricité (France)"],
    "Chauffage/Flotte (S1)": data_input["Gaz"] * FACTEURS["Gaz Naturel"],
    "Services (S3)": data_input["Services"] * FACTEURS["Achats Services"],
    "Numérique (S3)": data_input["IT"] * FACTEURS["Achats Informatiques"],
    "Déplacements (S3)": data_input["Deplacement"] * FACTEURS["Déplacements"]
}

df_res = pd.DataFrame(list(emissions.items()), columns=["Poste", "kgCO2e"])
df_res["tCO2e"] = df_res["kgCO2e"] / 1000
total_tco2 = df_res["tCO2e"].sum()
arbres_equivalents = total_tco2 * 40

# Affichage Résultats
st.markdown("---")
st.header("📊 Résultats")
col1, col2, col3 = st.columns(3)
col1.metric("Total", f"{total_tco2:,.1f} tCO2e")
col2.metric("Par employé", f"{total_tco2/nb_employes:,.1f} tCO2e")
col3.metric("Arbres", f"{arbres_equivalents:,.0f} 🌳")

# Graphiques
c_chart1, c_chart2 = st.columns([2, 1])
with c_chart1:
    fig_bar = px.bar(df_res, x="tCO2e", y="Poste", orientation='h', text_auto='.1f', color="tCO2e", color_continuous_scale="Greens")
    st.plotly_chart(fig_bar, use_container_width=True)
with c_chart2:
    fig_pie = px.pie(df_res, values='tCO2e', names='Poste', hole=0.6, color_discrete_sequence=px.colors.sequential.Greens_r)
    st.plotly_chart(fig_pie, use_container_width=True)

# Export PDF
st.markdown("---")
st.header("📄 Export Officiel")
st.info("Téléchargez votre rapport complet au format PDF.")

pdf_bytes = create_pdf_report(company_name, emissions, total_tco2, arbres_equivalents)

st.download_button(
    label="📥 Télécharger Rapport PDF",
    data=pdf_bytes,
    file_name="Rapport_RSE.pdf",
    mime="application/pdf"
)
