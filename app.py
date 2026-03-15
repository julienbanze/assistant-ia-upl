import streamlit as st
from groq import Groq
import logging
from pathlib import Path

# -----------------------
# CONFIGURATION PAGE
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
    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()]
)

# -----------------------
# MAINTENANCE / MODIFICATION
# -----------------------
MAINTENANCE_MODE = False  # <- True si tu modifies l'app
if MAINTENANCE_MODE:
    st.markdown(
        "⚠️ **L'application est actuellement en cours de maintenance par le développeur Julien Banze. "
        "Veuillez réessayer plus tard.**",
        unsafe_allow_html=True
    )
    st.stop()  # bloque le reste de l'application

# -----------------------
# GROQ CLIENT
# -----------------------
@st.cache_resource
def init_groq_client():
    try:
        return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except:
        st.error("Erreur : ajoute ta clé Groq dans Secrets Streamlit")
        st.stop()

groq_client = init_groq_client()

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
# DETECTION CREATEUR
# -----------------------
creator_keywords = ["julien", "banze", "kandolo"]
creator_questions = ["qui est ton createur", "ton createur", "qui t'a fait", "qui t'a developpe", "developpeur"]

def is_creator_mentioned(text):
    text = text.lower()
    # vérifie nom ou question sur créateur
    return any(word in text for word in creator_keywords) or any(q in text for q in creator_questions)

creator_message = (
    "👋 Bonjour ! Vous parlez du créateur de cette application, **Julien Banze Kandolo**. "
    "Il est passionné par l'intelligence artificielle et a conçu cet assistant académique pour vous aider de manière professionnelle."
)

# -----------------------
# QUESTION TEXTE
# -----------------------
prompt = st.chat_input("Posez votre question académique...")

if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role":"user","content":prompt})

    # Si on mentionne le créateur ou pose une question sur lui
    if is_creator_mentioned(prompt):
        st.chat_message("assistant").markdown(creator_message)

    # -----------------------
    # REPONSE IA
    # -----------------------
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        messages = [{"role":"system","content":SYSTEM_PROMPT}]
        for msg in st.session_state.messages:
            messages.append(msg)

        try:
            stream = groq_client.chat.completions.create(
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

        st.session_state.messages.append({"role":"assistant","content":full_response})

# -----------------------
# FOOTER
# -----------------------
st.markdown("---")
st.markdown("Développé par **Julien Banze Kandolo**")
