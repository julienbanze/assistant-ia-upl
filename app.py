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
.stApp {
    background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
    color: white;
}

h1 {
    color: #FFD700;
    text-align: center;
    margin-bottom: 5px;
}

/* Style du bloc de la bibliothèque */
.biblio-box {
    text-align: center;
    padding: 15px;
    background-color: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    border: 1px dashed #25D366;
    margin: 0 auto 30px auto;
    max-width: 850px;
}

.biblio-text {
    font-size: 1.1em;
    color: #f0f0f0;
    margin-bottom: 8px;
}

.biblio-link {
    color: #25D366 !important;
    font-weight: bold;
    text-decoration: underline;
    font-size: 1.2em;
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
        st.error("GROQ_API_KEY manquante dans les Secrets.")
        st.stop()

client = init_client()

# -----------------------
# SESSION STATE
# -----------------------
if "messages" not in st.session_state: st.session_state.messages = []
if "mode" not in st.session_state: st.session_state.mode = "Étudiant"
if "has_greeted" not in st.session_state: st.session_state.has_greeted = False

# -----------------------
# SIDEBAR (MENU GEMINI-STYLE)
# -----------------------
with st.sidebar:
    st.title("⚙️ Paramètres")
    st.session_state.mode = st.selectbox("Niveau d'analyse", ["Étudiant", "Enseignant"])
    st.divider()
    st.write("Cet assistant est dédié à votre réussite académique à l'UPL.")

# -----------------------
# HEADER & BIBLIOTHÈQUE
# -----------------------
st.markdown("# 🎓 Assistant Académique IA")

# Message professionnel corrigé et lien
st.markdown("""
<div class="biblio-box">
    <div class="biblio-text">
        💡 Pour développer vos compétences et approfondir vos connaissances, veuillez consulter les ressources de notre institution :
    </div>
    <a class="biblio-link" href="https://bibliotheque.upl-univ.ac/" target="_blank">
        📚 Accéder à la Bibliothèque de l'UPL
    </a>
</div>
""", unsafe_allow_html=True)

# -----------------------
# LOGIQUE DE FILTRAGE
# -----------------------
def is_educational(question):
    # Liste de thèmes strictement non-éducatifs
    mots_bloques = ["football", "mercato", "match", "chanson", "musique", "film", "serie", "amour", "copine", "copain", "buzz", "jeu vidéo"]
    return not any(mot in question.lower() for mot in mots_bloques)

def get_system_prompt(mode):
    base = f"""Tu es l'assistant académique officiel de l'UPL. 
    Ta mission est EXCLUSIVEMENT l'éducation, la formation humaine et la recherche scientifique.
    - Si la question est liée aux sciences, aux lettres, à la technologie ou à la culture générale éducative, réponds avec précision.
    - Si la question concerne le divertissement pur, le sport ou des sujets futiles, refuse poliment en rappelant ta mission éducative.
    - Mode actuel : {mode}."""
    return base

def text_to_speech(text):
    tts = gTTS(text=text, lang='fr')
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp.name)
    return temp.name

# -----------------------
# CHAT INTERFACE
# -----------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

audio = st.audio_input("🎤 Posez votre question oralement")
if audio:
    try:
        transcription = client.audio.transcriptions.create(file=("audio.wav", audio.getvalue()), model="whisper-large-v3")
        prompt = transcription.text.strip()
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
    except: st.warning("Erreur de transcription.")

prompt = st.chat_input("Posez votre question académique ici...")
if prompt:
    if not is_educational(prompt):
        resp = "Désolé, je suis programmé pour répondre uniquement aux questions cadrant avec l'éducation et le développement humain."
        st.chat_message("assistant").markdown(resp)
        st.session_state.messages.append({"role": "assistant", "content": resp})
    else:
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("assistant"):
            full_response = ""
            placeholder = st.empty()
            
            # Préparation des messages pour l'IA
            sys_msg = get_system_prompt(st.session_state.mode)
            if st.session_state.has_greeted: sys_msg += "\nNe salue plus l'utilisateur."
            else: st.session_state.has_greeted = True
            
            messages_api = [{"role": "system", "content": sys_msg}]
            for m in st.session_state.messages[-10:]: messages_api.append(m)
            
            stream = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages_api, stream=True)
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
            
            # Audio
            st.audio(text_to_speech(full_response), format="audio/mp3")
            st.session_state.messages.append({"role": "assistant", "content": full_response})

st.markdown("---")
st.markdown("<p style='text-align: center;'>Propulsé par l'IA pour l'UPL | Développé par <b>Julien Banze Kandolo</b> 🚀</p>", unsafe_allow_html=True)
