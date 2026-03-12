"""
ASSISTANT IA ACADÉMIQUE
Développé par Julien Banze Kandolo
Version internationale (interface en français)
"""

import streamlit as st
from groq import Groq
import logging
from pathlib import Path

# -----------------------------
# CONFIGURATION PAGE
# -----------------------------

st.set_page_config(
    page_title="Assistant Académique IA",
    page_icon="🎓",
    layout="wide"
)

# -----------------------------
# DESIGN
# -----------------------------

st.markdown("""
<style>

.stApp{
background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
color:white;
}

h1{
text-align:center;
color:#FFD700;
}

.stChatInput input{
border-radius:30px;
padding:15px;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# LOGS
# -----------------------------

Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

# -----------------------------
# INITIALISATION GROQ
# -----------------------------

@st.cache_resource
def init_client():
    try:
        return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except:
        st.error("Ajoutez GROQ_API_KEY dans les secrets Streamlit")
        st.stop()

client = init_client()

# -----------------------------
# PROMPT SYSTEME
# -----------------------------

SYSTEM_PROMPT = """
Tu es un assistant académique très intelligent.

Règles :
- Réponds toujours en français
- Explique clairement comme un professeur
- Utilise une structure académique

Structure de réponse :
Titre
Introduction
Explication détaillée
Conclusion

Sois pédagogique et précis.
"""

# -----------------------------
# MEMOIRE SESSION
# -----------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------------
# EN-TETE
# -----------------------------

st.title("🎓 Assistant Académique IA")
st.write("Posez vos questions académiques ou utilisez le micro.")

# -----------------------------
# AFFICHAGE CHAT
# -----------------------------

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------------
# QUESTION VOCALE
# -----------------------------

audio = st.audio_input("🎤 Posez votre question avec votre voix")

if audio is not None:

    with st.spinner("Transcription de la voix..."):

        transcription = client.audio.transcriptions.create(
            file=("audio.wav", audio.getvalue()),
            model="whisper-large-v3"
        )

        voice_prompt = transcription.text.strip()

        if voice_prompt != "":
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
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    st.chat_message("user").markdown(prompt)

# -----------------------------
# REPONSE IA
# -----------------------------

if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":

    with st.chat_message("assistant"):

        placeholder = st.empty()
        full_response = ""

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        for msg in st.session_state.messages:
            if msg["content"].strip() != "":
                messages.append(msg)

        stream = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
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

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response
    })

# -----------------------------
# FOOTER
# -----------------------------

st.markdown("---")

st.markdown("""
Assistant Académique IA  

Développé par **Julien Banze Kandolo**  
Propulsé par Groq IA
""")
