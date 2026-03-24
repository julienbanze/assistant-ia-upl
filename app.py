import streamlit as st
from groq import Groq
from gtts import gTTS
import tempfile

# -----------------------
# CONFIG PAGE
# -----------------------
st.set_page_config(
    page_title="Assistant Académique IA",
    page_icon="logo.jpg",  # 👈 JPG ici
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
}

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
# GROQ
# -----------------------
@st.cache_resource
def init_client():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])

client = init_client()

if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------
# SIDEBAR
# -----------------------
with st.sidebar:
    st.image("logo.jpg", width=120)  # 👈 JPG
    st.title("⚙️ Paramètres")
    mode = st.selectbox("Niveau", ["Étudiant", "Enseignant"])
    st.session_state.mode = mode

# -----------------------
# HEADER
# -----------------------
col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.image("logo.jpg", width=140)  # 👈 JPG

st.markdown("# 🎓 Assistant Académique IA")

# -----------------------
# BIBLIOTHÈQUE
# -----------------------
st.markdown("""
<div class="biblio-box">
    💡 Consultez les ressources de l'UPL :
    <br><br>
    <a class="biblio-link" href="https://bibliotheque.upl-univ.ac/" target="_blank">
        📚 Bibliothèque UPL
    </a>
</div>
""", unsafe_allow_html=True)

# -----------------------
# CHAT
# -----------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Posez votre question académique...")
if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        response = "Réponse générée..."  # simplifié ici
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

# -----------------------
# FOOTER
# -----------------------
st.markdown("---")
st.markdown(
    "<p style='text-align: center;'>UPL | Développé par Julien Banze 🚀</p>",
    unsafe_allow_html=True
)
