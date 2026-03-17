import streamlit as st
from groq import Groq
import logging
from pathlib import Path
import re
from supabase import create_client, Client

# -----------------------
# CONFIG PAGE
# -----------------------
st.set_page_config(
    page_title="Assistant Académique IA 🎓",
    page_icon="🎓",
    layout="wide"
)

# -----------------------
# DESIGN
# -----------------------
st.markdown("""
<style>
.main {background: linear-gradient(135deg,#1e3c72,#2a5298,#4a69bd)}
.stApp {background: linear-gradient(135deg,#1e3c72,#2a5298,#4a69bd)}

h1{
color:#ffd700;
text-align:center;
font-size:2.8em;
}

.stChatInput input{
border-radius:25px;
border:2px solid #ffd700;
padding:12px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------
# SUPABASE CONFIG
# -----------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------
# FONCTIONS
# -----------------------
def verifier_matricule(matricule):
    return re.match(r"^20\d{8}$", matricule)

def user_existe(matricule):
    response = supabase.table("users").select("*").eq("matricule", matricule).execute()
    return len(response.data) > 0

def ajouter_user(nom, email, matricule):
    supabase.table("users").insert({
        "nom": nom,
        "email": email,
        "matricule": matricule
    }).execute()

# -----------------------
# SESSION
# -----------------------
if "connecte" not in st.session_state:
    st.session_state.connecte = False

if "admin" not in st.session_state:
    st.session_state.admin = False

if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------
# INSCRIPTION
# -----------------------
st.markdown("## 🎓 Assistant Académique IA")

if not st.session_state.connecte:

    st.subheader("🔐 Inscription Étudiant")

    nom = st.text_input("Nom complet")
    email = st.text_input("Gmail")
    matricule = st.text_input("Numéro matricule")

    if st.button("Valider"):

        if not verifier_matricule(matricule):
            st.error("Matricule invalide ❌ (ex: 2025023061)")

        else:
            try:
                if user_existe(matricule):
                    st.success("Bienvenue 👋")
                    st.session_state.connecte = True
                else:
                    ajouter_user(nom, email, matricule)
                    st.success("Inscription réussie 🎉")
                    st.session_state.connecte = True
            except:
                st.error("Erreur connexion base de données")

    st.stop()

# -----------------------
# SIDEBAR
# -----------------------
with st.sidebar:

    st.title("Menu")

    if st.button("Se déconnecter"):
        st.session_state.connecte = False
        st.rerun()

    st.markdown("---")

    code_admin = st.text_input("Code Admin", type="password")

    if code_admin == "ADMIN123":
        st.session_state.admin = True

# -----------------------
# ADMIN PANEL
# -----------------------
if st.session_state.admin:
    st.subheader("📊 Liste des étudiants inscrits")
    response = supabase.table("users").select("nom,email,matricule").execute()
    st.table(response.data)

# -----------------------
# LOGS
# -----------------------
Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

# -----------------------
# GROQ CLIENT
# -----------------------
@st.cache_resource
def init_client():
    try:
        return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except:
        st.error("Ajoutez GROQ_API_KEY dans Secrets")
        st.stop()

client = init_client()

# -----------------------
# PROMPT IA
# -----------------------
SYSTEM_PROMPT = """
Tu es un assistant académique intelligent.

Réponds toujours en français.

Structure :
Titre
Introduction
Explication
Conclusion
"""

# -----------------------
# HEADER
# -----------------------
st.write("Posez vos questions académiques ou utilisez le micro.")

# -----------------------
# HISTORIQUE
# -----------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------
# AUDIO
# -----------------------
audio = st.audio_input("🎤 Posez votre question avec votre voix")

if audio is not None:
    try:
        transcription = client.audio.transcriptions.create(
            file=("audio.wav", audio.getvalue()),
            model="whisper-large-v3"
        )
        text = transcription.text.strip()
        if text:
            st.chat_message("user").markdown(text)
            st.session_state.messages.append({"role": "user", "content": text})
    except:
        st.warning("Erreur transcription")

# -----------------------
# TEXTE
# -----------------------
prompt = st.chat_input("Posez votre question académique...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)

# -----------------------
# REPONSE IA
# -----------------------
if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":

    with st.chat_message("assistant"):

        placeholder = st.empty()
        full_response = ""

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += st.session_state.messages

        try:
            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                stream=True,
                temperature=0.2,
                max_tokens=1500
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    placeholder.markdown(full_response + "▌")

            placeholder.markdown(full_response)

        except Exception as e:
            st.error(f"Erreur IA : {e}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response
    })

# -----------------------
# FOOTER
# -----------------------
st.markdown("---")
st.markdown("Développé par **Julien Banze Kandolo**")
