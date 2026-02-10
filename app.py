

import streamlit as st
try:
    from groq import Groq
except ImportError:
    st.error("Le module 'groq' est manquant. Vérifiez votre fichier requirements.txt.")
    st.stop()
from PIL import Image

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Assistant Académique | Julien Banze Kandolo",
    page_icon="✨", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLE CSS AVANCÉ (EXPÉRIENCE GEMINI) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500&display=swap');
    
    /* Global Background & Font */
    html, body, [data-testid="stapp"], [data-testid="stHeader"] { 
        font-family: 'Google Sans', sans-serif;
        background-color: #131314 !important;
        color: #e3e3e3;
    }
    
    /* Masquer les éléments Streamlit natifs */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Sidebar Style */
    [data-testid="stSidebar"] { 
        background-color: #1e1f20 !important; 
        border-right: none;
        padding-top: 2rem;
    }
    
    /* Branding Card */
    .jbk-branding {
        padding: 24px;
        background: linear-gradient(145deg, #2b2c2e, #1e1f20);
        border-radius: 20px;
        border: 1px solid #333537;
        margin-bottom: 2rem;
    }
    .jbk-role { font-size: 0.75rem; color: #8ab4f8; text-transform: uppercase; letter-spacing: 2px; font-weight: 500; margin: 0; }
    .jbk-name { font-size: 1.2rem; font-weight: 500; color: #ffffff; margin-top: 5px; margin-bottom: 0; }

    /* Bouton Nouveau Chat (Gemini Style) */
    .stButton>button {
        background-color: #1a1b1c;
        color: #e3e3e3;
        border: 1px solid #444746;
        border-radius: 50px;
        padding: 12px 24px;
        font-size: 0.95rem;
        width: 100%;
        text-align: left;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background-color: #333537;
        border-color: #8ab4f8;
        color: #8ab4f8;
    }

    /* BARRE DE SAISIE FLOTTANTE */
    .stChatInputContainer {
        padding: 0 12% 3rem 12% !important;
        background-color: transparent !important;
    }
    .stChatInputContainer > div {
        background-color: #1e1f20 !important;
        border: 1px solid #444746 !important;
        border-radius: 32px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }
    
    /* Welcome Header Animé */
    .welcome-container {
        margin-top: 12vh;
        text-align: center;
    }
    .welcome-title {
        background: linear-gradient(90deg, #4285f4, #9b72cb, #d96570, #4285f4);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 4rem;
        font-weight: 500;
        animation: gradient 5s linear infinite;
    }
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        100% { background-position: 200% 50%; }
    }
    
    .custom-footer {
        position: fixed;
        bottom: 15px;
        left: 50%;
        transform: translateX(-50%);
        color: #5f6368;
        font-size: 0.75rem;
        z-index: 100;
    }
</style>
""", unsafe_allow_html=True)

# --- INITIALISATION GROQ ---
api_key = st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.error("🔑 Erreur : 'GROQ_API_KEY' est manquante dans les Secrets Streamlit.")
    st.stop()
client = Groq(api_key=api_key)

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.markdown(f"""
    <div class="jbk-branding">
        <p class="jbk-role">Expert en Intelligence Artificielle</p>
        <p class="jbk-name">Julien Banze Kandolo</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("＋ Nouvelle discussion"):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    st.caption("🚀 Version Académique v3.0")
    st.caption("🧠 Modèle : Llama-3.3-70B")

# --- GESTION DU CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-container">
        <h1 class="welcome-title">Bonjour Julien.</h1>
        <h2 style='color: #8e918f; font-weight: 400; font-size: 2rem; margin-top: 10px;'>
            Comment puis-je t'aider dans tes projets aujourd'hui ?
        </h2>
    </div>
    """, unsafe_allow_html=True)

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Posez votre question scientifique ici..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Tu es l'Assistant Académique de Julien Banze Kandolo. IA experte, factuelle et scientifique."},
                    *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                ],
                stream=True,
            )
            for chunk in completion:
                content = chunk.choices[0].delta.content
                if content:
                    full_response += content
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"Erreur : {e}")

st.markdown("""<div class="custom-footer">Développé par Julien Banze Kandolo • Assistant Académique JBK</div>""", unsafe_allow_html=True)
