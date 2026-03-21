import streamlit as st
from groq import Groq
from gtts import gTTS
import tempfile
import logging
from pathlib import Path

# -----------------------
# CONFIG PAGE
# -----------------------

st.set_page_config(
    page_title="Assistant Académique IA 🎓",
    page_icon="🎓",
    layout="wide"
)

# -----------------------
# DESIGN PRO & PERSONNALISATION
# -----------------------

st.markdown("""
<style>
/* Fond général */
.stApp {
    background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
    color: white;
}

h1 {
    color: #FFD700;
    text-align: center;
}

/* --- STYLE WHATSAPP & CHAT INPUT --- */
div[data-testid="stChatInput"] {
    border: none !important;
}

div[data-testid="stChatInput"] > div {
    border: 2px solid #25D366 !important; /* Bordure verte uniquement */
    border-radius: 25px !important;
    background-color: #1e2a38 !important;
}

div[data-testid="stChatInput"] textarea {
    box-shadow: none !important;
    border: none !important;
    color: white !important;
}

/* Bouton d'envoi style WhatsApp */
div[data-testid="stChatInput"] button {
    background-color: #25D366 !important;
    border-radius: 50% !important;
    border: none !important;
    right: 10px !important;
    bottom: 4px !important;
    height: 40px !important;
    width: 40px !important;
}

div[data-testid="stChatInput"] button svg {
    color: white !important;
    fill: white !important;
}

/* Style lien bibliothèque */
.biblio-link {
    display: block;
    text-align: center;
    padding: 10px;
    background-color: #004a99;
    color: white !important;
    border-radius: 10px;
    text-decoration: none;
    font-weight: bold;
    margin-top: 10px;
}
.biblio-link:hover {
    background-color: #0056b3;
}
</style>
""", unsafe_allow_html=True)

# -----------------------
# LOGS
# -----------------------

Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

# -----------------------
# GROQ CLIENT
# -----------------------

@st.cache_resource
def init_client():
    try:
        return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except:
        st.error("Ajoutez GROQ_API_KEY dans Settings > Secrets")
        st.stop()

client = init_client()

# -----------------------
# SESSION
# -----------------------

if "messages" not in st.session_state:
    st.session_state.messages = []
if "mode" not in st.session_state:
    st.session_state.mode = "Étudiant"
if "has_greeted" not in st.session_state:
    st.session_state.has_greeted = False

# -----------------------
# SIDEBAR (LOGO & BIBLIOTHÈQUE)
# -----------------------

# Ajout du logo UPL
st.sidebar.image("logo_upl.png", use_container_width=True) # Assure-toi que le fichier s'appelle logo_upl.png

# Lien bibliothèque
st.sidebar.markdown('<a href="https://bibliotheque.upl-univ.ac/" target="_blank" class="biblio-link">📚 Bibliothèque UPL</a>', unsafe_allow_html=True)

st.sidebar.divider()
st.sidebar.title("⚙️ Paramètres")
mode = st.sidebar.selectbox("Mode", ["Étudiant", "Enseignant"])
st.session_state.mode = mode

# -----------------------
# FONCTIONS LOGIQUE (FILTRE, PROMPT, TTS)
# -----------------------

def is_academic(question):
    mots_interdits = ["football","match","musique","chanson","film","serie","amour","copine","copain","jeu","divertissement","buzz"]
    question = question.lower()
    for mot in mots_interdits:
        if mot in question: return False
    return True

def get_system_prompt(mode):
    base = "Tu es un assistant académique professionnel. Règle : Réponds uniquement aux questions éducatives."
    if mode == "Étudiant": base += "\nMode Étudiant : Explications simples et exemples."
    else: base += "\nMode Enseignant : Détails poussés et niveau avancé."
    return base

def text_to_speech(text):
    tts = gTTS(text=text, lang='fr')
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_file.name)
    return temp_file.name

# -----------------------
# INTERFACE PRINCIPALE
# -----------------------

st.markdown("# 🎓 Assistant Académique IA")

# Historique
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Entrée Audio
audio = st.audio_input("🎤 Parlez")
if audio is not None:
    try:
        transcription = client.audio.transcriptions.create(
            file=("audio.wav", audio.getvalue()),
            model="whisper-large-v3"
        )
        prompt_audio = transcription.text.strip()
        st.chat_message("user").markdown(prompt_audio)
        st.session_state.messages.append({"role": "user", "content": prompt_audio})
    except:
        st.warning("Erreur audio")

# Entrée Texte (CHAT INPUT)
prompt = st.chat_input("Pose ta question...")

if prompt:
    if not is_academic(prompt):
        resp = "Je suis un assistant académique conçu pour les questions éducatives uniquement."
        st.chat_message("assistant").markdown(resp)
        st.session_state.messages.append({"role": "assistant", "content": resp})
        st.stop()
    
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

# Réponse IA
if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        SYSTEM_PROMPT = get_system_prompt(st.session_state.mode)
        if st.session_state.has_greeted:
            SYSTEM_PROMPT += "\nNe commence pas par une salutation."
        else:
            st.session_state.has_greeted = True

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in st.session_state.messages[-10:]:
            messages.append(msg)

        try:
            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
            
            # Audio
            audio_file = text_to_speech(full_response)
            st.audio(audio_file, format="audio/mp3")
        except Exception as e:
            st.error(f"Erreur IA : {e}")

    st.session_state.messages.append({"role": "assistant", "content": full_response})

# -----------------------
# FOOTER
# -----------------------
st.markdown("---")
st.markdown("Développé par **Julien Banze Kandolo** 🚀")
