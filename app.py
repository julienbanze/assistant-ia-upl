import streamlit as st
from groq import Groq
import logging
from pathlib import Path
import bcrypt
import mysql.connector
from mysql.connector import Error
from io import BytesIO

# -----------------------------
# CONFIG PAGE
# -----------------------------
st.set_page_config(
    page_title="Assistant Académique IA 🎓",
    page_icon="🎓",
    layout="wide"
)

# -----------------------------
# DESIGN
# -----------------------------
st.markdown("""
<style>
.main {background: linear-gradient(135deg,#1e3c72,#2a5298,#4a69bd)}
.stApp {background: linear-gradient(135deg,#1e3c72,#2a5298,#4a69bd)}
h1 {color:#ffd700; text-align:center; font-size:2.8em;}
.stChatInput input {border-radius:25px; border:2px solid #ffd700; padding:12px;}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# LOGS
# -----------------------------
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()]
)

# -----------------------------
# GROQ CLIENT
# -----------------------------
@st.cache_resource
def init_client():
    try:
        return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except:
        st.error("🔑 Ajoutez GROQ_API_KEY dans Settings > Secrets")
        st.stop()

client = init_client()

# -----------------------------
# SYSTEM PROMPT
# -----------------------------
SYSTEM_PROMPT = """
Tu es un assistant académique intelligent.
Réponds toujours en français.
Structure tes réponses : Titre, Introduction, Explication claire, Conclusion.
"""

# -----------------------------
# BASE DE DONNÉES MYSQL
# -----------------------------
def connect_db():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # mettre le mot de passe MySQL
            database="assistant_ia"
        )
    except Error as e:
        st.error(f"Erreur DB : {e}")
        st.stop()

def create_user(email, password):
    db = connect_db()
    cursor = db.cursor()
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    cursor.execute("INSERT INTO users (email, password) VALUES (%s,%s)", (email, hashed))
    db.commit()
    cursor.close()
    db.close()

def check_user(email, password):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT password FROM users WHERE email=%s", (email,))
    row = cursor.fetchone()
    cursor.close()
    db.close()
    if row and bcrypt.checkpw(password.encode(), row[0].encode()):
        return True
    return False

def save_chat_to_db(user_email, question, answer):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO chats (user_email, question, answer) VALUES (%s,%s,%s)",
        (user_email, question, answer)
    )
    db.commit()
    cursor.close()
    db.close()

# -----------------------------
# MEMOIRE
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_email" not in st.session_state:
    st.session_state.user_email = None

# -----------------------------
# FORMULAIRE INSCRIPTION / CONNEXION
# -----------------------------
st.header("📌 Connexion / Inscription")

with st.expander("Inscription"):
    email_reg = st.text_input("Email", key="inscription_email")
    password_reg = st.text_input("Mot de passe", type="password", key="inscription_password")
    if st.button("S'inscrire", key="btn_inscrire"):
        if email_reg and password_reg:
            create_user(email_reg, password_reg)
            st.success("✅ Compte créé ! Vous pouvez maintenant vous connecter.")

with st.expander("Connexion"):
    email_conn = st.text_input("Email", key="connexion_email")
    password_conn = st.text_input("Mot de passe", type="password", key="connexion_password")
    if st.button("Se connecter", key="btn_connexion"):
        if check_user(email_conn, password_conn):
            st.session_state.user_email = email_conn
            st.success(f"✅ Connecté en tant que {email_conn}")
        else:
            st.error("❌ Email ou mot de passe incorrect")

if not st.session_state.user_email:
    st.info("Veuillez vous connecter pour poser vos questions.")
    st.stop()

# -----------------------------
# HEADER
# -----------------------------
st.markdown(f"## 🎓 Assistant Académique IA - Utilisateur : {st.session_state.user_email}")
st.write("Posez vos questions académiques par texte ou par voix.")

# -----------------------------
# HISTORIQUE
# -----------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------------
# AUDIO INPUT
# -----------------------------
audio = st.audio_input("🎤 Posez votre question avec votre voix")
if audio is not None:
    try:
        transcription = client.audio.transcriptions.create(
            file=("audio.wav", audio.getvalue()),
            model="whisper-large-v3"
        )
        voice_prompt = transcription.text.strip()
        if voice_prompt:
            st.chat_message("user").markdown(voice_prompt)
            st.session_state.messages.append({"role":"user","content":voice_prompt})
    except Exception:
        st.warning("Erreur lors de la transcription vocale")

# -----------------------------
# TEXTE INPUT
# -----------------------------
prompt = st.chat_input("Posez votre question académique...")
if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role":"user","content":prompt})

# -----------------------------
# GENERATION IA
# -----------------------------
if st.session_state.messages and st.session_state.messages[-1]["role"]=="user":
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        messages = [{"role":"system","content":SYSTEM_PROMPT}]
        for msg in st.session_state.messages:
            # Détection de Julien Banze Kandolo
            if "julien banze kandolo" in msg["content"].lower():
                full_response = "💡 Vous avez mentionné le créateur du projet ! Julien Banze Kandolo est passionné d'IA et développe ce projet pour l'éducation."
                placeholder.markdown(full_response)
                break
            messages.append(msg)
        if not full_response:
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

        # Sauvegarde dans la DB
        if full_response and st.session_state.user_email:
            last_question = st.session_state.messages[-1]["content"]
            save_chat_to_db(st.session_state.user_email, last_question, full_response)

        st.session_state.messages.append({"role":"assistant","content":full_response})

# -----------------------------
# FOOTER
# -----------------------------
st.divider()
st.markdown("Développé par **Julien Banze Kandolo**")
