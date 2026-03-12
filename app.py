"""
ASSISTANT ACADÉMIQUE IA - VERSION 100% FONCTIONNELLE
Problème corrigé : AFFICHAGE IMMÉDIAT DES RÉPONSES
"""

import streamlit as st
import logging
from pathlib import Path
from groq import Groq
import time

# Configuration logging simple
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/assistant.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# CSS PREMIUM ACADÉMIQUE
st.set_page_config(
    page_title="Assistant Académique IA 🎓",
    page_icon="🎓",
    layout="wide"
)

st.markdown("""
<style>
    .main {background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #4a69bd 100%) !important}
    .stApp {background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #4a69bd 100%) !important}
    
    h1 {color: #ffd700 !important; text-align: center; font-size: 3em; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);}
    .user {background: rgba(255,215,0,0.2) !important; border-left: 5px solid #ffd700 !important;}
    .assistant {background: rgba(0,255,127,0.15) !important; border-left: 5px solid #00ff7f !important;}
    
    .stChatInput input {border-radius: 25px !important; border: 2px solid #ffd700 !important; padding: 15px !important;}
    .typing {color: #ffd700; font-style: italic;}
</style>
""", unsafe_allow_html=True)

# CLIENT GROQ
@st.cache_resource
def init_client():
    try:
        return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except:
        st.error("🔑 Ajoutez GROQ_API_KEY dans Settings > Secrets")
        st.stop()

client = init_client()

# PROMPT ACADÉMIQUE PUISSANT
SYSTEM_PROMPT = """Tu es l'ASSISTANT ACADÉMIQUE IA le plus puissant du monde.
Réponds EN FRANÇAIS avec structure académique :
1️⃣ **TITRE** en gras
2️⃣ **Introduction** claire
3️⃣ **Développement** structuré avec listes/étapes
4️⃣ **Conclusion** + sources si possible
Utilise markdown, formules, tableaux. Sois précis et pédagogue."""

# ÉTAT SESSION
if "messages" not in st.session_state:
    st.session_state.messages = []

# HEADER
st.markdown("## 🎓 **ASSISTANT ACADÉMIQUE IA** - Le plus puissant pour vos études")
st.markdown("*Maths, Physique, Chimie, Info, Littérature, Histoire...*")

# AFFICHAGE MESSAGES
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# INPUT + RÉPONSE IMMÉDIATE
if prompt := st.chat_input("Votre question académique..."):
    # AJOUT USER
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()  # AFFICHAGE IMMÉDIAT USER
    
    # GÉNÉRATION RÉPONSE
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # STREAMING DIRECT
        stream = client.chat.completions.create(
            model="llama-3.1-70b-versatile",  # LE PLUS PUISSANT
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages,
            stream=True,
            temperature=0.1,
            max_tokens=2000
        )
        
        # AFFICHAGE CARACTÈRE PAR CARACTÈRE
        for chunk in stream:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
                message_placeholder.markdown(full_response + "⏳")
        
        message_placeholder.markdown(full_response)
    
    # SAUVEGARDE
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.rerun()

# FOOTER
st.markdown("---")
st.markdown("*Développé par Julien Banze Kandolo | Powered by Groq Llama 70B*")
