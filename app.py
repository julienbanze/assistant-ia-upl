import streamlit as st
from groq import Groq

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Assistant Académique | Julien Banze Kandolo",
    page_icon="🎓",
    layout="wide"
)

# --- 2. INTEGRATION DU CSS DIRECTE (Design Académique) ---
# On utilise st.markdown pour injecter le style sans avoir besoin d'un fichier externe
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Google Sans', sans-serif;
        background-color: #131314 !important;
        color: #e3e3e3;
    }

    /* Carte de Profil Julien Banze Kandolo */
    .jbk-card {
        padding: 15px;
        background: linear-gradient(145deg, #2b2c2e, #1e1f20);
        border-radius: 15px;
        border: 1px solid #444746;
        text-align: center;
        margin-bottom: 1rem;
    }
    .jbk-name { font-size: 1.1rem; font-weight: 700; color: #8ab4f8; margin:0; }

    /* Titre Animé */
    .welcome-title {
        background: linear-gradient(90deg, #4285f4, #9b72cb, #d96570, #4285f4);
        background-size: 200% auto;
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 700;
        animation: grad_flow 5s linear infinite;
        text-align: center;
    }
    @keyframes grad_flow { 0% {background-position: 0% 50%;} 100% {background-position: 200% 50%;} }

    /* Adaptation Mobile */
    @media (max-width: 768px) {
        .welcome-title { font-size: 1.8rem !important; }
        .stChatInputContainer { padding-bottom: 20px !important; }
    }

    /* Signature */
    .input-label-name {
        text-align: center;
        color: #8ab4f8;
        font-size: 0.9rem;
        margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. INITIALISATION API GROQ ---
# Utilise bien GROQ_API_KEY dans tes secrets Streamlit
api_key = st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.error("🔑 Erreur : GROQ_API_KEY manquante dans les Secrets Streamlit.")
    st.stop()
client = Groq(api_key=api_key)

# --- 4. BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.markdown(f"""
    <div class="jbk-card">
        <p style='font-size: 0.7rem; color: #8ab4f8; text-transform: uppercase; margin:0;'>Expert IA</p>
        <p class="jbk-name">Julien Banze Kandolo</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("＋ Nouvelle Session"):
        st.session_state.messages = []
        st.rerun()

# --- 5. LOGIQUE DE CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Écran d'accueil si pas de messages
if not st.session_state.messages:
    st.markdown("<div style='margin-top: 10vh;'><h1 class='welcome-title'>Assistant Académique JBK</h1><p style='text-align:center;'>Posez vos questions sur vos cours de l'UPL.</p></div>", unsafe_allow_html=True)

# Affichage des messages
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Signature au-dessus de l'input
st.markdown('<div class="input-label-name">Julien Banze Kandolo • Assistant Académique JBK 🎓</div>', unsafe_allow_html=True)

# Entrée utilisateur
if prompt := st.chat_input("Posez votre question académique..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        
        try:
            # On force le comportement académique ici
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Tu es l'Assistant Académique de Julien Banze Kandolo. Réponds exclusivement aux sujets liés aux études, informatique, électronique et mathématiques."},
                    *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                ],
                stream=True
            )

            for chunk in completion:
                content = chunk.choices[0].delta.content
                if content:
                    full_res += content
                    placeholder.markdown(full_res + "▌")
            
            placeholder.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            
        except Exception as e:
            st.error(f"Erreur : {e}")
