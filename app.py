
import streamlit as st
try:
    from groq import Groq
except ImportError:
    st.error("Le module 'groq' est manquant. Vérifiez votre fichier requirements.txt.")
    st.stop()
from PIL import Image
import io

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Assistant Académique | Julien Banze Kandolo",
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLE CSS AVANCÉ (OPTIMISATION ESPACES ET MOBILE) ---
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

    /* Réduction des marges supérieures de Streamlit */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        max-width: 1000px;
    }
    
    /* Sidebar Moderne */
    [data-testid="stSidebar"] { 
        background-color: #1e1f20 !important; 
        border-right: none;
    }
    
    /* Carte de Profil JBK - Plus compacte */
    .jbk-card {
        padding: 15px;
        background: linear-gradient(145deg, #2b2c2e, #1e1f20);
        border-radius: 15px;
        border: 1px solid #333537;
        margin-bottom: 1rem;
        text-align: center;
    }
    .jbk-name { font-size: 1.1rem; font-weight: 500; color: white; margin:0; }
    .jbk-role { font-size: 0.7rem; color: #8ab4f8; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 500; }

    /* Boutons Style Google */
    .stButton>button {
        background-color: #1e1f20;
        color: #e3e3e3;
        border: 1px solid #444746;
        border-radius: 50px;
        padding: 8px 20px;
        width: 100%;
        text-align: left;
    }

    /* BARRE DE SAISIE FLOTTANTE - AJUSTÉE POUR MOBILE */
    .stChatInputContainer {
        padding: 0 5% 1.5rem 5% !important;
        background-color: transparent !important;
    }
    .stChatInputContainer > div {
        background-color: #1e1f20 !important;
        border: 1px solid #444746 !important;
        border-radius: 28px !important;
    }

    /* Welcome Header Animé */
    .welcome-title {
        background: linear-gradient(90deg, #4285f4, #9b72cb, #d96570, #4285f4);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 500;
        animation: grad_flow 5s linear infinite;
        margin-bottom: 0.5rem;
    }
    @keyframes grad_flow { 0% {background-position: 0% 50%;} 100% {background-position: 200% 50%;} }

    /* Icône de diplôme */
    .grad-icon {
        font-size: 3rem;
        margin-bottom: 10px;
        display: block;
    }

    /* Bulles de Chat - Espacements réduits */
    .stChatMessage {
        border-bottom: 1px solid #222 !important;
        padding: 0.8rem 2% !important;
        background-color: transparent !important;
    }

    /* Signature Bas de page ultra-lisible */
    .footer-signature {
        position: fixed;
        bottom: 15px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(30, 31, 32, 0.8);
        padding: 5px 20px;
        border-radius: 20px;
        border: 1px solid #444746;
        color: #ffffff;
        font-size: 0.85rem;
        font-weight: 500;
        z-index: 1000;
        white-space: nowrap;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }

    /* Ajustements Android/Mobile */
    @media (max-width: 768px) {
        .welcome-title { font-size: 2rem; }
        .block-container { padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
        .stChatInputContainer { padding: 0 2% 1rem 2% !important; }
        .footer-signature { font-size: 0.75rem; bottom: 10px; }
    }
</style>
""", unsafe_allow_html=True)

# --- INITIALISATION API GROQ ---
api_key = st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.error("🔑 GROQ_API_KEY manquante dans les Secrets Streamlit.")
    st.stop()
client = Groq(api_key=api_key)

# --- BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.markdown(f"""
    <div class="jbk-card">
        <p class="jbk-role">Assistant Académique</p>
        <p class="jbk-name">Julien Banze Kandolo</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("＋ Nouvelle Session"):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    st.markdown("<p style='font-size:0.75rem; color:#8ab4f8; font-weight:500;'>OPTIONS</p>", unsafe_allow_html=True)
    voice_mode = st.toggle("Réponse vocale")
    
    uploaded_file = st.file_uploader("Document (Vision)", type=['png', 'jpg', 'pdf'])
    
    st.divider()
    st.caption("🚀 Assistant Académique JBK")

# --- MOTEUR DE CONVERSATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Écran d'accueil
if not st.session_state.messages:
    st.markdown(f"""
    <div style='margin-top: 12vh; text-align: center;'>
        <span class="grad-icon">🎓</span>
        <h1 class="welcome-title">Je suis votre assistant.</h1>
        <p style='color: #8e918f; font-size: 1.3rem;'>Que souhaiteriez-vous savoir aujourd'hui ?</p>
    </div>
    """, unsafe_allow_html=True)

# Affichage des messages
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Zone de saisie utilisateur
if prompt := st.chat_input("Écrivez ici..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_res = ""
        
        try:
            with st.spinner("Réflexion..."):
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "Tu es l'Assistant Académique de Julien Banze Kandolo. IA experte et scientifique."},
                        *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                    ],
                    stream=True,
                )

                for chunk in completion:
                    content = chunk.choices[0].delta.content
                    if content:
                        full_res += content
                        message_placeholder.markdown(full_res + "▌")
                
                message_placeholder.markdown(full_res)
                st.session_state.messages.append({"role": "assistant", "content": full_res})
                
                if voice_mode:
                    st.components.v1.html(f"""
                        <script>
                            var msg = new SpeechSynthesisUtterance({repr(full_res[:250])});
                            msg.lang = 'fr-FR';
                            window.speechSynthesis.speak(msg);
                        </script>
                    """, height=0)
            
        except Exception as e:
            st.error(f"Erreur : {e}")

# Footer Signature - Lisible et bien placée
st.markdown("""
    <div class="footer-signature">
        Julien Banze Kandolo • Assistant Académique JBK 🎓
    </div>
""", unsafe_allow_html=True)
