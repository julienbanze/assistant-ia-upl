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
/* Fond de l'application */
.stApp {
    background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
    color: white;
}

h1 {
    color: #FFD700;
    text-align: center;
    margin-bottom: 0px;
}

/* Style pour le message professionnel de la bibliothèque */
.biblio-box {
    text-align: center;
    padding: 15px;
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 15px;
    border: 1px solid #FFD700;
    margin: 10px auto 25px auto;
    max-width: 800px;
}

.biblio-link {
    color: #25D366 !important;
    font-weight: bold;
    text-decoration: none;
    font-size: 1.1em;
}

/* --- STYLE WHATSAPP POUR LE CHAT INPUT --- */
div[data-testid="stChatInput"] {
    border: none !important;
}

div[data-testid="stChatInput"] > div {
    border: 2px solid #25D366 !important;
    border-radius: 25px !important;
    background-color: #1e2a38 !important;
}

div[data-testid="stChatInput"] textarea {
    box-shadow: none !important;
    border: none !important;
    color: white !important;
}

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
</style>
""", unsafe_allow_html=True)

# -----------------------
# LOGS
# -----------------------
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()])

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
# SIDEBAR (Le menu à trois lignes s'affiche auto ici)
# -----------------------
st.sidebar.title("⚙️ Paramètres")
mode = st.sidebar.selectbox("Mode d'assistance", ["Étudiant", "Enseignant"])
st.session_state.mode = mode

# -----------------------
# HEADER & LIEN BIBLIOTHÈQUE
# -----------------------
st.markdown("# 🎓 Assistant Académique IA")

# Message professionnel et lien vers la bibliothèque de l'UPL
st.markdown("""
<div class="biblio-box">
    🚀 <i>Enrichissez vos recherches en consultant les ressources officielles :</i><br>
    <a class="biblio-link" href="https://bibliotheque.upl-univ.ac/" target="_blank">
        📖 Visitez la Bibliothèque Numérique de l'UPL
    </a>
</div>
""", unsafe_allow_html=True)

# -----------------------
# LOGIQUE (FILTRE, PROMPT, TTS)
# -----------------------
def is_academic(question):
    mots_interdits = ["football","match","musique","chanson","film","serie","amour","copine","copain","jeu","divertissement","buzz"]
    return not any(mot in question.lower() for mot in mots_interdits)

def get_system_prompt(mode):
    base = "Tu es un assistant académique professionnel. Règle : Réponds uniquement aux questions éducatives."
    if mode == "Étudiant":
        base += "\nMode Étudiant : Explications simples et pédagogiques."
    else:
        base += "\nMode Enseignant : Détails approfondis et niveau universitaire."
    return base

def text_to_speech(text):
    tts = gTTS(text=text, lang='fr')
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_file.name)
    return temp_file.name

# -----------------------
# INTERFACE DE CHAT
# -----------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

audio = st.audio_input("🎤 Parlez")
if audio is not None:
    try:
        transcription = client.audio.transcriptions.create(file=("audio.wav", audio.getvalue()), model="whisper-large-v3")
        prompt = transcription.text.strip()
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
    except:
        st.warning("Erreur audio")

prompt = st.chat_input("Pose ta question...")
if prompt:
    if not is_academic(prompt):
        response = "Je suis un assistant académique conçu pour répondre uniquement aux questions éducatives."
        st.chat_message("assistant").markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.stop()

    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

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
            stream = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True)
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
            audio_file = text_to_speech(full_response)
            st.audio(audio_file, format="audio/mp3")
        except Exception as e:
            st.error(f"Erreur IA : {e}")

    st.session_state.messages.append({"role": "assistant", "content": full_response})

# -----------------------
# FOOTER
# -----------------------
st.markdown("---")
st.markdown("<p style='text-align: center;'>Développé par <b>Julien Banze Kandolo</b> 🚀</p>", unsafe_allow_html=True)
