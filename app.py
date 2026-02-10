
import streamlit as st
try:
    from groq import Groq
except ImportError:
    st.error("Le module 'groq' est manquant. Vérifiez votre fichier requirements.txt.")
    st.stop()
from PIL import Image
import io
import time

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Assistant Académique | Julien Banze Kandolo",
    page_icon="✨", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLE CSS AVANCÉ (EXPÉRIENCE GEMINI ULTIME) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500&display=swap');
    
    html, body, [data-testid="stapp"], [data-testid="stHeader"] { 
        font-family: 'Google Sans', sans-serif;
        background-color: #131314 !important;
        color: #e3e3e3;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Sidebar Moderne */
    [data-testid="stSidebar"] { 
        background-color: #1e1f20 !important; 
        border-right: none;
    }
    
    /* Carte JBK Premium */
    .jbk-card {
        padding: 24px;
        background: linear-gradient(145deg, #2b2c2e, #1e1f20);
        border-radius: 20px;
        border: 1px solid #333537;
        margin-bottom: 2rem;
    }
    .jbk-name { font-size: 1.1rem; font-weight: 500; color: white; margin:0; }
    .jbk-role { font-size: 0.7rem; color: #8ab4f8; text-transform: uppercase; letter-spacing: 2px; font-weight: 500; }

    /* Boutons Style Google */
    .stButton>button {
        background-color: #1e1f20;
        color: #e3e3e3;
        border: 1px solid #444746;
        border-radius: 50px;
        padding: 10px 20px;
        width: 100%;
        text-align: left;
        transition: 0.2s;
    }
    .stButton>button:hover {
        background-color: #333537;
        border-color: #8ab4f8;
    }

    /* Barre de Saisie Flottante */
    .stChatInputContainer {
        padding: 0 10% 3rem 10% !important;
        background-color: transparent !important;
    }
    .stChatInputContainer > div {
        background-color: #1e1f20 !important;
        border: 1px solid #444746 !important;
        border-radius: 32px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }

    /* Welcome Text Gemini */
    .welcome-title {
        background: linear-gradient(90deg, #4285f4, #9b72cb, #d96570, #4285f4);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.8rem;
        font-weight: 500;
        animation: grad 5s linear infinite;
    }
    @keyframes grad { 0% {background-position: 0% 50%;} 100% {background-position: 200% 50%;} }

    /* Historique */
    .history-item {
        font-size: 0.85rem;
        padding: 8px 12px;
        color: #c4c7c5;
        cursor: pointer;
        border-radius: 8px;
    }
    .history-item:hover { background-color: #333537; }

</style>
""", unsafe_allow_html=True)

# --- INITIALISATION API ---
api_key = st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.error("🔑 GROQ_API_KEY manquante.")
    st.stop()
client = Groq(api_key=api_key)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("""
    <div class="jbk-card">
        <p class="jbk-role">Expert en Intelligence Artificielle</p>
        <p class="jbk-name">Julien Banze Kandolo</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("＋ Nouvelle Session"):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    st.markdown("<p style='font-size:0.8rem; color:#8ab4f8;'>HISTORIQUE RÉCENT</p>", unsafe_allow_html=True)
    st.markdown("<div class='history-item'>💭 Analyse de données UPL</div>", unsafe_allow_html=True)
    st.markdown("<div class='history-item'>💭 Recherche Algorithmie</div>", unsafe_allow_html=True)
    
    st.divider()
    st.markdown("<p style='font-size:0.8rem; color:#8ab4f8;'>OUTILS AVANCÉS</p>", unsafe_allow_html=True)
    voice_mode = st.toggle("Activer la réponse vocale")
    search_mode = st.toggle("Mode recherche Web profond")
    
    st.divider()
    uploaded_file = st.file_uploader("Analyser un document", type=['png', 'jpg', 'pdf'])

# --- CHAT ENGINE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.markdown("""
    <div style='margin-top: 15vh; text-align: center;'>
        <h1 class="welcome-title">Bonjour Julien.</h1>
        <h2 style='color: #8e918f; font-weight: 400; font-size: 1.8rem;'>Expert IA à votre service. Que voulez-vous accomplir ?</h2>
    </div>
    """, unsafe_allow_html=True)

# Affichage
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Input
if prompt := st.chat_input("Posez votre question scientifique..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        
        try:
            with st.spinner("L'expert IA réfléchit..."):
                system_msg = "Tu es l'Assistant Académique de Julien Banze Kandolo. IA experte et scientifique."
                if search_mode:
                    system_msg += " Simule une recherche web approfondie pour donner des sources précises."
                
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_msg},
                        *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                    ],
                    stream=True,
                )

                for chunk in completion:
                    content = chunk.choices[0].delta.content
                    if content:
                        full_res += content
                        placeholder.markdown(full_res + "▌")
                
                placeholder.markdown(full_res)
                st.session_state.messages.append({"role": "assistant", "content": full_res})
                
                # Fonctionnalité Vocale (Simulation TTS via HTML)
                if voice_mode:
                    st.components.v1.html(f"""
                        <script>
                            var msg = new SpeechSynthesisUtterance({repr(full_res[:200])});
                            msg.lang = 'fr-FR';
                            window.speechSynthesis.speak(msg);
                        </script>
                    """, height=0)
            
        except Exception as e:
            st.error(f"Erreur : {e}")

st.markdown("<div style='position:fixed; bottom:15px; left:50%; transform:translateX(-50%); color:#5f6368; font-size:0.75rem;'>Développé par Julien Banze Kandolo • Expert IA JBK</div>", unsafe_allow_html=True)

