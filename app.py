# app.py
import streamlit as st
from groq import Groq
import logging
from pathlib import Path
from PIL import Image
import pandas as pd
import PyPDF2
import mysql.connector

# -----------------------------
# CONFIGURATION PAGE
# -----------------------------
st.set_page_config(
    page_title="Assistant Académique IA",
    page_icon="🎓",
    layout="wide"
)

# -----------------------------
# DESIGN PROFESSIONNEL
# -----------------------------
st.markdown("""
<style>
.stApp{
background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
color:white;
}

h1{
color:#FFD700;
text-align:center;
}

.stChatInput input{
border-radius:25px;
border:2px solid gold;
padding:12px;
}

.sidebar .sidebar-content{
background:#111;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# LOGS
# -----------------------------
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

# -----------------------------
# GROQ CLIENT
# -----------------------------
@st.cache_resource
def init_client():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])

client = init_client()

# -----------------------------
# BASE DE DONNÉES XAMPP / MYSQL
# -----------------------------
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",        # utilisateur XAMPP
        password="",        # mot de passe XAMPP par défaut
        database="assistant_ia"
    )

def save_chat_to_db(user_question, ai_response):
    db = connect_db()
    cursor = db.cursor()
    sql = "INSERT INTO chat_history (user_question, ai_response) VALUES (%s, %s)"
    cursor.execute(sql, (user_question, ai_response))
    db.commit()
    cursor.close()
    db.close()

# -----------------------------
# FILTRAGE AUTOMATIQUE DES QUESTIONS
# -----------------------------
def is_question_valid(question):
    bad_words = ["insulte", "mauvais", "polémique"]  # mots interdits
    forbidden_subjects = ["Julien Banze Kandolo"]     # sujets sensibles
    question_lower = question.lower()
    
    if any(word in question_lower for word in bad_words):
        return False, "⚠️ Question refusée : merci de poser une question académique appropriée."
    
    if any(subject.lower() in question_lower for subject in forbidden_subjects):
        return False, "⚠️ Cette question concerne le créateur de l'IA. Merci de poser une question académique."
    
    return True, ""

# -----------------------------
# PROMPT SYSTÈME
# -----------------------------
SYSTEM_PROMPT = """
Tu es un assistant académique expert.
Tu aides les étudiants dans :
informatique
mathématiques
électronique
intelligence artificielle
programmation
Réponds toujours en français.
Structure tes réponses :
Titre
Explication claire
Exemple
Conclusion
"""

# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:
    st.title("🎓 Assistant IA")
    st.markdown("Développé par **Julien Banze Kandolo**")
    st.divider()
    
    if st.button("Nouvelle conversation"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    uploaded_pdf = st.file_uploader(
        "📄 Charger un PDF de cours",
        type="pdf"
    )

# -----------------------------
# EXTRACTION PDF
# -----------------------------
pdf_text = ""
if uploaded_pdf:
    reader = PyPDF2.PdfReader(uploaded_pdf)
    for page in reader.pages:
        pdf_text += page.extract_text()
    st.success("PDF chargé avec succès")

# -----------------------------
# MÉMOIRE SESSION
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------------
# TITRE
# -----------------------------
st.title("🎓 Assistant Académique IA")
st.write("Posez vos questions académiques par texte ou par voix.")

# -----------------------------
# HISTORIQUE CHAT
# -----------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------------
# QUESTION VOCALE
# -----------------------------
audio = st.audio_input("🎤 Posez votre question avec votre voix")
if audio is not None:
    transcription = client.audio.transcriptions.create(
        file=("audio.wav", audio.getvalue()),
        model="whisper-large-v3"
    )
    voice_prompt = transcription.text
    st.chat_message("user").markdown(voice_prompt)
    st.session_state.messages.append({
        "role": "user",
        "content": voice_prompt
    })

# -----------------------------
# QUESTION TEXTE
# -----------------------------
prompt = st.chat_input("Posez votre question académique...")
if prompt:
    valid, message = is_question_valid(prompt)
    if not valid:
        st.chat_message("assistant").markdown(message)
    else:
        st.session_state.messages.append({"role":"user","content":prompt})
        st.chat_message("user").markdown(prompt)

# -----------------------------
# GENERATION IA
# -----------------------------
if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
    last_question = st.session_state.messages[-1]["content"]
    
    valid, message = is_question_valid(last_question)
    if valid:
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            
            messages = [{"role":"system","content":SYSTEM_PROMPT}]
            if pdf_text != "":
                messages.append({
                    "role":"system",
                    "content":"Voici un cours PDF fourni par l'utilisateur :" + pdf_text[:4000]
                })
            for m in st.session_state.messages:
                messages.append(m)

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
            
            # Réponse vocale
            st.markdown(f"""
            <script>
            var text = `{full_response}`;
            var speech = new SpeechSynthesisUtterance(text);
            speech.lang = "fr-FR";
            speech.rate = 1;
            speech.pitch = 1;
            window.speechSynthesis.speak(speech);
            </script>
            """, unsafe_allow_html=True)

            # Sauvegarde dans DB
            save_chat_to_db(last_question, full_response)
            
            # Sauvegarde session
            st.session_state.messages.append({"role":"assistant","content":full_response})

# -----------------------------
# FOOTER
# -----------------------------
st.divider()
st.markdown("Assistant académique intelligent développé par **Julien Banze Kandolo**")
