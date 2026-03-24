import streamlit as st
from groq import Groq
from gtts import gTTS
import tempfile

# -----------------------
# CONFIG PAGE
# -----------------------
st.set_page_config(
    page_title="Assistant Académique IA",
    page_icon="logo.jpg",
    layout="wide"
)

# -----------------------
# STYLE
# -----------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
    color: white;
}
h1 { color: #FFD700; }

div[data-testid="stChatInput"] > div {
    border: 2px solid #25D366 !important;
    border-radius: 25px !important;
    background-color: #1e2a38 !important;
}
div[data-testid="stChatInput"] textarea {
    border: none !important;
    color: white !important;
}
div[data-testid="stChatInput"] button {
    background-color: #25D366 !important;
    border-radius: 50% !important;
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
        st.error("Clé API manquante")
        st.stop()

client = init_client()

if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------
# SIDEBAR
# -----------------------
with st.sidebar:
    st.image("logo.jpg", width=100)
    st.title("⚙️ Paramètres")
    mode = st.selectbox("Niveau", ["Étudiant", "Enseignant"])
    st.session_state.mode = mode

# -----------------------
# HEADER (LOGO + TEXTE SUR LA MEME LIGNE)
# -----------------------
col1, col2 = st.columns([1,8])

with col1:
    st.image("logo.jpg", width=60)  # 👈 petit logo

with col2:
    st.markdown("<h1>Assistant Académique IA</h1>", unsafe_allow_html=True)

# -----------------------
# FONCTION IA
# -----------------------
def get_system_prompt(mode):
    return f"""Tu es un assistant académique sérieux.
    Tu aides uniquement dans les études.
    Mode : {mode}"""

def text_to_speech(text):
    tts = gTTS(text=text, lang='fr')
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp.name)
    return temp.name

# -----------------------
# CHAT
# -----------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Pose ta question...")
if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

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

            # 🔊 AUDIO
            audio_file = text_to_speech(full_response)
            st.audio(audio_file)

            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"Erreur : {e}")

# -----------------------
# FOOTER
# -----------------------
st.markdown("---")
st.markdown(
    "<p style='text-align:center;'>UPL | Développé par Julien Banze 🚀</p>",
    unsafe_allow_html=True
)
