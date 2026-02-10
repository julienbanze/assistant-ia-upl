
import streamlit as st
from groq import Groq
from PIL import Image
import io

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Assistant Académique | Julien Banze Kandolo",
    page_icon="✨", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLE CSS PERSONNALISÉ (DESIGN GEMINI) ---
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
    
    [data-testid="stSidebar"] { 
        background-color: #1e1f20 !important; 
        border-right: none;
    }
    
    .stButton>button {
        background-color: #1a1b1c;
        color: #e3e3e3;
        border: 1px solid #444746;
        border-radius: 24px;
        padding: 10px 24px;
        width: 100%;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #333537;
        border-color: #8ab4f8;
    }

    .stChatInputContainer {
        border-top: none !important;
        background-color: transparent !important;
        padding: 1rem 10% !important;
    }
    
    .stChatInputContainer > div {
        background-color: #1e1f20 !important;
        border: 1px solid #444746 !important;
        border-radius: 32px !important;
    }
    
    .branding-card {
        padding: 1.5rem;
        background-color: #28292a;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        border: 1px solid #333;
    }
    .dev-name { font-size: 1.1rem; font-weight: 500; color: white; margin:0; }
    .dev-role { font-size: 0.75rem; color: #8ab4f8; text-transform: uppercase; letter-spacing: 1px; }

</style>
""", unsafe_allow_html=True)

# --- INITIALISATION DU MOTEUR GROQ ---
# Récupération de la clé depuis les secrets de Streamlit
api_key = st.secrets.get("GROQ_API_KEY")

if api_key:
    client = Groq(api_key=api_key)
else:
    st.error("🔑 Configuration manquante : Ajoutez 'GROQ_API_KEY' dans les Secrets de Streamlit.")
    st.stop()

# --- BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.markdown("""
    <div class="branding-card">
        <p class="dev-role">Architecte IA Académique</p>
        <p class="dev-name">Julien Banze Kandolo</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<h3 style='text-align:center; color:#e3e3e3;'>Menu Assistant</h3>", unsafe_allow_html=True)
    
    if st.button("＋ Nouvelle Session"):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    uploaded_file = st.file_uploader("Analyser une image", type=['png', 'jpg', 'jpeg'])
    
    st.divider()
    st.caption("⚙️ Moteur : Llama 3.3 70B")
    st.caption("📍 Statut : Connecté")

# --- INTERFACE DE CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Message de bienvenue si vide
if not st.session_state.messages:
    st.markdown("""
    <div style='margin-top: 15vh; text-align: center;'>
        <h1 style='font-size: 3.5rem; font-weight: 500; color: white;'>Bonjour Julien.</h1>
        <h2 style='color: #888; font-weight: 400;'>Comment puis-je t'aider dans tes recherches aujourd'hui ?</h2>
    </div>
    """, unsafe_allow_html=True)

# Affichage de l'historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Zone de saisie (Input)
if prompt := st.chat_input("Posez votre question académique ici..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Envoi de la requête au moteur Llama 3 via Groq
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Tu es l'Assistant Académique de Julien Banze Kandolo. Tu es une IA experte, factuelle et scientifique. Tu réponds de manière structurée."},
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
            st.error(f"Erreur de connexion : {e}")

# Footer
st.markdown(f"""
    <div style="position: fixed; bottom: 10px; left: 50%; transform: translateX(-50%); color: #5f6368; font-size: 0.7rem; text-align: center; width: 100%;">
        Développé par Julien Banze Kandolo • Assistant Académique v2.5
    </div>
""", unsafe_allow_html=True)
