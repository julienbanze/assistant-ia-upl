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
# DESIGN PRO (ÉLIMINATION TOTALE DU ROUGE)
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
}

/* --- NETTOYAGE DU CHAMP DE SAISIE --- */

/* On supprime la bordure rouge sur TOUS les états du conteneur parent */
div[data-testid="stChatInput"] {
    border: none !important;
    box-shadow: none !important;
}

/* Ciblage du cadre extérieur (fieldset) pour forcer la disparition du rouge */
div[data-testid="stChatInput"] fieldset {
    border: none !important;
    outline: none !important;
}

/* Ciblage du conteneur interne BaseWeb */
div[data-baseweb="base-input"], div[data-baseweb="input"] {
    border: none !important;
    outline: none !important;
    background-color: transparent !important;
}

/* Style du champ de texte (textarea) */
div[data-testid="stChatInput"] textarea {
    background-color: #1e2a38 !important;
    color: white !important;
    border-radius: 25px !important;
    border: 1px solid #3d4b5c !important; 
    padding-right: 45px !important;
    caret-color: #25D366 !important; /* Curseur vert */
}

/* On force le contour VERT uniquement lors de la saisie */
div[data-testid="stChatInput"] textarea:focus {
    box-shadow: 0 0 0 2px #25D366 !important; 
    border: 1px solid #25D366 !important;
    outline: none !important;
}

/* Suppression de l'ombre de focus par défaut de Streamlit */
.stChatInput:focus-within {
    box-shadow: none !important;
}

/* --- BOUTON ENVOI STYLE WHATSAPP --- */
div[data-testid="stChatInput"] button {
    background-color: #25D366 !important; /* Vert WhatsApp */
    border-radius: 50% !important;
    right: 12px !important;
    bottom: 10px !important;
    width: 38px !important;
    height: 38px !important;
    border: none !important;
    transition: transform 0.2s ease;
}

div[data-testid="stChatInput"] button:hover {
    transform: scale(1.1);
    background-color: #128C7E !important;
}

/* Icône d'envoi blanche */
div[data-testid="stChatInput"] button svg {
    color: white !important;
    fill: white !important;
}

/* Désactivation des contours sur le bouton */
div[data-testid="stChatInput"] button:focus, 
div[data-testid="stChatInput"] button:active {
    outline: none !important;
    box-shadow: none !important;
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
    except Exception:
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
# SIDEBAR
# -----------------------

st.sidebar.title("⚙️ Paramètres")

mode = st.sidebar.selectbox(
    "Mode",
    ["Étudiant", "Enseignant"]
)

st.session_state.mode = mode

# -----------------------
# FILTRE ACADEMIQUE
# -----------------------

def is_academic(question):
    mots_interdits = [
        "football","match","musique","chanson",
        "film","serie","amour","copine","copain",
        "jeu","divertissement","buzz"
    ]

    question = question.lower()

    for mot in mots_interdits:
        if mot in question:
            return False
    return True

# -----------------------
# PROMPT IA
# -----------------------

def get_system_prompt(mode):
    base = """
Tu es un assistant académique professionnel.

Règles STRICTES :
- Réponds uniquement aux questions éducatives
- Refuse les sujets hors contexte
- Ne salue qu'une seule fois
- Réponds de manière claire et naturelle
"""
    if mode == "Étudiant":
        base += "\nMode Étudiant :\n- Explications simples\n- Exemples"
    else:
        base += "\nMode Enseignant :\n- Réponses détaillées\n- Niveau avancé"
    return base

# -----------------------
# TEXT TO SPEECH
# -----------------------

def text_to_speech(text):
    tts = gTTS(text=text, lang='fr')
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_file.name)
    return temp_file.name

# -----------------------
# HEADER
# -----------------------

st.markdown("# 🎓 Assistant Académique IA")

# -----------------------
# HISTORIQUE
# -----------------------

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------
# AUDIO INPUT
# -----------------------

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
    except Exception:
        st.warning("Erreur lors de la transcription audio.")

# -----------------------
# TEXTE INPUT
# -----------------------

prompt = st.chat_input("Pose ta question...")

if prompt:
    if not is_academic(prompt):
        response = "Je suis un assistant académique conçu pour répondre uniquement aux questions éducatives."
        st.chat_message("assistant").markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.stop()

    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

# -----------------------
# REPONSE IA
# -----------------------

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

            # 🔊 AUDIO RESPONSE
            audio_file = text_to_speech(full_response)
            st.audio(audio_file, format="audio/mp3")

        except Exception as e:
            st.error(f"Erreur IA : {e}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response
    })

# -----------------------
# FOOTER
# -----------------------

st.markdown("---")
st.markdown("Développé par **Julien Banze Kandolo** 🚀")
