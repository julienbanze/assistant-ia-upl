"""
ASSISTANT ACADÉMIQUE IA
Version Professionnelle
Développé par Julien Banze Kandolo
"""

import streamlit as st
from groq import Groq
import logging
from pathlib import Path

# -----------------------
# CONFIG PAGE
# -----------------------

st.set_page_config(
    page_title="Assistant Académique IA 🎓",
    page_icon="🎓",
    layout="wide"
)

# -----------------------
# DESIGN ORIGINAL
# -----------------------

st.markdown("""
<style>

.main {background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #4a69bd 100%) !important}
.stApp {background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #4a69bd 100%) !important}

h1 {
color: #ffd700 !important;
text-align: center;
font-size: 3em;
text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
}

.stChatInput input {
border-radius: 25px !important;
border: 2px solid #ffd700 !important;
padding: 15px !important;
}

</style>
""", unsafe_allow_html=True)

# -----------------------
# LOGS
# -----------------------

Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
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
        st.error("Ajoutez GROQ_API_KEY dans Settings > Secrets")
        st.stop()

client = init_client()

# -----------------------
# PROMPT IA
# -----------------------

SYSTEM_PROMPT = """
Tu es un assistant académique très intelligent.

Réponds toujours en français.

Structure ta réponse :

1. Titre
2. Introduction
3. Explication claire
4. Conclusion

Explique comme un professeur.
"""

# -----------------------
# MEMOIRE
# -----------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------
# HEADER
# -----------------------

st.markdown("## 🎓 Assistant Académique IA")
st.markdown("Posez vos questions académiques ou utilisez le micro.")

# -----------------------
# HISTORIQUE CHAT
# -----------------------

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------
# QUESTION VOCALE
# -----------------------

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

# -----------------------
# REPONSE IA
# -----------------------

if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":

    with st.chat_message("assistant"):

        placeholder = st.empty()
        full_response = ""

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        for msg in st.session_state.messages:
            if msg["content"].strip() != "":
                messages.append(msg)

        try:

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

        except Exception as e:

            st.error("Erreur IA. Vérifiez votre clé API ou le modèle.")
            st.write(e)

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response
    })

# -----------------------
# FOOTER
# -----------------------

st.markdown("---")

st.markdown("""
Développé par **Julien Banze Kandolo**  
Assistant Académique IA
""")
