import streamlit as st
import google.generativeai as genai
import sqlite3
import PyPDF2
from PIL import Image
from datetime import datetime

# --- CONFIGURATION INITIALE ---
st.set_page_config(
    page_title="Expert AI OS | Julien Banze Kandolo",
    page_icon="🧠",
    layout="wide"
)

# --- INITIALISATION BASE DE DONNÉES (SQLITE) ---
def init_db():
    conn = sqlite3.connect('jbk_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS chat_logs 
                 (timestamp TEXT, role TEXT, content TEXT)''')
    conn.commit()
    return conn

def save_to_db(role, content):
    conn = sqlite3.connect('jbk_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO chat_logs VALUES (?, ?, ?)", 
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), role, content))
    conn.commit()
    conn.close()

# --- CONFIGURATION API ---
api_key = st.secrets.get("api_key") or st.secrets.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("Clé API manquante dans les Secrets Streamlit.")
    st.stop()

# --- FONCTIONS EXPERTES ---
def extract_pdf_text(file):
    pdf_reader = PyPDF2.PdfReader(file)
    return " ".join([page.extract_text() for page in pdf_reader.pages])

# --- INTERFACE SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Panneau de Contrôle")
    st.info(f"Développeur : Julien Banze Kandolo")
    
    # Zone d'upload pour le RAG (Analyse de documents)
    st.subheader("📁 Documents Académiques")
    doc_file = st.file_uploader("Charger un syllabus ou cours (PDF)", type=['pdf'])
    doc_context = ""
    if doc_file:
        doc_context = extract_pdf_text(doc_file)
        st.success("Document analysé et prêt.")

    if st.button("🗑️ Réinitialiser la Session"):
        st.session_state.messages = []
        st.rerun()

# --- ZONE DE CHAT PRINCIPALE ---
st.header("🎓 Assistant Expert JBK Edition")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage de l'historique
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Logique de réponse
if prompt := st.chat_input("Posez votre question d'expert..."):
    # 1. Gérer l'entrée utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_to_db("user", prompt)
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Générer la réponse avec Contexte (si PDF présent)
    with st.chat_message("assistant"):
        try:
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            # Construction du prompt intelligent
            final_prompt = prompt
            if doc_context:
                final_prompt = f"CONTEXTE DOCUMENTAIRE: {doc_context[:5000]}\n\nQUESTION: {prompt}\n\nRéponds en tant qu'expert UPL."

            response = model.generate_content(final_prompt)
            full_response = response.text
            
            st.markdown(full_response)
            
            # 3. Sauvegarder la réponse
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            save_to_db("assistant", full_response)
            
        except Exception as e:
            st.error(f"Erreur : {e}")

st.markdown("---")
st.caption("Julien banze kandolo- Lubumbashi 2026")
