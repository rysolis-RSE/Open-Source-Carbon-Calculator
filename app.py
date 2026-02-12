import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from io import BytesIO

# --- CONFIGURATION DU SITE ---
st.set_page_config(page_title="OpenCarbon | Calculateur CSRD", layout="wide", page_icon="🌱")

# --- STYLE CSS (Pour ressembler à une SaaS moderne) ---
st.markdown("""
<style>
    .metric-card {background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center;}
    .big-font {font-size: 24px !important; font-weight: bold;}
    .stButton>button {width: 100%; border-radius: 20px;}
</style>
""", unsafe_allow_html=True)

# --- 1. BASE DE DONNÉES FACTEURS D'ÉMISSION (Simplifiée - Méthode Hybride) ---
# Ces facteurs sont des moyennes ADEME / Base Empreinte
FACTEURS = {
    # Scope 1 & 2 (Physique)
    "Electricité (France)": 0.06, # kgCO2e / kWh
    "Gaz Naturel": 0.22, # kgCO2e / kWh
    "Essence/Diesel": 2.5, # kgCO2e / Litre
    
    # Scope 3 (Monétaire - Ratios "Spend-based" en kgCO2e par € dépensé)
    "Achats Services (Consulting, Juridique)": 0.15, 
    "Achats Informatiques (Licences, Cloud)": 0.25,
    "Publicité & Marketing": 0.10,
    "Matériel IT (PC, Tel)": 0.80, # Forte intensité carbone
    "Déplacements (Mixte)": 0.50,
}

# --- 2. FONCTION GÉNÉRATEUR D'IMAGE LINKEDIN (VIRALITÉ) ---
def create_linkedin_badge(company_name, total_co2, equivalent_trees):
    # Création d'une image avec Matplotlib
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Fond dégradé (simulé par une couleur solide moderne)
    fig.patch.set_facecolor('#0E1117')
    ax.set_facecolor('#0E1117')
    
    # Textes
    ax.text(0.5, 0.85, "CERTIFICAT DE MESURE 2025", ha='center', va='center', color='#2BDD66', fontsize=18, weight='bold')
    ax.text(0.5, 0.65, company_name.upper(), ha='center', va='center', color='white', fontsize=40, weight='heavy')
    
    ax.text(0.5, 0.45, f"Bilan Carbone : {total_co2:,.0f} tCO2e", ha='center', va='center', color='white', fontsize=28)
    ax.text(0.5, 0.30, f"Soit l'absorption de {equivalent_trees:,.0f} arbres 🌳", ha='center', va='center', color='#AAAAAA', fontsize=16, style='italic')
    
    ax.text(0.5, 0.10, "Généré par OpenCarbon (Open Source)", ha='center', va='center', color='#2BDD66', fontsize=12)
    
    # Enlever les axes
    ax.axis('off')
    
    # Sauvegarde dans un buffer
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=200, bbox_inches='tight', facecolor='#0E1117')
    buf.seek(0)
    return buf

# --- 3. INTERFACE UTILISATEUR ---

# Header
c1, c2 = st.columns([1, 4])
with c1:
    st.image("https://img.icons8.com/color/96/000000/leaf.png", width=80)
with c2:
    st.title("OpenCarbon Calculator")
    st.markdown("**Le bilan carbone Open Source pour les PME modernes.**")

st.markdown("---")

# Sidebar : Profil Entreprise
st.sidebar.header("🏢 Votre Entreprise")
company_name = st.sidebar.text_input("Nom de l'entreprise", "Ma Super Boite")
secteur = st.sidebar.selectbox("Secteur", ["Services / Tech", "Commerce", "Industrie", "Autre"])
nb_employes = st.sidebar.number_input("Nombre d'employés", value=10, min_value=1)

# --- 4. SAISIE DES DONNÉES (INPUT) ---
st.subheader("📝 Saisissez vos données annuelles")
st.info("Remplissez ce que vous connaissez. Les calculs sont automatiques.")

tab1, tab2, tab3 = st.tabs(["🔥 Scope 1 & 2 (Énergie)", "💸 Scope 3 (Achats)", "✈️ Scope 3 (Déplacements)"])

data_input = {}

with tab1:
    c1, c2, c3 = st.columns(3)
    data_input["Elec"] = c1.number_input("Électricité (kWh)", value=10000)
    data_input["Gaz"] = c2.number_input("Gaz (kWh)", value=0)
    data_input["Carburant"] = c3.number_input("Carburant Flotte (Litres)", value=500)

with tab2:
    st.caption("Méthode 'Monétaire' : Entrez vos dépenses annuelles HT en Euros.")
    c1, c2 = st.columns(2)
    data_input["Achats_Service"] = c1.number_input("Prestations Service (Consulting, RH, Avocats)", value=50000)
    data_input["Achats_Pub"] = c2.number_input("Publicité & Marketing (Ads, Events)", value=10000)
    
    c3, c4 = st.columns(2)
    data_input["Achats_IT_Soft"] = c3.number_input("Logiciels & Cloud (AWS, SaaS)", value=15000)
    data_input["Achats_IT_Hard"] = c4.number_input("Achat Matériel IT (PC, Ecrans...)", value=5000)

with tab3:
    st.caption("Si vous ne connaissez pas les km, estimez le budget déplacement.")
    data_input["Deplacement_Budget"] = st.number_input("Budget Train/Avion/Hôtel (€)", value=20000)


# --- 5. MOTEUR DE CALCUL (BACKEND) ---
# Calcul des émissions par poste
emissions = {
    "Energie (S2)": data_input["Elec"] * FACTEURS["Electricité (France)"],
    "Chauffage/Flotte (S1)": (data_input["Gaz"] * FACTEURS["Gaz Naturel"]) + (data_input["Carburant"] * FACTEURS["Essence/Diesel"]),
    "Services & Pub (S3)": (data_input["Achats_Service"] * FACTEURS["Achats Services (Consulting, Juridique)"]) + (data_input["Achats_Pub"] * FACTEURS["Publicité & Marketing"]),
    "Numérique (S3)": (data_input["Achats_IT_Soft"] * FACTEURS["Achats Informatiques (Licences, Cloud)"]) + (data_input["Achats_IT_Hard"] * FACTEURS["Matériel IT (PC, Tel)"]),
    "Déplacements (S3)": data_input["Deplacement_Budget"] * FACTEURS["Déplacements (Mixte)"]
}

# Conversion en Tonnes
df_res = pd.DataFrame(list(emissions.items()), columns=["Poste", "kgCO2e"])
df_res["tCO2e"] = df_res["kgCO2e"] / 1000
total_tco2 = df_res["tCO2e"].sum()

# KPIs d'intensité
tco2_par_employe = total_tco2 / nb_employes
# 1 arbre absorbe ~25kg par an (moyenne très large) -> ~40 arbres pour 1 tonne
arbres_equivalents = total_tco2 * 40

# --- 6. DASHBOARD (OUTPUT) ---
st.markdown("---")
st.header("📊 Votre Bilan Carbone 2025")

# KPIs en haut
col1, col2, col3, col4 = st.columns(4)
col1.metric("Emissions Totales", f"{total_tco2:,.1f} tCO2e")
col2.metric("Intensité / Employé", f"{tco2_par_employe:,.1f} tCO2e/pax", delta="Moyenne PME: 3-5t")
col3.metric("Equivalence Arbres", f"{arbres_equivalents:,.0f} 🌳")
col4.metric("Score Green", "B" if tco2_par_employe < 4 else "C", help="Score indicatif")

# Graphiques
c_chart1, c_chart2 = st.columns([2, 1])

with c_chart1:
    st.subheader("Répartition par poste d'émission")
    fig_bar = px.bar(df_res, x="tCO2e", y="Poste", orientation='h', text_auto='.1f', color="tCO2e", color_continuous_scale="Greens")
    st.plotly_chart(fig_bar, use_container_width=True)

with c_chart2:
    st.subheader("Répartition Scopes")
    # On regroupe vite fait pour le Pie Chart
    scope_data = {
        "Scope 1 (Direct)": emissions["Chauffage/Flotte (S1)"],
        "Scope 2 (Elec)": emissions["Energie (S2)"],
        "Scope 3 (Indirect)": emissions["Services & Pub (S3)"] + emissions["Numérique (S3)"] + emissions["Déplacements (S3)"]
    }
    fig_pie = px.pie(values=list(scope_data.values()), names=list(scope_data.keys()), hole=0.6, color_discrete_sequence=['#FF4B4B', '#FFAA00', '#00CC96'])
    st.plotly_chart(fig_pie, use_container_width=True)

# --- 7. LE "HOOK" LINKEDIN (LA FONCTIONNALITÉ VIRALE) ---
st.markdown("---")
st.header("🚀 Communiquez votre engagement !")
st.markdown("Générez votre badge officiel pour annoncer à votre réseau que vous avez mesuré votre impact.")

col_badge_L, col_badge_R = st.columns([1, 1])

with col_badge_L:
    # Génération de l'image
    badge_buffer = create_linkedin_badge(company_name, total_tco2, arbres_equivalents)
    st.image(badge_buffer, caption="Votre Badge LinkedIn", use_container_width=True)

with col_badge_R:
    st.info("💡 **Pourquoi poster ?** \n\n84% des talents préfèrent postuler dans une entreprise engagée. Montrez que vous ne faites pas que du 'Blabla', mais de la mesure concrète.")
    
    st.download_button(
        label="📥 Télécharger mon Badge (PNG)",
        data=badge_buffer,
        file_name=f"Bilan_Carbone_{company_name}.png",
        mime="image/png"
    )
    
    st.markdown("### Exemple de texte pour votre post :")
    st.code(f"""🚀 {company_name} s'engage pour le climat !

Nous venons de réaliser notre Bilan Carbone Open Source.
🔍 Résultat : {total_tco2:.1f} tonnes de CO2e.

C'est le début de notre trajectoire de réduction.
Prochaine étape : réduire le scope 3 ! 🌱

#CSRD #BilanCarbone #Transparence #ClimateAction""", language="text")
