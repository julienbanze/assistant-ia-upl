import streamlit as st
from groq import Groq
from gtts import gTTS
import tempfile
import os
from streamlit_mic_recorder import mic_recorder # 👈 Nouveau composant pour la voix

# -----------------------
# CONFIG PAGE
# -----------------------
st.set_page_config(
    page_title="Assistant Académique IA",
    page_icon="logo.jpg",
    layout="wide"
)

# -----------------------
# STYLE CSS AMÉLIORÉ
# -----------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
    color: white;
}
/* Style pour aligner logo et titre */
.header-container {
    display: flex;
    align-items: center;
    gap: 20px;
    margin-bottom: 20px;
}
h1 { 
    color: #FFD700; 
    margin: 0; 
    padding: 0;
    font-size: 2.5rem;
}
.logo-img {
    border-radius: 10px;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
}

div[data-testid="stChatInput"] > div {
    border: 2px solid #25D366 !important;
    border-radius: 25px !important;
    background-color: #1e2a38 !important;
}
</style>
""", unsafe_allow_html=True)

# -----------------------
# GROQ CLIENT
# -----------------------
@st.cache_resource
def init_client():
    try:
        return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except:
        st.error("Clé API manquante dans les secrets")
        st.stop()

client = init_client()

if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------
# FONCTIONS UTILES
# -----------------------
def get_system_prompt(mode):
    return f"Tu es un assistant académique sérieux pour l'UPL. Tu aides uniquement dans les études. Mode actuel : {mode}"

def text_to_speech(text):
    tts = gTTS(text=text, lang='fr')
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp.name)
    return temp.name

def transcribe_audio(audio_bytes):
    """Transcrit l'audio en texte via Whisper de Groq"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(audio_bytes)
            temp_audio_path = temp_audio.name
        
        with open(temp_audio_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(temp_audio_path, file.read()),
                model="whisper-large-v3",
                language="fr"
            )
        os.unlink(temp_audio_path)
        return transcription.text
    except Exception as e:
        st.error(f"Erreur de transcription : {e}")
        return None

# -----------------------
# SIDEBAR
# -----------------------
with st.sidebar:
    st.image("logo.jpg", width=120)
    st.title("⚙️ Paramètres")
    mode = st.selectbox("Niveau", ["Étudiant", "Enseignant"])
    st.session_state.mode = mode
    st.info("Utilisez le micro en bas pour poser votre question oralement.")

# -----------------------
# HEADER (LOGO + TITRE ALIGNÉS)
# -----------------------
# Utilisation de colonnes avec alignement vertical via CSS injecté plus haut
col_logo, col_titre = st.columns([1, 6])
with col_logo:
    st.image("logo.jpg", width=80)
with col_titre:
    st.markdown("<h1 style='line-height: 80px;'>Assistant Académique IA</h1>", unsafe_allow_html=True)

# -----------------------
# CHAT ET AUDIO INPUT
# -----------------------
# Affichage des messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Conteneur pour les entrées (Texte + Micro)
st.write("---")
c1, c2 = st.columns([9, 1])

with c1:
    prompt = st.chat_input("Pose ta question ici...")

with c2:
    # Bouton Micro
    audio_input = mic_recorder(
        start_prompt="🎤",
        stop_prompt="🛑",
        key='recorder'
    )

# Logique de traitement (si texte OU si audio)
final_prompt = None

if prompt:
    final_prompt = prompt
elif audio_input:
    with st.spinner("Transcription de votre voix..."):
        text_from_voice = transcribe_audio(audio_input['bytes'])
        if text_from_voice:
            final_prompt = text_from_voice

# Si on a un message (voix ou texte)
if final_prompt:
    st.chat_message("user").markdown(final_prompt)
    st.session_state.messages.append({"role": "user", "content": final_prompt})

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        messages_api = [{"role": "system", "content": get_system_prompt(st.session_state.mode)}]
        for m in st.session_state.messages[-5:]:
            messages_api.append(m)

        try:
            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages_api,
                stream=True,
                temperature=0.2
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    placeholder.markdown(full_response + "▌")

            placeholder.markdown(full_response)

            # Synthèse vocale de la réponse
            audio_response_path = text_to_speech(full_response)
            st.audio(audio_response_path)

            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"Erreur IA : {e}")

# -----------------------
# FOOTER
# -----------------------
st.markdown("<br><p style='text-align:center; opacity: 0.6;'>UPL | Développé par Julien Banze 🚀</p>", unsafe_allow_html=True)
