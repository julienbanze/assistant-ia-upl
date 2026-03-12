"""
ASSISTANT IA ACADÉMIQUE INTERNATIONAL
Développé par Julien Banze Kandolo
Version : Pro
Fonctions :
- Chat IA
- Question vocale
- Multi-langue
- Design moderne
"""

import streamlit as st
from groq import Groq
import logging
from pathlib import Path

# =============================
# CONFIGURATION PAGE
# =============================

st.set_page_config(
    page_title="AI Academic Assistant",
    page_icon="🎓",
    layout="wide"
)

# =============================
# DESIGN PROFESSIONNEL
# =============================

st.markdown("""
<style>

.stApp{
background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
color:white;
}

h1{
text-align:center;
color:#FFD700;
font-size:40px;
}

.chat-user{
background:#FFD70020;
padding:10px;
border-radius:10px;
}

.chat-ai{
background:#00ff7f20;
padding:10px;
border-radius:10px;
}

.stChatInput input{
border-radius:30px;
padding:15px;
}

</style>
""", unsafe_allow_html=True)

# =============================
# LOGGING
# =============================

Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

# =============================
# INITIALISATION GROQ
# =============================

@st.cache_resource
def init_client():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])

client = init_client()

# =============================
# PROMPT IA MULTILINGUE
# =============================

SYSTEM_PROMPT = """
You are an international academic AI assistant.

Rules:
- Detect automatically the language of the user
- Answer in the same language
- Provide structured academic responses
- Use:
Title
Introduction
Explanation
Conclusion

Be clear, professional and educational.
"""

# =============================
# MEMOIRE CHAT
# =============================

if "messages" not in st.session_state:
    st.session_state.messages = []

# =============================
# HEADER
# =============================

st.title("🎓 AI Academic Assistant")
st.write("Ask questions in **any language** or use **voice input**.")

# =============================
# AFFICHAGE CHAT
# =============================

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# =============================
# INPUT VOCAL
# =============================

audio = st.audio_input("🎤 Ask your question with voice")

if audio:

    with st.spinner("Transcribing voice..."):

        transcription = client.audio.transcriptions.create(
            file=("audio.wav", audio),
            model="whisper-large-v3"
        )

        voice_prompt = transcription.text

        st.chat_message("user").markdown(voice_prompt)

        st.session_state.messages.append({
            "role":"user",
            "content":voice_prompt
        })

# =============================
# INPUT TEXTE
# =============================

prompt = st.chat_input("Ask your academic question...")

if prompt:
    st.session_state.messages.append({"role":"user","content":prompt})
    st.chat_message("user").markdown(prompt)

# =============================
# GENERATION REPONSE IA
# =============================

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":

    with st.chat_message("assistant"):

        placeholder = st.empty()
        full_response = ""

        stream = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role":"system","content":SYSTEM_PROMPT}]
            + st.session_state.messages,
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
        "role":"assistant",
        "content":full_response
    })

# =============================
# FOOTER
# =============================

st.markdown("---")

st.markdown(
"""
🌍 **AI Academic Assistant**

Developed by **Julien Banze Kandolo**  
Powered by Groq AI
"""
)
