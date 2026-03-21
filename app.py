import streamlit as st
from groq import Groq
from gtts import gTTS
import tempfile
import logging
import os
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
# DESIGN PRO & STYLE WHATSAPP
# -----------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
    color: white;
}

h1 { color: #FFD700; text-align: center; }

/* Supprimer le contour rouge et styliser l'input */
div[data-testid="stChatInput"] { border: none !important; }

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

/* Bouton style WhatsApp */
div[data-testid="stChatInput"] button {
    background-color: #25D366 !important;
    border-radius: 50% !important;
    border: none !important;
    height: 40px !important;
    width: 40px !important;
}

div[data-testid="stChatInput"] button svg {
    color: white !important;
    fill: white !important;
}

/* Style du lien Bibliothèque */
.biblio-link {
    display: block;
    text-align: center;
    padding: 12px;
    background-color: #004a99;
    color: white !important;
    border-radius: 10px;
    text-decoration: none;
    font-weight: bold;
    margin-top: 15px;
    border: 1px solid #FFD700;
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
        st.error("Ajoutez GROQ_API_KEY dans vos Secrets")
        st.stop()

client = init_client()

# -----------------------
# SESSION STATE
# -----------------------
if "messages" not in st.session_state: st.session_state.messages = []
if "mode" not in st.session_state: st.session_state.mode = "Étudiant"
if "has_greeted" not in st.session_state: st.session_state.has_greeted = False

# -----------------------
# SIDEBAR (CORRECTION ERREUR IMAGE)
# -----------------------
with st.sidebar:
    # On tente d'afficher l'image via URL pour éviter le crash
    url_logo = "https://bibliotheque.upl-univ.ac/wp-content/uploads/2021/04/Logo-UPL.png"
    try:
        st.image(url_logo, use_container_width=True)
    except:
        st.write("🎓 **Université Protestante de Lubumbashi**")
    
    st.markdown(f'<a href="https://bibliotheque.upl-univ.ac/" target="_blank" class="biblio-link">📚 Bibliothèque UPL</a>', unsafe_allow_html=True)
    
    st.divider()
    st.title("⚙️ Paramètres")
    mode = st.selectbox("Mode", ["Étudiant", "Enseignant"])
    st.session_state.mode = mode

# -----------------------
# LOGIQUE ACADÉMIQUE
# -----------------------
def is_academic(question):
    interdits = ["football","match","musique","chanson","film","serie","amour","copine","copain","jeu","divertissement"]
    return not any(mot in question.lower() for mot in interdits)

def get_system_prompt(mode):
    prompt = f"Tu es un assistant académique. Mode : {mode}."
    return prompt + " Réponds de manière claire et strictement éducative."

def text_to_speech(text):
    tts = gTTS(text=text, lang='fr')
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp.name)
    return temp.name

# -----------------------
# INTERFACE DE CHAT
# -----------------------
st.markdown("# 🎓 Assistant Académique IA")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# Entrée Audio
audio = st.audio_input("🎤 Parlez")
if audio:
    try:
        transcription = client.audio.transcriptions.create(file=("audio.wav", audio.getvalue()), model="whisper-large-v3")
        prompt = transcription.text.strip()
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
    except: st.warning("Erreur audio")

# Entrée Texte
prompt = st.chat_input("Pose ta question...")
if prompt:
    if not is_academic(prompt):
        st.warning("Sujet non académique détecté.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("assistant"):
            full_response = ""
            placeholder = st.empty()
            messages_api = [{"role": "system", "content": get_system_prompt(st.session_state.mode)}]
            for m in st.session_state.messages[-10:]: messages_api.append(m)
            
            stream = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages_api, stream=True)
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
            
            audio_res = text_to_speech(full_response)
            st.audio(audio_res, format="audio/mp3")
            st.session_state.messages.append({"role": "assistant", "content": full_response})

st.markdown("---")
st.markdown("<center>Développé par <b>Julien Banze Kandolo</b> 🚀</center>", unsafe_allow_html=True)
