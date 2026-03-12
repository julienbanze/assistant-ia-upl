import streamlit as st
from groq import Groq
import logging
from pathlib import Path
import PyPDF2

# -----------------------------
# CONFIGURATION DE LA PAGE
# -----------------------------
st.set_page_config(
    page_title="Assistant Académique IA",
    page_icon="🎓",
    layout="wide"
)

# -----------------------------
# DESIGN PROFESSIONNEL
# -----------------------------
st.markdown("""
<style>
.stApp{
background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
color:white;
}
h1{
color:#FFD700;
text-align:center;
}
.stChatInput input{
border-radius:25px;
border:2px solid gold;
padding:12px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# LOGS
# -----------------------------
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

# -----------------------------
# INIT CLIENT GROQ
# -----------------------------
@st.cache_resource
def init_client():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])
client = init_client()

# -----------------------------
# PROMPT SYSTÈME
# -----------------------------
SYSTEM_PROMPT = """
Tu es un assistant académique expert.
Tu aides les étudiants dans :
informatique, mathématiques, électronique, intelligence artificielle, programmation.
Réponds toujours en français.

Règles :
1. Refuse poliment les questions impolies ou insultantes.
2. Si on mentionne "Julien Banze Kandolo" ou variantes, affiche un message respectueux pour le créateur.
3. Reconnais et explique les abréviations (ex: UPL = Université Protestante de Lubumbashi).
4. Tu peux répéter la question dans une autre langue mais réponds toujours en français.
5. Structure les réponses : Titre, Explication, Exemple, Conclusion.
"""

# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:
    st.title("🎓 Assistant IA")
    st.markdown("Développé par **Julien Banze Kandolo**")
    st.divider()
    if st.button("Nouvelle conversation"):
        st.session_state.messages=[]
        st.rerun()
    uploaded_pdf = st.file_uploader("📄 Charger un PDF de cours", type="pdf")

# -----------------------------
# EXTRACTION PDF
# -----------------------------
pdf_text=""
if uploaded_pdf:
    reader = PyPDF2.PdfReader(uploaded_pdf)
    for page in reader.pages:
        pdf_text += page.extract_text()
    st.success("PDF chargé avec succès")

# -----------------------------
# MÉMOIRE CHAT
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages=[]

# -----------------------------
# TITRE
# -----------------------------
st.title("🎓 Assistant Académique IA")
st.write("Tapez votre question ou utilisez le micro. L’IA répond en texte et en voix.")

# -----------------------------
# HISTORIQUE CHAT
# -----------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------------
# ZONE TEXTE + AUDIO (comme ChatGPT)
# -----------------------------
col_text, col_audio = st.columns([3,1])

# --- Texte
with col_text:
    prompt = st.chat_input("Posez votre question")

# --- Audio
with col_audio:
    audio_input = st.audio_input("🎤")

# -----------------------------
# TRAITEMENT AUDIO
# -----------------------------
if audio_input is not None:
    transcription = client.audio.transcriptions.create(
        file=("audio.wav", audio_input.getvalue()),
        model="whisper-large-v3"
    )
    question = transcription.text
    st.chat_message("user").markdown(question)
    st.session_state.messages.append({"role":"user","content":question})

# -----------------------------
# TRAITEMENT TEXTE
# -----------------------------
if prompt:
    st.session_state.messages.append({"role":"user","content":prompt})
    st.chat_message("user").markdown(prompt)

# -----------------------------
# GENERATION IA (texte + voix)
# -----------------------------
if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"]=="user":
    with st.chat_message("assistant"):
        messages=[{"role":"system","content":SYSTEM_PROMPT}]
        if pdf_text!="":
            messages.append({"role":"system","content":"Cours fourni par l'utilisateur :"+pdf_text[:4000]})
        for m in st.session_state.messages:
            messages.append(m)

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.2,
            max_tokens=1200
        )
        response = completion.choices[0].message.content

        # Affichage texte
        st.markdown(response)

        # Voix automatique
        st.markdown(f"""
        <script>
        var speech = new SpeechSynthesisUtterance(`{response}`);
        speech.lang="fr-FR";
        window.speechSynthesis.speak(speech);
        </script>
        """, unsafe_allow_html=True)

        st.session_state.messages.append({"role":"assistant","content":response})

# -----------------------------
# FOOTER
# -----------------------------
st.divider()
st.markdown("Assistant académique intelligent développé par **Julien Banze Kandolo**")
