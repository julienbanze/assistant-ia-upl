import streamlit as st
import google.generativeai as genai
import sqlite3
import PyPDF2
import pandas as pd
from PIL import Image
from datetime import datetime
import os

# --- CONFIGURATION PAGE ---
st.set_page_config(
    page_title="JBK Expert AI | UPL Edition", 
    layout="wide", 
    page_icon="🎓"
)

# --- GESTION DE LA BASE DE DONNÉES SÉCURISÉE ---
DB_FILE = 'jbk_data.db'

def init_db():
    """Initialise la table si elle n'existe pas."""
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS chat_logs 
                     (timestamp TEXT, role TEXT, content TEXT)''')
        conn.commit()
        conn.close()
    except Exception:
        # On ne bloque pas l'app si la DB échoue sur le cloud
        pass

init_db()

def save_to_db(role, content):
    """Sauvegarde un message sans faire planter l'application."""
    try:
        with sqlite3.connect(DB_FILE, check_same_thread=False) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO chat_logs VALUES (?, ?, ?)", 
                      (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), role, content))
            conn.commit()
    except Exception:
        # Si Streamlit Cloud refuse l'écriture, on ignore silencieusement
        pass

# --- CONFIGURATION API GEMINI ---
# On récupère la clé depuis les Secrets Streamlit
api_key = st.secrets.get("api_key")

if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("🔑 Erreur : Clé API non configurée dans les Secrets Streamlit.")
    st.stop()

# --- BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.markdown(f"""
    <div style='padding: 10px; background: #1e1f20; border-radius: 10px; border: 1px solid #444;'>
        <p style='color: #8ab4f8; margin-bottom: 0;'>Développeur Expert</p>
        <h3 style='margin-top: 0;'>Julien Banze Kandolo</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Zone PDF pour le RAG
    st.subheader("📚 Documents de cours")
    uploaded_pdf = st.file_uploader("Charger un Syllabus (PDF)", type=['pdf'])
    pdf_context = ""
    if uploaded_pdf:
        try:
            reader = PyPDF2.PdfReader(uploaded_pdf)
            pdf_context = " ".join([page.extract_text() for page in reader.pages])
            st.success("✅ Document analysé")
        except Exception as e:
            st.error("Erreur de lecture PDF")

    # Dashboard de monitoring
    with st.expander("📊 Monitoring (Admin)"):
        if os.path.exists(DB_FILE):
            try:
                conn = sqlite3.connect(DB_FILE)
                df = pd.read_sql_query("SELECT * FROM chat_logs ORDER BY timestamp DESC LIMIT 10", conn)
                st.dataframe(df, use_container_width=True)
                conn.close()
            except:
                st.write("Base de données inaccessible.")
        
        if st.button("🗑️ Vider l'historique DB"):
            try:
                conn = sqlite3.connect(DB_FILE)
                conn.cursor().execute("DELETE FROM chat_logs")
                conn.commit()
                conn.close()
                st.rerun()
            except:
                pass

# --- ZONE DE CHAT PRINCIPALE ---
st.title("🎓 Assistant IA Universitaire Pro")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage des messages
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Entrée utilisateur
if prompt := st.chat_input("Posez votre question académique..."):
    # 1. Affichage et sauvegarde utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_to_db("user", prompt)
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Génération de la réponse
    with st.chat_message("assistant"):
        try:
            model =
