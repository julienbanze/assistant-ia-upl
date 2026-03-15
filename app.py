import streamlit as st
from groq import Groq
import logging
from pathlib import Path
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
h1{ color:#ffd700; text-align:center; font-size:2.8em; }
.stChatInput input{ border-radius:25px; border:2px solid #ffd700; padding:12px; }
</style>
""", unsafe_allow_html=True)

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
# SECRETS STREAMLIT
# -----------------------

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# -----------------------
# GROQ CLIENT
# -----------------------

@st.cache_resource
def init_groq():
    try:
        return Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        st.error(f"Erreur Groq : {e}")
        st.stop()

client = init_groq()

# -----------------------
# SUPABASE CLIENT
# -----------------------

@st.cache_resource
def init_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Erreur Supabase : {e}")
        st.stop()

supabase: Client = init_supabase()

# -----------------------
# PROMPT IA
# -----------------------

SYSTEM_PROMPT = """
Tu es un assistant académique intelligent.
Réponds toujours en français.
Structure ta réponse :
Titre
Introduction
Explication claire
Conclusion
"""

# -----------------------
# MEMOIRE CHAT
# -----------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------
# HEADER
# -----------------------

st.markdown("## 🎓 Assistant Académique IA")
st.write("Posez vos questions académiques ou utilisez le micro.")

# -----------------------
# HISTORIQUE
# -----------------------

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------
# QUESTION VOCALE
# -----------------------

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
            st.session_state.messages.append({
                "role": "user",
                "content": voice_prompt
            })
            # Sauvegarde dans Supabase
            supabase.table("messages").insert({
                "user_id": "user_anonyme",
                "question": voice_prompt,
                "date": "now()"
            }).execute()
    except Exception:
        st.warning("Erreur lors de la transcription vocale")

# -----------------------
# QUESTION TEXTE
# -----------------------

prompt = st.chat_input("Posez votre question académique...")

if prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })
    st.chat_message("user").markdown(prompt)
    # Sauvegarde dans Supabase
    supabase.table("messages").insert({
        "user_id": "user_anonyme",
        "question": prompt,
        "date": "now()"
    }).execute()

# -----------------------
# REPONSE IA
# -----------------------

if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        messages = [{"role":"system","content":SYSTEM_PROMPT}] + st.session_state.messages
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
        "role":"assistant",
        "content":full_response
    })

# -----------------------
# FOOTER
# -----------------------

st.markdown("---")
st.markdown("Développé par **Julien Banze Kandolo**")
