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
MAINTENANCE_MODE = False  # <- Mettre à True si tu modifies l'app
if MAINTENANCE_MODE:
    st.warning("⚠️ L'application est actuellement en cours de modification par le développeur Julien Banze. Merci de revenir plus tard.")
    st.stop()

# -----------------------
# GROQ CLIENT
# -----------------------
@st.cache_resource
def init_groq_client():
    try:
        # 🔒 Clé sécurisée via Streamlit Secrets
        return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except:
        st.error("Erreur : ajoute ta clé Groq dans Secrets")
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
# SPECIAL RESPONSE POUR LE CREATEUR
# -----------------------
creator_names = ["julien", "banze", "kandolo"]  # n'importe quelle partie du nom
def check_creator(prompt_text):
    prompt_text = prompt_text.lower()
    return any(name in prompt_text for name in creator_names)

# -----------------------
# QUESTION TEXTE
# -----------------------
prompt = st.chat_input("Posez votre question académique...")

if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role":"user","content":prompt})

    # Vérifie si l'utilisateur mentionne le créateur
    if check_creator(prompt):
        st.chat_message("assistant").markdown(
            "👋 Bonjour ! Vous parlez du créateur de cette application, **Julien Banze Kandolo**. "
            "Il est passionné par l'intelligence artificielle et a conçu cet assistant académique pour vous aider de manière professionnelle."
        )

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
