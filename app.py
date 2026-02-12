import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF

# --- CONFIGURATION ---
st.set_page_config(page_title="OpenCarbon Ultimate", layout="wide", page_icon="💎")

# --- CSS PRO ---
st.markdown("""
<style>
    .metric-card {background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #2BDD66;}
    h1, h2, h3 {font-family: 'Helvetica Neue', sans-serif;}
</style>
""", unsafe_allow_html=True)

# --- 1. MOTEUR DE CALCUL (HYBRIDE) ---
# Facteurs d'émission (Source: Base Empreinte / Exurgue)
FE = {
    # Physique (Précis)
    "Elec": 0.06,       # kgCO2e/kWh (Mix France)
    "Gaz": 0.23,        # kgCO2e/kWh
    "Essence": 2.5,     # kgCO2e/L
    # Monétaire (Rapide - Ratios Spend-based)
    "Services": 0.12,   # kgCO2e/€ (Avocats, Consultants...)
    "Numérique": 0.22,  # kgCO2e/€ (SaaS, Cloud, Hardware lissé)
    "Transport": 0.55,  # kgCO2e/€ (Mixte Avion/Train/Hôtel)
    "Resto": 0.30       # kgCO2e/€ (Traiteur, Repas)
}

# Benchmarks (tCO2e / employé par an)
BENCHMARKS = {
    "Tech / SaaS": 3.5,
    "Consulting / Services": 4.5,
    "Commerce": 6.0,
    "Industrie": 15.0
}

# --- 2. FONCTION PDF ---
def create_pdf(company, kpis, details, actions):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 10, f"Rapport Carbone : {company}", ln=True, align='L')
    pdf.line(10, 25, 200, 25)
    pdf.ln(20)
    
    # KPIs
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"Resultats Clés", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Total Emissions : {kpis['total']:,.1f} tCO2e", ln=True)
    pdf.cell(0, 10, f"Intensite : {kpis['ratio']:,.1f} tCO2e / employe", ln=True)
    pdf.ln(10)
    
    # Détails
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Details par Scope", ln=True)
    pdf.set_font("Arial", '', 11)
    for cat, val in details.items():
        pdf.cell(100, 8, f"{cat}", 1)
        pdf.cell(50, 8, f"{val:,.1f} t", 1, 1, 'R')
    
    # Plan d'action
    if actions:
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(0, 150, 0)
        pdf.cell(0, 10, "Plan de Reduction retenu", ln=True)
        pdf.set_font("Arial", '', 11)
        pdf.set_text_color(0, 0, 0)
        for act in actions:
            pdf.cell(0, 8, f"- {act}", ln=True)

    return pdf.output(dest='S').encode('latin-1')

# --- 3. INTERFACE ---
with st.sidebar:
    st.title("💎 OpenCarbon")
    st.caption("Intelligence Carbone pour Entreprises")
    st.markdown("---")
    company = st.text_input("Société", "Ma Boite")
    secteur = st.selectbox("Secteur d'activité", list(BENCHMARKS.keys()))
    nb_pax = st.number_input("Effectif (ETP)", 1, 10000, 25)
    
    st.markdown("---")
    st.info("ℹ️ Remplissez les données à droite. Pas besoin de factures détaillées, des estimations budgétaires suffisent.")

# TABS
t_input, t_dash, t_simu, t_doc = st.tabs(["📝 Saisie Rapide", "📊 Analyse Expert", "🚀 Simulateur ROI", "📄 Rapport"])

# --- TAB 1 : SAISIE (SIMPLE) ---
with t_input:
    st.subheader("Entrez vos volumes annuels")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏢 Bureaux & Énergie")
        elec = st.number_input("Électricité (kWh)", value=30000, help="Regardez votre facture annuelle ou compteur Linky.")
        gaz = st.number_input("Gaz / Chauffage (kWh)", value=10000)
        surface = st.number_input("Surface Bureaux (m2)", value=250, help="Pour vérifier la cohérence.")

    with col2:
        st.markdown("### 💸 Achats & Déplacements")
        achats = st.number_input("Budget Achats Services/IT (€)", value=150000, help="Total des comptes 60/61/62 (hors RH/Loyer).")
        deplacements = st.number_input("Budget Déplacements (€)", value=40000, help="Train + Avion + Hôtel.")
        flotte = st.number_input("Carburant Flotte Auto (Litres)", value=2000)

    # --- MOTEUR DE CALCUL (INVISIBLE) ---
    co2_elec = elec * FE["Elec"]
    co2_gaz = gaz * FE["Gaz"]
    co2_flotte = flotte * FE["Essence"]
    co2_achats = achats * FE["Services"] # On simplifie en mixant services/numérique
    co2_depl = deplacements * FE["Transport"]

    # Agrégation par Scope (Pour le Waterfall)
    s1 = (co2_gaz + co2_flotte) / 1000
    s2 = (co2_elec) / 1000
    s3 = (co2_achats + co2_depl) / 1000
    total_t = s1 + s2 + s3
    ratio = total_t / nb_pax

# --- TAB 2 : ANALYSE (AVANCÉE) ---
with t_dash:
    # 1. KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bilan Carbone", f"{total_t:,.1f} tCO2e", delta="2025")
    c2.metric("Intensité / Collab", f"{ratio:,.1f} t", delta=f"{ratio - BENCHMARKS[secteur]:.1f} vs Secteur", delta_color="inverse")
    c3.metric("Scope 3 (Indirect)", f"{(s3/total_t)*100:.0f}%", help="C'est souvent la part la plus grosse !")
    c4.metric("Coût Latent", f"{total_t * 90:,.0f} €", help="Si taxe à 90€/tonne")

    st.markdown("---")

    # 2. GRAPHIQUES PROS
    g1, g2 = st.columns([2, 1])
    
    with g1:
        st.subheader("Structure des Émissions (Waterfall)")
        # Le graphique des consultants
        fig_water = go.Figure(go.Waterfall(
            orientation = "v",
            measure = ["relative", "relative", "relative", "total"],
            x = ["Scope 1 (Direct)", "Scope 2 (Énergie)", "Scope 3 (Flux)", "TOTAL"],
            textposition = "outside",
            text = [f"{s1:.1f}", f"{s2:.1f}", f"{s3:.1f}", f"{total_t:.1f}"],
            y = [s1, s2, s3, total_t],
            connector = {"line":{"color":"rgb(63, 63, 63)"}},
        ))
        fig_water.update_layout(title="Comment se construit votre bilan ?", showlegend=False)
        st.plotly_chart(fig_water, use_container_width=True)

    with g2:
        st.subheader("Benchmark")
        # Comparaison visuelle
        bench_val = BENCHMARKS[secteur]
        df_bench = pd.DataFrame({
            "Entité": ["Votre Entreprise", f"Moyenne {secteur}"],
            "Intensité": [ratio, bench_val],
            "Color": ["#2BDD66" if ratio < bench_val else "#FF4B4B", "#DDDDDD"]
        })
        fig_b = px.bar(df_bench, x="Entité", y="Intensité", color="Color", text_auto=".1f", color_discrete_map="identity")
        fig_b.update_layout(showlegend=False)
        st.plotly_chart(fig_b, use_container_width=True)
        
        if ratio > bench_val:
            st.warning("⚠️ Vous êtes au-dessus de la moyenne. Le plan d'action est prioritaire.")
        else:
            st.success("✅ Vous êtes performant (Low Carbon Leader).")

# --- TAB 3 : SIMULATEUR (ACTION) ---
with t_simu:
    st.subheader("🎯 Construisez votre Trajectoire de Réduction")
    col_act, col_res = st.columns([1, 2])
    
    saved = 0
    actions_list = []
    
    with col_act:
        st.markdown("**Energie & Locaux**")
        if st.checkbox("⚡ Passer au 100% Renouvelable (S2)"):
            gain = s2 * 0.95
            saved += gain
            actions_list.append(f"Electricité Verte (-{gain:.1f}t)")
            
        st.markdown("**Mobilité**")
        if st.checkbox("🚆 Politique Train > Avion (S3)"):
            gain = (co2_depl/1000) * 0.30
            saved += gain
            actions_list.append(f"Report Modal Train (-{gain:.1f}t)")
            
        if st.checkbox("🚗 Électrification Flotte (S1)"):
            gain = (co2_flotte/1000) * 0.60
            saved += gain
            actions_list.append(f"Flotte Electrique (-{gain:.1f}t)")
            
        st.markdown("**Achats Responsables**")
        if st.checkbox("💻 Sobriété Numérique & Reconditionné"):
            gain = (co2_achats/1000) * 0.15
            saved += gain
            actions_list.append(f"Sobriété IT (-{gain:.1f}t)")

    with col_res:
        new_total = total_t - saved
        pct = (saved / total_t) * 100
        
        st.metric("Potentiel de Réduction", f"-{saved:,.1f} tCO2e", delta=f"-{pct:.1f}%")
        
        # Jauge
        fig_g = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = new_total,
            delta = {'reference': total_t, 'increasing': {'color': "red"}, 'decreasing': {'color': "green"}},
            title = {'text': "Objectif Trajectoire"},
            gauge = {
                'axis': {'range': [0, total_t]},
                'bar': {'color': "#2BDD66"},
                'steps': [{'range': [0, total_t], 'color': "lightgray"}],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': total_t}
            }
        ))
        st.plotly_chart(fig_g, use_container_width=True)

# --- TAB 4 : EXPORT ---
with t_doc:
    st.header("📄 Votre Rapport Stratégique")
    st.markdown("Téléchargez le document officiel pour vos parties prenantes (Banques, Investisseurs, Clients).")
    
    # Bouton PDF
    pdf_data = create_pdf(company, {'total': total_t, 'ratio': ratio}, {'Scope 1': s1, 'Scope 2': s2, 'Scope 3': s3}, actions_list)
    
    st.download_button("📥 Télécharger Rapport PDF", pdf_data, "Bilan_Carbone_Pro.pdf", "application/pdf")
