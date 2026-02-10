import streamlit as st
try:
    from groq import Groq
except ImportError:
    st.error("Le module 'groq' est manquant. Vérifiez votre fichier requirements.txt.")
    st.stop()
from PIL import Image
import io

st.set_page_config(
    page_title="Assistant Académique | Julien Banze Kandolo",
    page_icon="✨", 
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        padding-top: 1rem;
    }
    
    /* Carte de Profil JBK */
    .jbk-card {
        padding: 24px;
        background: linear-gradient(145deg, #2b2c2e, #1e1f20);
        border-radius: 20px;
        border: 1px solid #333537;
        margin-bottom: 2rem;
    }
    .jbk-name { font-size: 1.15rem; font-weight: 500; color: white; margin:0; }
    .jbk-role { font-size: 0.7rem; color: #8ab4f8; text-transform: uppercase; letter-spacing: 2px; font-weight: 500; }

    /* Boutons Style Google */
    .stButton>button {
        background-color: #1e1f20;
        color: #e3e3e3;
        border: 1px solid #444746;
        border-radius: 50px;
        padding: 10px 24px;
        width: 100%;
        text-align: left;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #333537;
        border-color: #8ab4f8;
        color: #8ab4f8;
    }

    /* BARRE DE SAISIE FLOTTANTE (DESIGN GEMINI) */
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

    /* Welcome Header Animé */
    .welcome-title {
        background: linear-gradient(90deg, #4285f4, #9b72cb, #d96570, #4285f4);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.8rem;
        font-weight: 500;
        animation: grad_flow 5s linear infinite;
    }
    @keyframes grad_flow { 0% {background-position: 0% 50%;} 100% {background-position: 200% 50%;} }

    /* Bulles de Chat */
    .stChatMessage {
        border-bottom: 1px solid #222 !important;
        padding: 1.5rem 5% !important;
    }
</style>
""", unsafe_allow_html=True)

api_key = st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.error("🔑 GROQ_API_KEY manquante dans les Secrets Streamlit.")
    st.stop()
client = Groq(api_key=api_key)

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
    st.markdown("<p style='font-size:0.8rem; color:#8ab4f8; font-weight:500;'>OPTIONS AVANCÉES</p>", unsafe_allow_html=True)
    voice_mode = st.toggle("Activer la réponse vocale")
    
    st.divider()
    uploaded_file = st.file_uploader("Joindre un document (Analyse Vision)", type=['png', 'jpg', 'jpeg', 'pdf'])
    
    st.divider()
    st.caption("🚀 Assistant Académique JBK")
    st.caption(f"👨‍💻 Par Julien Banze Kandolo")
    st.caption("🧠 Modèle : Llama-3.3-70B")

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.markdown("""
    <div style='margin-top: 15vh; text-align: center;'>
        <h1 class="welcome-title">Je suis votre assistant.</h1>
        <h2 style='color: #8e918f; font-weight: 400; font-size: 1.8rem;'>Que souhaiteriez-vous savoir aujourd'hui ?</h2>
    </div>
    """, unsafe_allow_html=True)

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Posez votre question académique ici..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_res = ""
        
        try:
            with st.spinner("Analyse de la requête..."):
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "Tu es l'Assistant Académique de Julien Banze Kandolo. Tu es une IA experte et scientifique."},
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
                            var msg = new SpeechSynthesisUtterance({repr(full_res[:300])});
                            msg.lang = 'fr-FR';
                            window.speechSynthesis.speak(msg);
                        </script>
                    """, height=0)
            
        except Exception as e:
            st.error(f"Erreur de connexion : {e}")

st.markdown("<div style='position:fixed; bottom:15px; left:50%; transform:translateX(-50%); color:#5f6368; font-size:0.75rem;'>Propulsé par Julien Banze Kandolo • Assistant Académique JBK</div>", unsafe_allow_html=True)
