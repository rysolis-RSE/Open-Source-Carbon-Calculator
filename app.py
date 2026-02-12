import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from io import BytesIO
from fpdf import FPDF
import tempfile
import os

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

# --- 2. FONCTION BADGE (Image) ---
def create_linkedin_badge(company_name, total_co2, equivalent_trees):
    fig, ax = plt.subplots(figsize=(10, 6))
    # Couleurs sombres pour le badge (Style Dark Mode)
    fig.patch.set_facecolor('#0E1117')
    ax.set_facecolor('#0E1117')
    
    ax.text(0.5, 0.85, "CERTIFICAT DE MESURE 2025", ha='center', va='center', color='#2BDD66', fontsize=18, weight='bold')
    ax.text(0.5, 0.65, company_name.upper(), ha='center', va='center', color='white', fontsize=40, weight='heavy')
    ax.text(0.5, 0.45, f"Bilan Carbone : {total_co2:,.1f} tCO2e", ha='center', va='center', color='white', fontsize=28)
    ax.text(0.5, 0.30, f"Compensation théorique : {equivalent_trees:,.0f} arbres 🌳", ha='center', va='center', color='#AAAAAA', fontsize=16, style='italic')
    ax.text(0.5, 0.10, "Généré par OpenCarbon", ha='center', va='center', color='#2BDD66', fontsize=12)
    
    ax.axis('off')
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=200, bbox_inches='tight', facecolor='#0E1117')
    buf.seek(0)
    return buf

# --- 3. FONCTION PDF (Avec Badge inclus) ---
def create_pdf_report(company, data, total, trees, badge_buffer):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. En-tête
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 10, f"Rapport Bilan Carbone 2025", ln=True, align='C')
    pdf.set_font("Arial", 'I', 12)
    pdf.cell(0, 10, f"Entreprise : {company}", ln=True, align='C')
    pdf.ln(10)
    
    # 2. Le Badge en image (En haut à droite ou centré, ici on le met "en petit" à droite)
    # Astuce : On doit sauvegarder le buffer dans un fichier temporaire pour que FPDF puisse le lire
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
        tmp_file.write(badge_buffer.getvalue())
        tmp_filename = tmp_file.name
    
    # Insertion de l'image (x=150mm, y=10mm, largeur=40mm)
    pdf.image(tmp_filename, x=160, y=10, w=40)
    
    # 3. Détails des chiffres
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Synthese des Emissions", ln=True)
    pdf.set_font("Arial", '', 12)
    
    pdf.cell(0, 10, f"Total Emissions : {total:,.2f} tCO2e", ln=True)
    pdf.cell(0, 10, f"Equivalent Arbres : {trees:,.0f} arbres", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Details par poste :", ln=True)
    pdf.set_font("Arial", '', 11)
    
    for poste, val in data.items():
        # On convertit en tonnes pour le PDF
        val_t = val / 1000
        pdf.cell(100, 8, f"- {poste}", border=0)
        pdf.cell(50, 8, f"{val_t:,.2f} tCO2e", border=0, ln=True)
        
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 10)
    pdf.multi_cell(0, 5, "Ce rapport a ete genere automatiquement par OpenCarbon. Il respecte les grandes masses de la methodologie Bilan Carbone mais ne remplace pas un audit certifie.")

    # Nettoyage du fichier temporaire
    os.remove(tmp_filename)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 4. INTERFACE STREAMLIT ---

# Header
c1, c2 = st.columns([1, 4])
with c1: st.image("https://img.icons8.com/color/96/000000/leaf.png", width=80)
with c2: 
    st.title("OpenCarbon Calculator")
    st.markdown("**Bilan Carbone Open Source & Générateur de Rapport CSRD**")

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
    "Chauffage/Flotte (S1)": data_input["Gaz"] * FACTEURS["Gaz Naturel"], # Simplifié pour démo
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

# Génération des Assets (Badge + PDF)
badge_buffer = create_linkedin_badge(company_name, total_tco2, arbres_equivalents)
pdf_bytes = create_pdf_report(company_name, emissions, total_tco2, arbres_equivalents, badge_buffer)

# Section Téléchargement
st.markdown("---")
st.header("🚀 Exports & Communication")

col_L, col_R = st.columns([1, 1])

with col_L:
    st.subheader("1. Badge LinkedIn")
    st.image(badge_buffer, caption="Visuel Réseaux Sociaux", use_container_width=True)
    st.download_button("📥 Télécharger Badge (PNG)", badge_buffer, "Badge_Climat.png", "image/png")

with col_R:
    st.subheader("2. Rapport Officiel (PDF)")
    st.info("Le rapport contient le détail des calculs et inclut votre Badge de certification en haut à droite.")
    
    # Affichage d'un aperçu visuel (fictif) du PDF pour faire joli
    st.markdown("""
    <div style="border:1px solid #ddd; padding:10px; border-radius:5px; background-color:#fff; color:#333; height:200px; overflow:hidden; font-family:Arial; font-size:10px;">
        <b>Rapport Bilan Carbone 2025</b><br>
        <i>Entreprise : ...</i><br><br>
        Total Emissions : ... tCO2e<br>
        <div style="text-align:right; margin-top:-40px;"><span style="background-color:#000; color:#fff; padding:2px;">BADGE</span></div>
        <br>...
    </div>
    """, unsafe_allow_html=True)
    
    st.download_button("📄 Télécharger Rapport (PDF)", pdf_bytes, "Rapport_RSE.pdf", "application/pdf")
