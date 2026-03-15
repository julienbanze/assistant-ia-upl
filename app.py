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
# GROQ CLIENT
# -----------------------
@st.cache_resource
def init_groq_client():
    try:
        # ⚠️ Mets ta clé Groq ici ou via secrets pour ne pas exposer
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
# SPECIAL RESPONSE SI ON PARLE DE JULIEN BANZE KANDOLO
# -----------------------
special_names = ["julien banze kandolo"]

# Question texte
prompt = st.chat_input("Posez votre question académique...")

if prompt:
    # Affiche la question utilisateur
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role":"user","content":prompt})

    # Vérifie si l’utilisateur mentionne ton nom complet
    if any(name in prompt.lower() for name in special_names):
        st.chat_message("assistant").markdown(
            "👋 Bonjour ! Vous parlez de **Julien Banze Kandolo**, le créateur de cette application. "
            "Il est passionné par l'intelligence artificielle et a conçu cet assistant académique pour vous aider."
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
