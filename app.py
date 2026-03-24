import streamlit as st
from groq import Groq
from gtts import gTTS
import tempfile
from pathlib import Path
from streamlit_mic_recorder import mic_recorder

# -----------------------
# CONFIG PAGE
# -----------------------
st.set_page_config(
    page_title="Assistant Académique IA 🎓",
    page_icon="🎓",
    layout="wide"
)

# -----------------------
# STYLE PRO WHATSAPP + BOUTON MICRO MODERNE
# -----------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
    color: white;
}

h1 { color: #FFD700; text-align: center; }

.biblio-box {
    text-align: center;
    padding: 15px;
    background-color: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    border: 1px dashed #25D366;
    margin: 0 auto 30px auto;
    max-width: 850px;
}

.biblio-link {
    color: #25D366 !important;
    font-weight: bold;
    text-decoration: underline;
    font-size: 1.2em;
}

/* CHAT INPUT */
div[data-testid="stChatInput"] { border: none !important; }
div[data-testid="stChatInput"] > div {
    border: 2px solid #25D366 !important;
    border-radius: 25px !important;
    background-color: #1e2a38 !important;
}
div[data-testid="stChatInput"] textarea { 
    box-shadow: none !important; border: none !important; color: white !important; 
}
div[data-testid="stChatInput"] button { 
    background-color: #25D366 !important; border-radius: 50% !important; 
}

/* VOICE BUTTON */
.voice-bar {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: -10px;
}

.mic-button {
    background: linear-gradient(135deg, #00C853, #25D366);
    border-radius: 50%;
    width: 50px;
    height: 50px;
    display: flex;
    justify-content: center;
    align-items: center;
    color: white;
    font-size: 24px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
}

.mic-button:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 12px rgba(0,0,0,0.4);
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
        st.error("GROQ_API_KEY manquante.")
        st.stop()

client = init_client()

if "messages" not in st.session_state: st.session_state.messages = []
if "has_greeted" not in st.session_state: st.session_state.has_greeted = False

# -----------------------
# SIDEBAR
# -----------------------
with st.sidebar:
    st.title("⚙️ Paramètres")
    mode = st.selectbox("Niveau", ["Étudiant", "Enseignant"])
    st.session_state.mode = mode

# -----------------------
# HEADER & BIBLIOTHÈQUE
# -----------------------
st.markdown("# 🎓 Assistant Académique IA")

st.markdown("""
<div class="biblio-box">
    <div style="font-size: 1.1em; color: #f0f0f0; margin-bottom: 8px;">
        💡 Pour développer vos compétences et approfondir vos connaissances, veuillez consulter les ressources de notre institution :
    </div>
    <a class="biblio-link" href="https://bibliotheque.upl-univ.ac/" target="_blank">
        📚 Accéder à la Bibliothèque de l'UPL
    </a>
</div>
""", unsafe_allow_html=True)

# -----------------------
# SYSTEM PROMPT
# -----------------------
def get_system_prompt(mode):
    return f"""Tu es l'Assistant Académique de l'UPL (Université Protestante de Lubumbashi).
    
    CONSIGNE DE SÉCURITÉ ABSOLUE :
    1. Tu ne réponds QU'AUX questions liées à l'éducation, aux sciences, à la technologie, à la littérature, à l'histoire et au développement humain.
    2. Tu as l'INTERDICTION FORMELLE de parler de : célébrités, musique mondaine, sport, relations amoureuses/draguer, divertissement ou buzz.
    3. Si une question est hors-sujet ou non académique, réponds : "Désolé, ma mission est strictement limitée au cadre éducatif et académique de l'UPL."
    
    Mode actuel : {mode}."""

def text_to_speech(text):
    tts = gTTS(text=text, lang='fr')
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp.name)
    return temp.name

# -----------------------
# CHAT EXISTANT
# -----------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# -----------------------
# 🎤 MICRO DANS LA BARRE + VOIX → TEXTE → IA
# -----------------------
st.markdown('<div class="voice-bar">', unsafe_allow_html=True)
col1, col2 = st.columns([8,1])

with col2:
    audio = mic_recorder(
        start_prompt="",
        stop_prompt="",
        just_once=True,
        use_container_width=True
    )
st.markdown('</div>', unsafe_allow_html=True)

if audio:
    with open("voice.wav", "wb") as f:
        f.write(audio["bytes"])
    try:
        transcription = client.audio.transcriptions.create(
            file=open("voice.wav", "rb"),
            model="whisper-large-v3"
        )
        voice_text = transcription.text

        # Répéter la question en français
        st.chat_message("user").markdown(f"Vous avez dit : *{voice_text}*")
        st.session_state.messages.append({"role":"user","content":voice_text})

        # Envoi automatique à l'IA
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""

            sys_msg = get_system_prompt(st.session_state.mode)
            if st.session_state.has_greeted:
                sys_msg += "\nNe fais plus de salutations."
            else:
                st.session_state.has_greeted = True

            messages_api = [{"role": "system", "content": sys_msg}]
            for m in st.session_state.messages[-5:]:
                messages_api.append(m)

            try:
                stream = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages_api,
                    stream=True,
                    temperature=0.1
                )

                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)

                if "Désolé" not in full_response:
                    st.audio(text_to_speech(full_response), format="audio/mp3")

                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                st.error(f"Erreur IA : {e}")

    except Exception as e:
        st.error(f"Erreur audio : {e}")

# -----------------------
# CHAT INPUT NORMAL
# -----------------------
prompt = st.chat_input("Posez votre question académique...")
if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        sys_msg = get_system_prompt(st.session_state.mode)
        if st.session_state.has_greeted: sys_msg += "\nNe fais plus de salutations."
        else: st.session_state.has_greeted = True
        
        messages_api = [{"role": "system", "content": sys_msg}]
        for m in st.session_state.messages[-5:]: messages_api.append(m)
        
        try:
            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile", 
                messages=messages_api, 
                stream=True,
                temperature=0.1
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
            
            if "Désolé" not in full_response:
                st.audio(text_to_speech(full_response), format="audio/mp3")
                
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"Erreur : {e}")

# -----------------------
# FOOTER
# -----------------------
st.markdown("---")
st.markdown("<p style='text-align: center;'>Propulsé par l'IA pour l'UPL | Développé par <b>Julien Banze Kandolo</b> 🚀</p>", unsafe_allow_html=True)
