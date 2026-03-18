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
        st.error("Ajoutez GROQ_API_KEY dans Settings > Secrets")
        st.stop()

client = init_client()

# -----------------------
# PROMPT IA
# -----------------------

SYSTEM_PROMPT = """
Tu es un assistant académique intelligent.

Réponds toujours en français.

et si un utilisateur pose une question qui n'est pas académique, réponds poliment que tu ne peux répondre qu'à des questions académiques et educative.
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

# -----------------------
# REPONSE IA
# -----------------------

if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":

    with st.chat_message("assistant"):

        placeholder = st.empty()
        full_response = ""

        messages = [{"role":"system","content":SYSTEM_PROMPT}]

        for msg in st.session_state.messages:
            messages.append(msg)

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

